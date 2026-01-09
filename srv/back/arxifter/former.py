#!/usr/bin/env python
"""
Making responses to users out of answers from LLM.
"""

import os, json

from .setting import (
    LLM_MATCHES_KEYS,
    FALSE_VALUES_STR,
    LLM_SUGGESTION_KEY,
    ARTICLE_KEY_RANK_VAR,
    VIEW_WARNING_KEY,
    VIEW_WARNING_ANSWER_WRONG,
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
        logger.error(
            f"({__name__}._take_article_data) " + "\n".join([
                "could not read article data",
                article_path,
                str(exc),
            ])
        )
    return article


def _make_regular_response(logger, answer, docs_dir):
    response = []

    for item in _get_item_list(answer):
        art_rank_key = None
        with_parts = False
        if type(item) in [str, int]:
            art_rank = str(item)
        else:
            with_parts = True
            art_rank_key, art_rank = _get_article_rank(item)

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
            [art_rank_key],
        )
        if article is not None:
            response.append(article)

    return response


def _make_suggestion_response(
    logger, suggestion_article, suggestion_key, docs_dir
):
    art_rank_key, art_rank = _get_article_rank(suggestion_article)
    article_path = _get_article_path(art_rank, docs_dir)
    if article_path is None:
        return []

    article = _take_article_data(
        logger,
        article_path,
        suggestion_article,
        [art_rank_key, suggestion_key],
    )
    if article is not None:
        article[LLM_SUGGESTION_KEY] = True

    return article if article is not None else []


def form_response(logger, answer, docs_dir):
    """
    Provides response to user via:
    * taking LLM answer,
    * checking whether LLM found articles matching to user question
      or whether at least an inexact-matching suggestion was provided,
    * reading the saved articles that correspond to ids in LLM answer,
    * merging the the read articles with the LLM answer.
    """
    is_suggestion, suggestion_article, suggestion_key = (
        _get_suggestion_answer(answer)
    )

    if not is_suggestion:
        return _make_regular_response(logger, answer, docs_dir)
    return _make_suggestion_response(
        logger, suggestion_article, suggestion_key, docs_dir
    )
