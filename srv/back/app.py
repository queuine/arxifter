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

# fabric_js holds the part of configuration relevant for UI
fabric_js = get_fabric_js(conf, JS_FABRIC_PREFIX)
# path_prefix is used for setting where the arxifter listens for connections
path_prefix = conf["urls"]["path_prefix"]
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
    app.logger.info("guests got asked")
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
        app.logger.info("no guests got provided")
        return jsonify(
            available=[],
        )

    current_dt = dt.datetime.now(dt.UTC)
    await ensure_guest_id(conf, current_dt)
    guest_list = get_guests_json(conf, current_dt, clue_str)
    app.logger.info(f"guests provided: {len(guest_list)}")
    response = {
        conf["session"]["provided"]: guest_list,
    }

    return jsonify(
        **response,
    )


@app.websocket(f"{path_prefix}/query/<subject_id>")
async def answer_query(subject_id):
    """
    Serving for putting users' questions to LLMs
    and putting the LLM answers back to users.
    It is only available for users:
    * either regular users,
    * or guests if it is enabled in configuration.
    """
    app.logger.info(f"query got asked on {subject_id}")
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
            app.logger.info("handshake did not happen")
            return

        query_data = await websocket.receive_json()
        res = await answer_query_inner(
            conf,
            app,
            app.sync_to_async,
            query_data,
            subject_id
        )
        app.logger.info(f"state after querying: {res["ok"]}")

        sift_response = {
            conf["answer"]["sys_message"]: res["message"],
            conf["answer"]["llm_response"]: (
                res["answer"] if res["ok"] else [res["message"]]
            ),
        }

        await websocket.send_json(
            **sift_response,
        )

    except Exception as exc:
        app.logger.info("could not do the querying: " + str(exc))


if __name__ == "__main__":
    app.run()
