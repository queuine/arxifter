#!/usr/bin/env python
"""
Management of processing the user questions on biorxiv feeds,
with that being put to an LLM.
"""

import os, time, asyncio, functools

from .setting import (
    SESSION_EXPIRED_KEY,
    MIN_QUERY_LEN,
    MAX_QUERY_LEN,
    DOCUMENTS_SUBDIR,
)
from .utils import get_current_data_dir
from .keys import get_user_api_key
from .loader import presift_docs
from .mocking import get_mocked_answer
from .querier import exec_query
from .answerer import parse_llm_answer
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


async def answer_query_inner(
    conf, get_logger, executor, encoders, query_data, subject_spec
):
    """
    Processes the question on LLM:
    * takes/checks the required parameters,
    * loads the indexed feeds and presifts them according to the query,
    * puts the question, presifted feeds and the respective prompt to LLM,
    * the LLM answer is parsed, forming a response for user.
    The LLM actions can be mocked instead of being put to LLM
    when it is set on in the configuration.
    """
    logger = get_logger(__name__)

    if subject_spec not in conf["feeds"]["subjects"]["catalog"]:
        return {
            "ok": False,
            "message": "unknown subject",
        }
    subject_fs = conf["feeds"]["subjects"]["catalog"][subject_spec]

    got_params = False
    err_message = ""
    try:
        query_text, to_explain, user_id, is_guest = (
            _get_question_parts(conf, query_data)
        )
        got_params = True
        logger.info(" ".join([
            f"query asked by {"guest" if is_guest else "user"}",
            f"to{"" if to_explain else " not"} get explained",
        ]))
        if conf["debugging"]["query_sifting"]:
            logger.debug(
                f"query:\n{query_text}\n"
            )
    except Exception as exc:
        logger.info(f"wrong query params: {str(exc)}")
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
        logger.info(f"cannot continue with the query: {str(exc)}")
        err_message = (
            "session has expired" if is_guest
            else "the provided user is unkown"
        )
        got_api_key = False

    if not got_api_key:
        return {
            "ok": False,
            "message": err_message,
            SESSION_EXPIRED_KEY: is_guest,
        }

    data_dir = None
    try:
        data_dir = get_current_data_dir(conf)
        if data_dir is None:
            raise OSError("no embedded feeds are availabble")
    except Exception as exc:
        logger.error(f"an error occurred: {str(exc)}")
        err_message = "could not do the query"
        data_dir = None
    if data_dir is None:
        return {
            "ok": False,
            "message": err_message,
        }

    similar_articles = None
    time_presifting_span = None
    try:
        time_presifting_start = time.time()
        loop = asyncio.get_event_loop()
        similar_articles = await loop.run_in_executor(
            executor,
            functools.partial(
                presift_docs,
                conf=conf,
                encoders=encoders,
                data_dir=data_dir,
                base_path=os.path.join(data_dir, subject_fs),
                query=query_text,
                get_logger=get_logger,
            )
        )
        time_presifting_span = time.time() - time_presifting_start
        if similar_articles is None:
            raise OSError("could not load the similar articles")
    except Exception as exc:
        logger.error(f"an error occurred: {str(exc)}")
        err_message = "could not do the query"
        similar_articles = None

    if (
        (similar_articles is None) and (not conf["mocking"]["to_mock"])
    ):
        return {
            "ok": False,
            "message": err_message,
        }

    try:
        time_asking_start = time.time()
        if conf["mocking"]["to_mock"]:
            llm_answer = get_mocked_answer(conf, subject_fs, to_explain)
            if conf["mocking"]["mocking_delay"] > 0:
                await asyncio.sleep(conf["mocking"]["mocking_delay"])
        else:
            llm_answer = await exec_query(
                conf,
                similar_articles,
                query_text,
                to_explain,
                api_key,
                get_logger,
            )
        time_asking_span = time.time() - time_asking_start
        got_answer = True
        logger.info(" ".join([
            f"answer in {time_presifting_span:.3f} s (presifting),",
            f"{time_asking_span:.3f} s (llm answering)",
        ]))
        if conf["debugging"]["query_sifting"]:
            logger.debug(llm_answer)
    except Exception as exc:
        logger.error(f"an error occurred: {str(exc)}")
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
        parsed_answer = parse_llm_answer(conf, get_logger, llm_answer)
        has_parsed = True
    except Exception as exc:
        logger.warning(f"could not parse the answer data: {str(exc)}")
        err_message = "could not parse the LLM query answer"
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
        docs_dir = os.path.join(data_dir, subject_fs, DOCUMENTS_SUBDIR)
        article_list = form_response(
            get_logger, parsed_answer, similar_articles, docs_dir
        )
        got_articles = True
    except Exception as exc:
        logger.warning(f"could not read the answer articles: {str(exc)}")
        err_message = "problems with the query answer"
        got_articles = False

    return {
        "ok": got_articles,
        "message": "Success" if got_articles else err_message,
        "answer": article_list if has_parsed else parsed_answer,
    }
