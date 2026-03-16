#!/usr/bin/env python
"""
The querying of LLMs.

Some inference models have issues with returning the artnum correctly, thus:
* first, simplifying it to them by making the artnums equals to sequence ranks
  within the provided presifted set (that has to get remapped eventually),
* second, asking them to provide starts of article titles too,
  so that it is possible to check whether they provided the artnums correctly;
  (only starts of titles are asked for to not slow it too much).
"""
import json, traceback

from openai import AsyncOpenAI

from .setting import (
    ARTICLE_KEY_RANK,
    LLM_INFERRING_TITLE_THRESHOLD,
    LLM_INFERRING_TITLE_CUT_LENGTH,
    LLM_INFERRING_ABSTRACT_THRESHOLD,
    LLM_INFERRING_ABSTRACT_CUT_LENGTH,
    LLM_INFERRING_CUT_NOTICE,
)


def _get_querier(conf, api_key):
    additional_params = {}
    if conf["llms"]["base_url"] != "":
        additional_params["base_url"] = conf["llms"]["base_url"]

    return {
        "client": AsyncOpenAI(
            api_key=api_key,
            **additional_params,
        ),
        "model": conf["llms"]["model_name"],
    }


def _get_content_text(doc_content, doc_part_key):
    limits = {
        "title": (
            LLM_INFERRING_TITLE_THRESHOLD,
            LLM_INFERRING_TITLE_CUT_LENGTH,
        ),
        "abstract": (
            LLM_INFERRING_ABSTRACT_THRESHOLD,
            LLM_INFERRING_ABSTRACT_CUT_LENGTH,
        ),
    }

    if len(doc_content[doc_part_key]) <= limits[doc_part_key][0]:
        return doc_content[doc_part_key]

    return (" ".join([
        doc_content[doc_part_key][:limits[doc_part_key][1]],
        LLM_INFERRING_CUT_NOTICE,
    ]))


def _get_system_text(conf, similar_articles):
    return (
        conf["prompts"]["explained"]["content"]
    ).replace(
        "{context_str}",
        "\n".join([
            json.dumps({
                # artnum values are intentionally of this form;
                ARTICLE_KEY_RANK: str(idx + 1),
                "title": _get_content_text(doc["content"], "title"),
                "abstract": _get_content_text(doc["content"], "abstract"),
            })
            for idx, doc in enumerate(similar_articles)
        ]),
    )


def _get_user_text(conf, query):
    return (
        conf["prompts"]["common_end"]["content"]
    ).replace(
        "{query_str}",
        query,
    )


async def exec_query(
    conf, similar_articles, query, api_key, get_logger
):
    """
    Queries an LLM and returns its answer.
    It requires to have all the query components already prepared;
    those components are:
    * presifted feed (as the articles that possibly correspond to the query),
    * user question on the feeds (as a parameter),
    * prompt to the LLM: prompts are within the loaded configuration,
    * API key.
    """
    logger = get_logger(__name__)
    querier = _get_querier(conf, api_key)

    response = None
    try:
        # some models tend to explode for thinking too much;
        # it leads to raising an exception that is caught here;
        response = await querier["client"].responses.create(
            model=querier["model"],
            # all the info for the inferrer is put into "input",
            # b/c splitting it to "instructions" vs. "input"
            # leaves some inferrers ignoring the "instructions";
            input="\n".join([
                _get_system_text(conf, similar_articles),
                _get_user_text(conf, query),
            ]),
            store=False,
        )
    except Exception as exc:
        logger.warning("\n".join([
            "an error during waiting for LLM answer",
            str(exc),
        ]))
        if conf["debugging"]["query_sifting"]:
            logger.debug(traceback.format_exc())

    if response is None:
        return None

    answer = None
    try:
        answer = str(response.output_text)
    except Exception as exc:
        logger.warning("\n".join([
            "cannot take the output part from the LLM answer",
            str(exc),
        ]))
    return answer
