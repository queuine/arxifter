#!/usr/bin/env python
"""
Management of processing the user questions on biorxiv feeds,
with that being put to an LLM.
"""

import os, json, time, asyncio

from .setting import (
    MIN_QUERY_LEN,
    MAX_QUERY_LEN,
    VECTORS_SUBDIR,
    DOCUMENTS_SUBDIR,
)
from .utils import get_current_data_dir
from .keys import get_user_api_key
from .loader import load_index
from .mocking import get_mocked_answer
from .querier import exec_query
from .former import form_response


def _get_question_parts(conf, query_data):
    query_text = None
    to_explain = None
    user_id = None
    is_guest = None

    query_text_key = conf["query"]["query_text"]
    to_explain_key = conf["query"]["to_explain"]
    user_id_key = conf["query"]["user_id"]
    is_guest_key = conf["query"]["is_guest"]

    query_text = str(query_data[query_text_key]).strip()
    to_explain = query_data[to_explain_key]
    if type(to_explain) is not bool:
        raise OSError("the explaining flag has to be boolean")
    user_id = str(query_data[user_id_key]).strip()
    is_guest = query_data[is_guest_key]
    if type(is_guest) is not bool:
        raise OSError("the guest flag has to be boolean")

    return [
        "\n".join([
            " ".join(line.split()) for line in query_text.splitlines()
            if line.strip() != ""
        ])[:MAX_QUERY_LEN],
        to_explain,
        user_id,
        is_guest,
    ]


async def answer_query_inner(conf, app, run_sync, query_data, subject):
    """
    Processes the question on LLM:
    * takes/checks the required parameters,
    * loads the indexed feeds,
    * puts the question with the feeds and the respective prompt to LLM,
    * the LLM answer is parsed, forming a response for user.
    The LLM actions can be mocked instead of being put to LLM
    when it is set on in the configuration.
    """
    if subject not in conf["feeds"]["subjects"]["list"]:
        return {
            "ok": False,
            "message": "unknown subject",
        }

    got_params = False
    err_message = ""
    try:
        query_text, to_explain, user_id, is_guest = (
            _get_question_parts(conf, query_data)
        )
        got_params = True
        app.logger.info(" ".join([
            f"query asked by {"guest" if is_guest else "user"}",
            f"to{"" if to_explain else " not"} get explained",
        ]))
        app.logger.debug(
            f"query:\n{query_text}\n"
        )
    except Exception as exc:
        app.logger.info(f"wrong query params: {str(exc)}")
        err_message = "could not do the query"
        got_params = False

    if got_params and (len(query_text) < MIN_QUERY_LEN):
        err_message = "".join([
            "too short query text ",
            f"(minimal query length is {MIN_QUERY_LEN} letters)",
        ])
        got_params = False

    if not got_params:
        return {
            "ok": False,
            "message": err_message,
        }

    llm_answer = None
    got_answer = False

    api_key = None
    got_api_key = False
    try:
        api_key = get_user_api_key(conf, user_id, is_guest)
        if api_key is None:
            raise OSError("no user found with the provided identifier")
        got_api_key = True
    except Exception as exc:
        app.logger.info(f"an error occurred: {str(exc)}")
        err_message = "the provided user is unkown"
        got_api_key = False

    if not got_api_key:
        return {
            "ok": False,
            "message": err_message,
        }

    data_dir = None
    try:
        data_dir = get_current_data_dir(conf)
        if data_dir is None:
            raise OSError("no embedded feeds are availabble")
    except Exception as exc:
        app.logger.warning(f"an error occurred: {str(exc)}")
        err_message = "could not do the query"
        data_dir = None
    if data_dir is None:
        return {
            "ok": False,
            "message": err_message,
        }

    llm_index = None
    time_loading_span = None
    try:
        time_loading_start = time.time()
        embed_dir = os.path.join(data_dir, subject, VECTORS_SUBDIR)
        llm_index = await run_sync(load_index)(
            conf, data_dir, embed_dir, api_key
        )
        time_loading_end = time.time()
        time_loading_span = time_loading_end - time_loading_start
        if llm_index is None:
            raise OSError("could not load the embedded feeds")
    except Exception as exc:
        app.logger.warning(f"an error occurred: {str(exc)}")
        err_message = "could not do the query"
        llm_index = None

    if (
        (llm_index is None) and (not conf["mocking"]["to_mock"])
    ):
        return {
            "ok": False,
            "message": err_message,
        }

    try:
        time_asking_start = time.time()
        if conf["mocking"]["to_mock"]:
            llm_answer = get_mocked_answer(conf, subject, to_explain)
            if conf["mocking"]["mocking_delay"] > 0:
                await asyncio.sleep(conf["mocking"]["mocking_delay"])
        else:
            llm_answer = await exec_query(
                conf, llm_index, query_text, to_explain, api_key)
        time_asking_end = time.time()
        time_asking_span = time_asking_end - time_asking_start
        got_answer = True
        app.logger.debug(" ".join([
            f"answer in {time_loading_span} s (index loading),",
            f"{time_asking_span} s (llm answering):",
        ]))
        app.logger.debug(llm_answer)
    except Exception as exc:
        app.logger.warning(f"an error occurred: {str(exc)}")
        err_message = "could not do the query"
        got_answer = False

    if not got_answer:
        return {
            "ok": False,
            "message": err_message,
        }

    parsed_answer = None
    has_parsed = False
    try:
        parsed_answer = json.loads(str(llm_answer))
        has_parsed = True
    except Exception as exc:
        app.logger.warning(f"could not parse the answer data: {str(exc)}")
        err_message = "problems with the query answer"
        has_parsed = False

    if not has_parsed:
        return {
            "ok": False,
            "message": err_message,
            "answer": llm_answer,
        }

    got_articles = False
    article_list = []
    try:
        docs_dir = os.path.join(data_dir, subject, DOCUMENTS_SUBDIR)
        article_list = form_response(app, parsed_answer, docs_dir)
        got_articles = True
    except Exception as exc:
        app.logger.warning(f"could not read the answer articles: {str(exc)}")
        err_message = "problems with the query answer"
        got_articles = False

    return {
        "ok": got_articles,
        "message": "Success" if got_articles else err_message,
        "answer": article_list if has_parsed else parsed_answer,
    }
