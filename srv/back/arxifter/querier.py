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

import httpx
from openai import AsyncOpenAI

from .setting import (
    ARTICLE_KEY_RANK,
    LLM_NAME_SEP,
    LLM_NAME_THINK,
    LLM_NAME_COT,
    LLM_INFERRING_TITLE_THRESHOLD,
    LLM_INFERRING_TITLE_CUT_LENGTH,
    LLM_INFERRING_ABSTRACT_THRESHOLD,
    LLM_INFERRING_ABSTRACT_CUT_LENGTH,
    LLM_INFERRING_CUT_NOTICE,
    LLM_ASKING_RETRY,
    LLM_ASKING_MAX_CONN,
    LLM_ASKING_MAX_CONN_KA,
    LLM_API_FORM_RESPONSES,
    LLM_API_FORM_CHAT_COMPLETIONS,
)
from .mocking import get_mocked_answer


def _get_querier(conf, api_key, http_client):
    additional_params = {}
    if conf["llms"]["base_url"] != "":
        additional_params["base_url"] = conf["llms"]["base_url"]

    return {
        "client": AsyncOpenAI(
            api_key=api_key,
            http_client=http_client,
            max_retries=LLM_ASKING_RETRY,
            timeout=conf["llms"]["timeout"],
            **additional_params,
        ),
        "model": conf["llms"]["model_name"].split(LLM_NAME_SEP)[0],
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
        conf["prompts"]["query_part"]["content"]
    ).replace(
        "{query_str}",
        json.dumps(query),
    )


def _debug_response(conf, logger, response):
    try:
        logger.debug("\n".join(["response:", str(response)]))
    except Exception:
        pass
    try:
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
            if hasattr(response.choices[0].message, "reasoning"):
                logger.debug("\n".join([
                    "reasoning:",
                    str(response.choices[0].message.reasoning)
                ]))
            if hasattr(response.choices[0].message, "reasoning_content"):
                logger.debug("\n".join([
                    "reasoning content:",
                    str(response.choices[0].message.reasoning_content)
                ]))
    except Exception:
        logger.debug("could not display the LLM reasoning")


async def _exec_query_inner(conf, logger, querier, query_prompt):
    response = None
    prompt_prefix = ""
    prompt_postfix = ""
    additional_req_params = {}

    model_name_parts = (
        conf["llms"]["model_name"].lower().split(LLM_NAME_SEP)[1:]
    )
    force_to_think = LLM_NAME_THINK.lower() in model_name_parts
    force_to_cot = LLM_NAME_COT.lower() in model_name_parts

    if force_to_think:
        prompt_prefix += (
            conf["prompts"]["asking_think"]["content"]
        )
        additional_req_params["extra_body"] = {
            "reasoning": {"enabled": True},
            "chat_template_kwargs": {"enable_thinking": True},
            "skip_special_tokens": False,
        }
    if force_to_cot:
        prompt_postfix += (
            "\n" + conf["prompts"]["asking_cot"]["content"]
        )

    # some models tend to explode for thinking too long;
    # it leads to raising an exception that is caught here;
    try:
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
                input=prompt_prefix + query_prompt + prompt_postfix,
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
                        "content": (
                            prompt_prefix + query_prompt + prompt_postfix
                        ),
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

    if conf["debugging"]["query_sifting"]:
        _debug_response(conf, logger, response)

    answer = None
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

    async with httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=LLM_ASKING_MAX_CONN,
            max_keepalive_connections=LLM_ASKING_MAX_CONN_KA,
        ),
        timeout=conf["llms"]["timeout"],
    ) as http_client:
        querier = _get_querier(conf, api_key, http_client)

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

        return await _exec_query_inner(conf, logger, querier, query_prompt)
