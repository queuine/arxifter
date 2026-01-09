#!/usr/bin/env python
#
# web serving for arxifter actions
#
"""
Web server for questions on biorxiv feeds.
The questions are put to an LLM to get answered.
"""

import sys, string, random
import datetime as dt
from urllib.parse import urlparse
from collections import namedtuple
import logging

from quart import Quart, Response, request, jsonify, websocket

from arxifter.setting import (
    APP_NAME,
    ENV_CONF_PATH,
    JS_FABRIC_PREFIX,
    APP_MAX_CONTENT_LENGTH,
    APP_RESPONSE_TIMEOUT,
    HEXDIGITS,
    HEXDIGITS_REV,
    SESSION_CLUE_LEN_BASE,
)
from arxifter.utils import origin_spec_to_parts
from arxifter.config import get_conf
from arxifter.fabric import get_fabric_js
from arxifter.asking import answer_query_inner
from arxifter.guests import (
    ensure_guest_id,
    get_guests_json,
)

# conf holds the overall configuration of arxifter
conf = get_conf(ENV_CONF_PATH)
if conf is None:
    logging.error("configuration failed")
    sys.exit(1)
# preparation for client checking
conf_header_origin = origin_spec_to_parts(conf["server"]["header_origin"])

logging_level = (
    "DEBUG" if conf["debugging"]["llm_answers"] else "INFO"
)
logging.getLogger().setLevel(logging.getLevelName(logging_level))
logging.config.dictConfig({
    "version": 1,
    "loggers": {
        APP_NAME: {"level": logging_level},
    },
})
logging.basicConfig(format='[%(asctime)s] %(levelname)s %(message)s')

# fabric_js holds the part of configuration relevant for UI
fabric_js = get_fabric_js(conf, JS_FABRIC_PREFIX)
# path_prefix is used for setting where the arxifter listens for connections
path_prefix = conf["server"]["path_prefix"]
# handshake_start is an auxiliary variable used during an inital handshake
# between a user and the arxifter server the user's question is put to LLM
handshake_start = 2
for idx in range(conf["handshake"]["first_bits"] - 1):
    handshake_start <<= 2
    handshake_start += 2

app = Quart(
    __name__,
    static_folder=conf["view"]["static_dir"]["path"],
    static_url_path=f"{path_prefix}/static"
)
app.name = APP_NAME
app.config["MAX_CONTENT_LENGTH"] = APP_MAX_CONTENT_LENGTH
app.config["RESPONSE_TIMEOUT"] = APP_RESPONSE_TIMEOUT


def get_client_ip(headers, remote_addr):
    """
    Tries to get the actual IP address of the user.
    """
    return headers.get(
        "X-Forwarded-For",
        headers.get("X-Real-IP", remote_addr)
    )


def get_logger_with_client_ip(logger, where, client_ip):
    """
    Adds the provided (user) IP address to the logger methods,
    along with the specified effective location of the logger.
    """
    prefix = f"({client_ip}) in {where}: "
    Logger = namedtuple("Logger", ["debug", "info", "warning", "error"])
    return Logger(
        debug=(lambda msg: logger.debug(prefix + str(msg))),
        info=(lambda msg: logger.info(prefix + str(msg))),
        warning=(lambda msg: logger.warning(prefix + str(msg))),
        error=(lambda msg: logger.error(prefix + str(msg))),
    )


def check_client_permissible(headers):
    """
    Checks whether user request originated on the same server.
    """
    if conf_header_origin is None:
        return True
    client_origin = headers.get("Origin", "")
    if client_origin == "":
        return False

    try:
        client_origin_parts = urlparse(client_origin)
        if conf_header_origin["scheme"] != client_origin_parts.scheme:
            return False
        if conf_header_origin["hostname"] != client_origin_parts.hostname:
            return False
        client_origin_port = (
            client_origin_parts.port if client_origin_parts.port is not None
            else (80 if (client_origin_parts.scheme == "http") else 443)
        )
        if conf_header_origin["port"] != client_origin_port:
            return False
    except Exception:
        return False

    return True


@app.route(f"{path_prefix}/", methods=["GET"])
async def main_page():
    """
    The page that is visible to users as the arxifter UI.
    """
    return Response(
        conf["view"]["main_page"]["rendered"],
        mimetype="text/html"
    )


@app.route(f"{path_prefix}/config/js/fabric.js", methods=["GET"])
async def config_fabric():
    """
    Serves the UI-related configuration.
    """
    return Response(
        fabric_js,
        mimetype="text/javascript"
    )


@app.route(f"{path_prefix}/session/guests", methods=["POST"])
async def provide_guests():
    """
    Provides guest status for the arxifter users that are not regular users.
    Guest status is only provided when it is enabled in configuration.
    """
    logger = get_logger_with_client_ip(
        app.logger,
        "provide_guests",
        get_client_ip(request.headers, request.remote_addr),
    )
    logger.info("guests got requested")
    if not check_client_permissible(request.headers):
        logger.info("guests request not permissible")
        return "", 403

    # to check provided clues first;
    got_clues = False
    clue_str = None
    try:
        key_vis = conf["session"]["clue_vis"]
        key_hid = conf["session"]["clue_hid"]
        key_str = conf["session"]["clue_str"]
        data = await request.get_json()
        clue_str = data[key_str]
        if (
            (data[key_vis] is True)
            and (data[key_hid] is False)
            and (type(clue_str) is str)
            and (len(clue_str) == conf["session"]["clue_len"])
            and all(c in string.hexdigits for c in clue_str)
        ):
            clue_str = clue_str.lower()
            first_part = None
            for ind in range(0, len(clue_str), SESSION_CLUE_LEN_BASE):
                if ind == 0:
                    one_part = clue_str[:SESSION_CLUE_LEN_BASE]
                    one_part_sorted = "".join(sorted(list(one_part)))
                    if (
                        (one_part == HEXDIGITS)
                        or (one_part == HEXDIGITS_REV)
                        or (one_part_sorted != HEXDIGITS)
                    ):
                        break
                    first_part = one_part
                else:
                    one_part = clue_str[
                        (ind*SESSION_CLUE_LEN_BASE):
                        ((ind+1)*SESSION_CLUE_LEN_BASE)
                    ]
                    if one_part != first_part:
                        first_part = None
                        break
            if first_part is not None:
                got_clues = True
    except Exception:
        got_clues = False

    if (not conf["users"]["with_guest"]) or (not got_clues):
        logger.info("no guests got provided")
        return jsonify(
            available=[],
        )

    current_dt = dt.datetime.now(dt.UTC)
    await ensure_guest_id(conf, current_dt)
    guest_list = get_guests_json(conf, current_dt, clue_str)
    logger.info(f"guests provided: {len(guest_list)}")
    response = {
        conf["session"]["provided"]: guest_list,
    }

    return jsonify(
        **response,
    )


@app.websocket(f"{path_prefix}/query/<subject_spec>")
async def answer_query(subject_spec):
    """
    Serving for putting users' questions to LLMs
    and putting the LLM answers back to users.
    It is only available for users:
    * either regular users,
    * or guests if it is enabled in configuration.
    """
    logger = get_logger_with_client_ip(
        app.logger,
        "answer_query",
        get_client_ip(websocket.headers, websocket.remote_addr),
    )
    logger_inner = get_logger_with_client_ip(
        app.logger,
        "answer_query_inner",
        get_client_ip(websocket.headers, websocket.remote_addr),
    )
    logger.info(f"query got asked on {subject_spec}")
    if not check_client_permissible(websocket.headers):
        logger.info("query request not permissible")
        await websocket.close(403)
        return

    try:
        # to make handshake first
        can_follow = True
        data_prev = 0
        data_sent = handshake_start
        for _ in range(conf["handshake"]["count"]):
            data_recv = await websocket.receive_json()
            if type(data_recv) is not int:
                can_follow = False
                break
            if data_recv != abs(data_prev - data_sent):
                can_follow = False
                break
            data_prev = data_recv
            data_sent = random.randint(0, 1_000_000)
            await websocket.send_json(data_sent)

        if not can_follow:
            logger.info("query handshake did not happen")
            await websocket.close(401)
            return

        query_data = await websocket.receive_json()
        res = await answer_query_inner(
            conf,
            logger_inner,
            app.sync_to_async,
            query_data,
            subject_spec
        )
        logger.info(f"state after querying: {res["ok"]}")

        sift_response = {
            conf["answer"]["sys_message"]: res["message"],
            conf["answer"]["llm_response"]: (
                res["answer"] if res["ok"] else [res["message"]]
            ),
        }

        await websocket.send_json(
            **sift_response,
        )
        await websocket.close(200)
        return
    except Exception as exc:
        logger.info(
            "could not do the querying: " + str(exc)
        )
        try:
            await websocket.close(500)
        except Exception:
            pass


if __name__ == "__main__":
    app.run()
