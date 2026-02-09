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
from concurrent.futures import ThreadPoolExecutor as Executor
import logging

from aiohttp import web
from setproctitle import setproctitle

from arxifter.setting import (
    APP_NAME_WEB_IFCE,
    ENV_CONF_PATH,
    JS_FABRIC_PREFIX,
    APP_MAX_CONTENT_LENGTH,
    APP_RESPONSE_TIMEOUT,
    HEXDIGITS,
    HEXDIGITS_REV,
    SESSION_CLUE_LEN_BASE,
    SESSION_EXPIRED_KEY,
)
from arxifter.utils import (
    origin_spec_to_parts,
    mute_hf,
)
from arxifter.config import get_conf
from arxifter.fabric import get_fabric_js
from arxifter.asking import answer_query_inner
from arxifter.guests import (
    ensure_guest_id,
    get_guests_json,
)
from arxifter.encoder import get_encoders

# to not accidentaly download models from HF
mute_hf()

# conf holds the overall configuration of arxifter
conf = get_conf(ENV_CONF_PATH)
if conf is None:
    logging.error("configuration failed")
    sys.exit(1)
presifting_encoders = get_encoders(conf, logging)
if presifting_encoders is None:
    logging.error("no presifting encoder was loaded")
    sys.exit(1)

# preparation for client checking
conf_header_origin = origin_spec_to_parts(conf["server"]["header_origin"])

logging_level = (
    "DEBUG" if conf["debugging"]["query_sifting"] else "INFO"
)
logging.getLogger().setLevel(logging.getLevelName(logging_level))
logging.basicConfig(format='[%(asctime)s] %(levelname)s %(message)s')

# fabric_js holds the part of configuration relevant for UI
fabric_js = get_fabric_js(conf, JS_FABRIC_PREFIX)
# path_prefix is used for setting where the arxifter listens for connections
path_prefix = conf["view"]["path_prefix"]

routes = web.RouteTableDef()


def get_client_ip(headers, remote_addr):
    """
    Tries to get the actual IP address of the user.
    """
    return headers.get(
        "X-Forwarded-For",
        headers.get("X-Real-IP", remote_addr)
    )


def get_logging_with_client_ip(logger, client_ip):
    """
    Adds the provided (user) IP address to the logger methods,
    along with the specified effective location of the logger.
    """
    def get_logger(logger, client_ip, where):
        prefix = f"({client_ip}) in {where}: "
        Logger = namedtuple("Logger", ["debug", "info", "warning", "error"])
        return Logger(
            debug=(lambda msg: logger.debug(prefix + str(msg))),
            info=(lambda msg: logger.info(prefix + str(msg))),
            warning=(lambda msg: logger.warning(prefix + str(msg))),
            error=(lambda msg: logger.error(prefix + str(msg))),
        )
    return lambda where: get_logger(logger, client_ip, where)


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


@routes.get(f"{path_prefix}/")
async def main_page(request):
    """
    The page that is visible to users as the arxifter UI.
    """
    return web.Response(
        text=conf["view"]["main_page"]["rendered"],
        content_type="text/html",
    )


@routes.get(f"{path_prefix}/config/js/fabric.js")
async def config_fabric(request):
    """
    Serves the UI-related configuration.
    """
    return web.Response(
        text=fabric_js,
        content_type="text/javascript",
    )


@routes.post(f"{path_prefix}/session/guests")
async def provide_guests(request):
    """
    Provides guest status for the arxifter users that are not regular users.
    Guest status is only provided when it is enabled in configuration.
    """
    logger = get_logging_with_client_ip(
        app.logger,
        get_client_ip(request.headers, request.remote),
    )("provide_guests")
    logger.info("guests got requested")
    if not check_client_permissible(request.headers):
        logger.info("guests request not permissible")
        return web.json_response({"available": []})

    # to check provided clues first;
    got_clues = False
    clue_str = None
    try:
        key_vis = conf["session"]["clue_vis"]
        key_hid = conf["session"]["clue_hid"]
        key_str = conf["session"]["clue_str"]
        data = await request.json()
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
        return web.json_response({"available": []})

    current_dt = dt.datetime.now(dt.UTC)
    await ensure_guest_id(conf, current_dt)
    guest_list = get_guests_json(conf, current_dt, clue_str)
    logger.info(f"guests provided: {len(guest_list)}")
    response = {
        conf["session"]["provided"]: guest_list,
    }

    return web.json_response(response)


@routes.get(f"{path_prefix}/query/" + "{subject_spec}")
async def answer_query(request):
    """
    Serving for putting users' questions to LLMs
    and putting the LLM answers back to users.
    It is only available for users:
    * either regular users,
    * or guests if it is enabled in configuration.
    """
    subject_spec = request.match_info["subject_spec"]

    get_logger = get_logging_with_client_ip(
        app.logger,
        get_client_ip(request.headers, request.remote),
    )
    logger = get_logger("answer_query")
    logger.info(f"query got asked on {subject_spec}")
    if not check_client_permissible(request.headers):
        logger.info("query request not permissible")
        return web.json_response("{}")

    websocket = web.WebSocketResponse(
        receive_timeout=APP_RESPONSE_TIMEOUT,
        max_msg_size=APP_MAX_CONTENT_LENGTH,
    )
    await websocket.prepare(request)

    try:
        # to make handshake first
        can_follow = True
        data_prev = 0
        data_sent = conf["handshake"]["handshake_start"]
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

        if can_follow:
            query_data = await websocket.receive_json()
            data_asked = str(abs(data_prev - data_sent))
            if data_asked in query_data:
                del query_data[data_asked]
            else:
                can_follow = False

        if not can_follow:
            logger.info("query handshake did not happen")
            await websocket.close()
            return websocket

        res = await answer_query_inner(
            conf,
            get_logger,
            request.app["executor"],
            presifting_encoders,
            query_data,
            subject_spec,
        )
        logger.info(f"state after querying: {res["ok"]}")

        sift_response = {
            conf["answer"]["sys_message"]: res["message"],
            conf["answer"]["llm_response"]: (
                res["answer"] if res["ok"] else [res["message"]]
            ),
        }
        if res.get(SESSION_EXPIRED_KEY, False):
            sift_response[SESSION_EXPIRED_KEY] = True

        await websocket.send_json(sift_response)
        await websocket.close()
        return websocket
    except Exception as exc:
        logger.info(
            "could not do the querying: " + str(exc)
        )
        try:
            await websocket.close()
        except Exception:
            pass

    return websocket


app = web.Application()
app["executor"] = Executor(max_workers=2)
app.add_routes(routes)
if not conf["server"]["behind_proxy"]:
    app.add_routes([
        web.static(
            f"{path_prefix}/static",
            conf["view"]["static_dir"]["path"],
        )
    ])

if __name__ == "__main__":
    setproctitle(APP_NAME_WEB_IFCE)
    log_ip_spec = (
        "{X-Forwarded-For}i" if conf["server"]["behind_proxy"] else "a"
    )
    web.run_app(
        app,
        port=conf["server"]["port"],
        host=conf["server"]["address"],
        access_log_format="(%" + log_ip_spec + ") %r %s",
    )
