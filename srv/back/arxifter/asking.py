#!/usr/bin/env python
"""
Management of processing of user questions on biorxiv feeds,
with local presifting, followed by a use of a remote LLM.
"""

import time

from .setting import (
    SESSION_EXPIRED_KEY,
    MIN_QUERY_LEN,
    MAX_QUERY_LEN,
    PRESIFT_LAST_COUNT,
    PRESIFT_LAST_DAYS,
)
from .utils import (
    subject_spec_to_base_subjects,
    is_access_ok,
)
from .keys import get_user_api_key
from .checker import (
    check_query,
    adjust_query,
)
from .querier import exec_query
from .answerer import parse_llm_answer
from .former import form_response
from .presifter import conduct_presift


def _get_question_parts(conf, query_data):
    query_text = None
    feed_type = None
    user_id = None
    is_guest = None

    query_text_key = conf["query"]["query_text"]
    feed_type_key = conf["query"]["feed_type"]
    user_id_key = conf["query"]["user_id"]
    is_guest_key = conf["query"]["is_guest"]

    query_text = str(query_data[query_text_key]).strip()
    feed_type = query_data[feed_type_key]
    if feed_type not in [PRESIFT_LAST_COUNT, PRESIFT_LAST_DAYS]:
        raise OSError("unknown feed type")
    user_id = str(query_data[user_id_key]).strip()
    is_guest = query_data[is_guest_key]
    if type(is_guest) is not bool:
        raise OSError("the guest flag has to be boolean")

    return [
        "\n".join([
            " ".join(line.split()) for line in query_text.splitlines()
            if line.strip() != ""
        ])[:MAX_QUERY_LEN],
        feed_type,
        user_id,
        is_guest,
    ]


def _get_base_subjects(conf, subject_spec):
    if subject_spec in conf["feeds"]["subjects"]["catalog"]:
        return conf["feeds"]["subjects"]["catalog"][subject_spec]

    if not conf["feeds"]["allow_combinations"]:
        return None

    base_subjects = subject_spec_to_base_subjects(subject_spec)
    for subject in base_subjects:
        if subject not in conf["feeds"]["subjects"]["bare"]:
            return None

    return base_subjects


async def answer_query_inner(
    conf, get_logger, executor, encoders, query_data, subject_spec, client_ip
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

    base_subjects = _get_base_subjects(conf, subject_spec)
    if base_subjects is None:
        return {
            "ok": False,
            "message": "unknown subject",
        }

    got_params = False
    err_message = ""
    try:
        query_text, feed_type, user_id, is_guest = (
            _get_question_parts(conf, query_data)
        )
        got_params = True
        logger.info(" ".join([
            f"query asked by {"guest" if is_guest else "user"}",
            f"on '{feed_type}' feed form",
        ]))
        if conf["debugging"]["query_sifting"]:
            logger.debug(
                f"query:\n{query_text}"
            )

        if is_guest and not conf["users"]["with_guest"]:
            logger.info("attempted guest querying while guests not allowed")
            return {
                "ok": False,
                "message": "guest users are not allowed",
            }

        if not is_access_ok(conf, client_ip, is_guest, logger.warning):
            access_prefix = "guest" if is_guest else "user"
            logger.info(
                f"{access_prefix} IP address is not allowed (query answering)"
            )
            access_error_message = (
                f"{client_ip} not allowed"
                if conf["access"][access_prefix + "_show_blocked_ip"]
                else "not doing the sifting"
            )
            return {
                "ok": False,
                "message": access_error_message,
            }

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

    query_checking = (
        (is_guest and conf["queries"]["check_for_guests"])
        or ((not is_guest) and conf["queries"]["check_for_users"])
    )

    if query_checking:
        check_status, check_message = check_query(query_text)
        if not check_status:
            logger.info(f"disallowed query: {check_message}")
            return {
                "ok": False,
                "message": check_message,
            }
        query_text = adjust_query(query_text)

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
    similar_articles = None
    err_message = None
    try:
        time_presifting_start = time.time()
        presift_res = await conduct_presift(
            conf,
            executor,
            get_logger,
            feed_type,
            encoders,
            base_subjects,
            query_text,
        )
        time_presifting_span = time.time() - time_presifting_start

        if presift_res is not None:
            data_dir = presift_res["data_dir"]
            similar_articles = presift_res["similar_articles"]
    except Exception as exc:
        similar_articles = None
        logger.error("\n".join([
            "could not do the presifting",
            str(exc),
        ]))

    if similar_articles is None:
        return {
            "ok": False,
            "message": "could not sift the query",
        }

    try:
        time_asking_start = time.time()
        llm_answer = await exec_query(
            conf,
            similar_articles,
            query_text,
            api_key,
            get_logger,
            subject_spec,
        )
        if llm_answer is not None:
            got_answer = True
        else:
            err_message = "could not get the answer from LLM"
        time_asking_span = time.time() - time_asking_start
        logger.info(" ".join([
            f"answer in {time_presifting_span:.3f} s (presifting),",
            f"{time_asking_span:.3f} s (llm answering)",
        ]))
        if conf["debugging"]["query_sifting"]:
            logger.debug(llm_answer)
    except Exception as exc:
        logger.error(f"an error occurred: {str(exc)}")
        err_message = "asking LLM the query has failed"
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
        article_list = form_response(
            conf,
            get_logger,
            parsed_answer,
            similar_articles,
            data_dir,
            feed_type,
        )
        got_articles = True
    except Exception as exc:
        logger.warning(f"could not read the answer articles: {str(exc)}")
        err_message = "problems with the LLM answer"
        got_articles = False

    return {
        "ok": got_articles,
        "message": "Success" if got_articles else err_message,
        "answer": article_list if has_parsed else parsed_answer,
    }
