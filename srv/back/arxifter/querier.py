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
import asyncio, json, traceback

from openai import AsyncOpenAI

from .setting import (
    ARTICLE_KEY_RANK,
    LLM_INFERRING_TITLE_THRESHOLD,
    LLM_INFERRING_TITLE_CUT_LENGTH,
    LLM_INFERRING_ABSTRACT_THRESHOLD,
    LLM_INFERRING_ABSTRACT_CUT_LENGTH,
    LLM_INFERRING_CUT_NOTICE,
    LLM_ASKING_TIMEOUT,
    LLM_API_FORM_RESPONSES,
    LLM_API_FORM_CHAT_COMPLETIONS,
)
from .mocking import get_mocked_answer


def _get_querier(conf, api_key):
    additional_params = {}
    if conf["llms"]["base_url"] != "":
        additional_params["base_url"] = conf["llms"]["base_url"]

    return {
        "client": AsyncOpenAI(
            api_key=api_key,
            timeout=LLM_ASKING_TIMEOUT,
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
        conf["prompts"]["main_part"]["content"]
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
    ) + conf["prompts"]["asking_honest"]["content"]


def _get_user_text(conf, query):
    return (
        conf["prompts"]["ending_part"]["content"]
    ).replace(
        "{query_str}",
        json.dumps(query),
    )


async def exec_query(
    conf, similar_articles, query, api_key, get_logger, subject_spec
):
    """
    Queries an LLM and returns its answer.
    It requires to have all the query components already prepared;
    those components are:
    * presifted feed (as the articles that possibly correspond to the query),
    * user question on the feeds (as a parameter),
    * prompt to the LLM: prompts are within the loaded configuration,
    * API key.
    If the system is set to mock the LLM, it returns a mocked LLM answer.
    """
    logger = get_logger(__name__)
    querier = _get_querier(conf, api_key)

    query_prompt = "\n".join([
        _get_system_text(conf, similar_articles),
        _get_user_text(conf, query),
    ])

    if conf["mocking"]["to_mock"]:
        if conf["debugging"]["query_sifting"]:
            logger.debug(query_prompt)
        answer = get_mocked_answer(conf, subject_spec)
        if conf["mocking"]["mocking_delay"] > 0:
            await asyncio.sleep(conf["mocking"]["mocking_delay"])
        return answer

    response = None
    try:
        additional_req_params = {}
        # some models tend to explode for thinking too much;
        # it leads to raising an exception that is caught here;
        if conf["llms"]["asking_form"] == LLM_API_FORM_RESPONSES:
            if conf["llms"]["max_tokens"] != 0:
                additional_req_params["max_output_tokens"] = (
                    conf["llms"]["max_tokens"]
                )

            response = await querier["client"].responses.create(
                model=querier["model"],
                # all the info for the inferrer is put into "input",
                # b/c splitting it to "instructions" vs. "input"
                # leaves some inferrers ignoring the "instructions";
                input=query_prompt,
                store=False,
                **additional_req_params,
            )
        elif conf["llms"]["asking_form"] == LLM_API_FORM_CHAT_COMPLETIONS:
            # some OpenAI-compatible providers still do not support
            # the "responses" API: using the "completions" API for them;
            if conf["llms"]["max_tokens"] != 0:
                additional_req_params["max_completion_tokens"] = (
                    conf["llms"]["max_tokens"]
                )

            response = await querier["client"].chat.completions.create(
                model=querier["model"],
                messages=[
                    {
                        "role": "user",
                        "content": query_prompt,
                    },
                ],
                **additional_req_params,
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
        if conf["debugging"]["query_sifting"]:
            logger.debug("\n".join(["response:", str(response)]))
    except Exception:
        pass
    try:
        if conf["debugging"]["query_sifting"]:
            if conf["llms"]["asking_form"] == LLM_API_FORM_RESPONSES:
                for part in response.output:
                    if part.type == "reasoning":
                        for subpart in [
                            [part.content, "reasoning:"],
                            [part.summary, "reasoning summary:"],
                        ]:
                            if subpart[0] is None:
                                continue
                            logger.debug("\n".join([
                                subpart[1],
                                *[
                                    str(item.text) for item in subpart[0]
                                    if item is not None
                                ],
                            ]))
            elif conf["llms"]["asking_form"] == LLM_API_FORM_CHAT_COMPLETIONS:
                logger.debug("\n".join([
                    "reasoning:",
                    str(response.choices[0].message.reasoning)
                ]))
    except Exception:
        logger.debug("could not display the LLM reasoning")

    try:
        if conf["llms"]["asking_form"] == LLM_API_FORM_RESPONSES:
            answer = str(response.output_text)
        elif conf["llms"]["asking_form"] == LLM_API_FORM_CHAT_COMPLETIONS:
            answer = str(response.choices[0].message.content)
    except Exception as exc:
        logger.warning("\n".join([
            "cannot take the output part from the LLM answer",
            str(exc),
        ]))
    return answer
