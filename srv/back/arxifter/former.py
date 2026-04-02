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
    LLM_TITLE_START_KEYS,
    LLM_TITLE_START_REGS,
    ARTICLE_KEY_RANK_VAR,
    VIEW_WARNING_KEY,
    VIEW_WARNING_ANSWER_WRONG,
    ARTICLE_RECOGNIZING_THRESHOLD,
    DOCUMENTS_SUBDIR,
    PRESIFT_LAST_COUNT,
    PRESIFT_LAST_DAYS,
    DOI_PREFIX,
    DOC_DOI_KEY,
    DOC_LINK_KEY,
    DOC_SUBJECT_KEY,
    DOC_BASE_KEYS,
    DOC_LINK_START,
    DOC_VERSION_KEY,
    DOC_TYPE_KEY,
)
from .utils import (
    get_doc_name,
)
from .spans.loader import (
    get_doc_depo_path,
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


def _check_is_title_prefix(key, value):
    for title_test_key in LLM_TITLE_START_KEYS:
        if title_test_key in str(key).lower():
            return [
                key,
                str(value).strip() if value is not None else None,
            ]

    for title_test_reg in LLM_TITLE_START_REGS:
        if title_test_reg.search(str(key).lower()) is not None:
            return [
                key,
                str(value).strip() if value is not None else None,
            ]

    return [None, None]


def _check_rank_within_similar_articles(
    art_rank, similar_articles, article, logger
):
    # checking whether the LLM-reported artnum (counted from 1) is correct;
    # the checking is via comparing the respectively reported title;
    # notice that the output article rank is counted from 0;
    checked_rank = None
    try:
        # turning the from-1 couunting to from-0 couunting;
        # that if the artnum is a positive number at first;
        if (
            str(art_rank).isdigit()
            and str(art_rank).isascii()
            and (int(art_rank) > 0)
            and (int(art_rank) <= len(similar_articles))
        ):
            checked_rank = int(art_rank) - 1
    except Exception:
        checked_rank = None

    # since an LLM can provide the article number incorrectly
    # (weaker inferring models tend to hallucinate it occassionally),
    # a checking/fixing of the back-mapping is done by comparing
    # article titles with the provided (start) of title;
    # it is somewhat involved, but that's it;
    title_key = None
    title_prefix = None
    try:
        if type(article) is dict:
            for key, value in article.items():
                title_key, title_prefix = _check_is_title_prefix(key, value)
                if title_key is not None:
                    break
    except Exception:
        title_prefix = None

    # the checking can be done only when a title is provided by LLM;
    # notice that providing the key of the LLM-provided article title too,
    # b/c it is used to avoid showing it at UI
    # (where the title from the article itself is showed);
    if title_prefix in [None, ""]:
        return [
            checked_rank,
            title_key,
        ]

    try:
        title_len = len(title_prefix)
        # computing similarities between the provided and actual titles
        simils = [
            [
                SequenceMatcher(
                    None,
                    title_prefix,
                    sim_art["content"]["title"][:title_len],
                ).ratio(),
                idx,
            ]
            for idx, sim_art in enumerate(similar_articles)
        ]
        # finding out the closest title (and the respective article rank)
        ranked = sorted(
            simils,
            key=lambda item: item[0],
            reverse=True,
        )
        closest_rank = ranked[0][1]
        # if it agrees with the reported article number
        # (or if the reported number is not a valid number),
        # taking the rank of this best-matching title;
        if checked_rank in [None, closest_rank]:
            return [closest_rank, title_key]

        # if here, then some different (than reported) article
        # has its title more similar to the LLM-provided title
        # than the title of the reported article;
        closest_simil = ranked[0][0]
        try:
            reported_simil = simils[checked_rank][0]
        except Exception:
            reported_simil = 0
        # thus it seems that the reported number has to be changed;
        # but only doing the fixing if the difference is big enough;
        # the similarities of the used SequenceMatcher method
        # are between 1.0 (identical) and 0.0 (completely differing);
        # according to seen values, e.g. 0.1 threshold makes sense here
        # (it pertains to a difference between two similarities);
        if (
            (closest_simil - reported_simil)
            > ARTICLE_RECOGNIZING_THRESHOLD
        ):
            logger.info(
                "inferring LLM has apparently reported an artnum wrong"
            )
            return [closest_rank, title_key]
        # if here, the similarity differences were not that big;
        return [checked_rank, title_key]
    except Exception:
        pass

    # if here, then s/t went wrong during the checking of the title;
    # in such a case returning the reported article number
    # (turned to from-0 counted) as having nothing better here;
    return [checked_rank, title_key]


def _back_remap_article_rank(art_rank, similar_articles, article, logger):
    doc_rank, title_key = _check_rank_within_similar_articles(
        art_rank, similar_articles, article, logger
    )

    taken_doc = None
    try:
        if doc_rank is not None:
            taken_doc = similar_articles[doc_rank]
    except Exception:
        taken_doc = None

    if taken_doc is None:
        return [None, None, title_key]

    return [
        str(taken_doc["name"]).lstrip("0"),
        taken_doc["subject"],
        title_key,
    ]


def _get_article_path(conf, art_rank, art_subject, data_dir, feed_type):
    if art_rank is None:
        return None

    if (
        (type(art_rank) is not str)
        or (len(art_rank) == 0)
        or (not art_rank.isascii())
        or (not art_rank.isdecimal())
    ):
        return None

    art_path = None
    if feed_type == PRESIFT_LAST_DAYS:
        art_path = get_doc_depo_path(conf, art_rank, art_subject, data_dir)
    if feed_type == PRESIFT_LAST_COUNT:
        art_path = os.path.join(
            data_dir, art_subject, DOCUMENTS_SUBDIR, get_doc_name(art_rank)
        )
    if art_path is None:
        return None

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


def _take_article_data(
    logger, article_path, article_subject, addendum, leave_keys
):
    try:
        article = {
            DOC_SUBJECT_KEY: article_subject,
        }
        with open(article_path, encoding="utf8") as fh:
            article_bare = json.load(fh)
            for key in DOC_BASE_KEYS:
                if key in article_bare:
                    article[key] = article_bare[key]
            if (
                (DOC_LINK_KEY not in article_bare)
                and (DOC_DOI_KEY in article_bare)
            ):
                doi_value = article_bare[DOC_DOI_KEY]
                if doi_value.startswith(DOI_PREFIX):
                    doi_value = doi_value[len(DOI_PREFIX):]
                article[DOC_LINK_KEY] = DOC_LINK_START + doi_value

            doc_version = article_bare.get(DOC_VERSION_KEY, None)
            if doc_version is not None:
                article["version"] = doc_version
            doc_type = article_bare.get(DOC_TYPE_KEY, None)
            if doc_type is not None:
                article["type"] = doc_type

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


def _make_regular_response(
    conf, logger, answer, similar_articles, data_dir, feed_type
):
    response = []

    for item in _get_item_list(answer):
        art_rank_key = None
        with_parts = False
        if type(item) in [str, int]:
            art_rank = str(item)
        else:
            with_parts = True
            art_rank_key, art_rank = _get_article_rank(item)

        art_rank, art_subject, title_key = _back_remap_article_rank(
            art_rank, similar_articles, item, logger
        )
        article_path = _get_article_path(
            conf, art_rank, art_subject, data_dir, feed_type
        )
        if article_path is None:
            response.append({
                VIEW_WARNING_KEY: VIEW_WARNING_ANSWER_WRONG,
            })
            continue

        article = _take_article_data(
            logger,
            article_path,
            art_subject,
            item if with_parts else None,
            [art_rank_key, title_key],
        )
        if article is not None:
            response.append(article)

    return response


def _make_suggestion_response(
    conf,
    logger,
    suggestion_article,
    similar_articles,
    suggestion_key,
    data_dir,
    feed_type,
):
    art_rank_key, art_rank = _get_article_rank(suggestion_article)
    art_rank, art_subject, title_key = _back_remap_article_rank(
        art_rank, similar_articles, suggestion_article, logger
    )
    article_path = _get_article_path(
        conf, art_rank, art_subject, data_dir, feed_type
    )
    if article_path is None:
        return []

    article = _take_article_data(
        logger,
        article_path,
        art_subject,
        suggestion_article,
        [art_rank_key, suggestion_key, title_key],
    )
    if article is not None:
        article[LLM_SUGGESTION_KEY] = True

    return article if article is not None else []


def form_response(
    conf, get_logger, answer, similar_articles, data_dir, feed_type
):
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
            conf,
            logger,
            answer,
            similar_articles,
            data_dir,
            feed_type,
        )
    return _make_suggestion_response(
        conf,
        logger,
        suggestion_article,
        similar_articles,
        suggestion_key,
        data_dir,
        feed_type,
    )
