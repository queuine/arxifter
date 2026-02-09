#!/usr/bin/env python
"""
Making responses to users out of answers from LLM.

Since some inferring models need the "artnum" numbering as simple as possible,
they get it simplified by having it set to sequence rank (counted from 1)
of the presifted set instead of sequence rank within the overall feed batch.
It has to be eventually remmaped back when handling the LLM answers,
and it is done within the "_back_remap_article_rank" function here.
To make it yet more certain that answered articles are correctly recognized,
matching between article titles and LLM-provided starts of titles is done too.
The result is that the back-mapping of article sequence ranks is safer,
with the process of it being somewhat involved.
"""

import os, json
from difflib import SequenceMatcher

from .setting import (
    LLM_MATCHES_KEYS,
    FALSE_VALUES_STR,
    LLM_SUGGESTION_KEY,
    ARTICLE_KEY_RANK_VAR,
    VIEW_WARNING_KEY,
    VIEW_WARNING_ANSWER_WRONG,
    ARTICLE_RECOGNIZING_THRESHOLD,
)
from .utils import (
    get_doc_name,
)


def _get_suggestion_answer(answer):
    article = None
    if type(answer) in [list, tuple]:
        if (
            (len(answer) == 1)
            and (type(answer[0]) is dict)
        ):
            article = answer[0]
    elif type(answer) is dict:
        article = answer

    if article is None:
        return [False, None, None]

    is_suggestion = False
    suggestion_key = None
    for key, value in article.items():
        for sugg_key in LLM_MATCHES_KEYS:
            if str(key).lower().startswith(sugg_key):
                if (
                    (value is False)
                    or (
                        (type(value) is str)
                        and value.lower() in FALSE_VALUES_STR
                    )
                ):
                    is_suggestion = True
                    suggestion_key = key
                    break
        if is_suggestion is True:
            break

    return [is_suggestion, article, suggestion_key]


def _get_article_rank(article):
    if type(article) is not dict:
        return [None, None]

    for key, value in article.items():
        for key_var in ARTICLE_KEY_RANK_VAR:
            if str(key).lower().startswith(key_var):
                return [key, str(value).strip().lstrip("0")]

    return [None, None]


def _back_remap_article_rank(art_rank, similar_articles, article, logger):
    # getting the actual article name-number from the answered article;
    # both the LLM-provided and back-mapped ranks are counted from 1;
    title_key = None
    remapped_rank = None
    try:
        # direct back-mapping from sequence number within presifted set
        # to sequence number within overall feed batch;
        if (
            str(art_rank).isdigit()
            and str(art_rank).isascii()
            and int(art_rank) > 0
        ):
            remapped_rank = (
                similar_articles[int(art_rank) - 1]["name"].lstrip("0")
            )
    except Exception:
        remapped_rank = None

    # since an LLM can provide the article number incorrectly
    # (weaker inferring models tend to hallucinate it occassionally),
    # a checking/fixing of the back-mapping is done by comparing
    # article titles with provided (start) of title;
    # it is somewhat involved, but that's it;
    try:
        title = None
        if type(article) is dict:
            for key, value in article.items():
                if "title" in str(key).lower():
                    title_key = key
                    title = str(value)
                    break
        if title is not None:
            # the checking can be done only when a title is provided by LLM
            title_len = len(title)
            # computing similarities between the provided and actual titles
            simils = [
                [
                    SequenceMatcher(
                        None, title, sim_art["content"]["title"][:title_len]
                    ).ratio(),
                    sim_art["name"].lstrip("0"),
                ]
                for sim_art in similar_articles
            ]
            # finding out the closest title (and its article)
            ranked = sorted(
                simils,
                key=lambda item: item[0],
                reverse=True,
            )
            closest_rank = ranked[0][1]
            # if it agrees with the directly back-mapped article
            # (or if the diret back-mapping failed), taking it;
            if remapped_rank in [None, closest_rank]:
                return [str(closest_rank), title_key]

            # if here, then some different (than back-mapped) article
            # has its title more similar to the LLM-provided title
            # than the title of the directly back-mapped article;
            # thus it seems that the back-mapping has to be fixed;
            closest_simil = ranked[0][0]
            try:
                remapped_simil = simils[int(art_rank) - 1][0]
            except Exception:
                remapped_simil = 0
            # only doing the fixing if the difference is big enough;
            # the similarities of the used SequenceMatcher method
            # are between 1.0 (identical) and 0.0 (completely differing);
            # according to seen values, e.g. 0.1 threshold makes sense here
            # (it pertains to a difference between two similarities);
            if (
                (closest_simil - remapped_simil)
                > ARTICLE_RECOGNIZING_THRESHOLD
            ):
                logger.info(
                    "inferring LLM has apparently reported an artnum wrong"
                )
                return [str(closest_rank), title_key]
    except Exception:
        pass

    # returning the back-mapped article number;
    # that along with key holding the LLM-provided article title,
    # since it gets used to avoid showing it at UI
    # (where the title from the article itself is showed);
    return [
        str(remapped_rank) if remapped_rank is not None else None,
        title_key,
    ]


def _get_article_path(art_rank, docs_dir):
    if art_rank is None:
        return None

    if (
        (type(art_rank) is not str)
        or (len(art_rank) == 0)
        or (not art_rank.isascii())
        or (not art_rank.isdecimal())
    ):
        return None

    art_path = os.path.join(docs_dir, get_doc_name(art_rank))

    if (
        (not os.path.exists(art_path))
        or (not os.path.isfile(art_path))
    ):
        return None

    return art_path


def _get_item_list(answer):
    if type(answer) in [list, tuple]:
        return list(answer)
    return [answer]


def _take_article_data(logger, article_path, addendum, leave_keys):
    try:
        with open(article_path, encoding="utf8") as fh:
            article = json.load(fh)
        if type(addendum) is dict:
            for key, value in addendum.items():
                if key not in leave_keys:
                    article[key] = value
    except Exception as exc:
        article = None
        logger.error("\n".join([
            "could not read article data:",
            article_path,
            str(exc),
        ]))
    return article


def _make_regular_response(logger, answer, similar_articles, docs_dir):
    response = []

    for item in _get_item_list(answer):
        art_rank_key = None
        with_parts = False
        if type(item) in [str, int]:
            art_rank = str(item)
        else:
            with_parts = True
            art_rank_key, art_rank = _get_article_rank(item)

        art_rank, title_key = _back_remap_article_rank(
            art_rank, similar_articles, item, logger
        )
        article_path = _get_article_path(art_rank, docs_dir)
        if article_path is None:
            response.append({
                VIEW_WARNING_KEY: VIEW_WARNING_ANSWER_WRONG,
            })
            continue

        article = _take_article_data(
            logger,
            article_path,
            item if with_parts else None,
            [art_rank_key, title_key],
        )
        if article is not None:
            response.append(article)

    return response


def _make_suggestion_response(
    logger, suggestion_article, similar_articles, suggestion_key, docs_dir
):
    art_rank_key, art_rank = _get_article_rank(suggestion_article)
    art_rank, title_key = _back_remap_article_rank(
        art_rank, similar_articles, suggestion_article, logger
    )
    article_path = _get_article_path(art_rank, docs_dir)
    if article_path is None:
        return []

    article = _take_article_data(
        logger,
        article_path,
        suggestion_article,
        [art_rank_key, suggestion_key, title_key],
    )
    if article is not None:
        article[LLM_SUGGESTION_KEY] = True

    return article if article is not None else []


def form_response(get_logger, answer, similar_articles, docs_dir):
    """
    Provides response to user via:
    * taking LLM answer,
    * checking whether LLM found articles matching to user question
      or whether at least an inexact-matching suggestion was provided,
    * reading the saved articles that correspond to ids in LLM answer,
    * merging the the read articles with the LLM answer.
    """
    logger = get_logger(__name__)
    is_suggestion, suggestion_article, suggestion_key = (
        _get_suggestion_answer(answer)
    )

    if not is_suggestion:
        return _make_regular_response(
            logger,
            answer,
            similar_articles,
            docs_dir,
        )
    return _make_suggestion_response(
        logger,
        suggestion_article,
        similar_articles,
        suggestion_key,
        docs_dir,
    )
