#!/usr/bin/env python
"""
Providing the UI-related part of the overall configuration.
"""

import json

from .setting import INDENT_SIZE


def _camelize(name):
    return "".join([
        (part.capitalize() if idx > 0 else part)
        for idx, part in enumerate(name.split("_"))
    ])


def _get_conf_view(conf):
    return {
        _camelize("path_prefix"): conf["view"]["path_prefix"],
    }


def _get_conf_backlink(conf):
    return {
        _camelize("name"): conf["backlink"]["name"],
        _camelize("link"): conf["backlink"]["link"],
        _camelize("title"): conf["backlink"]["title"],
    }


def _get_conf_notices(conf):
    return {
        _camelize("note_users"): conf["notices"]["note_users"]["content"],
        _camelize("note_users_html"): conf["notices"]["note_users_html"],
    }


def _get_conf_ui(conf):
    return {
        _camelize("user_id"): conf["ui"]["user_id"],
        _camelize("retain_user"): conf["ui"]["retain_user"],
        _camelize("storage_prefix"): conf["ui"]["storage_prefix"],
        _camelize("recall_sifts"): conf["ui"]["recall_sifts"],
    }


def _get_conf_feeds(conf):
    return {
        _camelize("subjects"): list(conf["feeds"]["subjects"]["catalog"]),
        _camelize("default_subject"): conf["feeds"]["default_subject"],
        _camelize("feed_size"): conf["feeds"]["feed_size"],
    }


def _get_conf_sifting(conf):
    return {
        _camelize("answer_max_count"): conf["sifting"]["answer_max_count"],
    }


def _get_conf_users(conf):
    return {
        _camelize("with_guest"): conf["users"]["with_guest"],
    }


def _get_conf_session(conf):
    return {
        _camelize("clue_vis"): conf["session"]["clue_vis"],
        _camelize("clue_hid"): conf["session"]["clue_hid"],
        _camelize("clue_str"): conf["session"]["clue_str"],
        _camelize("clue_len"): conf["session"]["clue_len"],
        _camelize("provided"): conf["session"]["provided"],
    }


def _get_conf_handshake(conf):
    return {
        _camelize("count"): conf["handshake"]["count"],
        _camelize("first_bits"): conf["handshake"]["first_bits"],
    }


def _get_conf_query(conf):
    return {
        _camelize("query_text"): conf["query"]["query_text"],
        _camelize("to_explain"): conf["query"]["to_explain"],
        _camelize("user_id"): conf["query"]["user_id"],
        _camelize("is_guest"): conf["query"]["is_guest"],
    }


def _get_conf_answer(conf):
    return {
        _camelize("llm_response"): conf["answer"]["llm_response"],
        _camelize("sys_message"): conf["answer"]["sys_message"],
    }


def _turn_config_to_return(config):
    return ("\n".join([
        ((" " * INDENT_SIZE) + line) for line in (
            "return " + json.dumps(config, indent=4)
        ).split("\n")
    ]))


def get_fabric_js(conf, prefix):
    """
    Provides the UI-related configuration as JS functions.
    """
    return "\n".join([
        "\n".join([
            "function " + _camelize(prefix + part) + "() {",
            _turn_config_to_return(func(conf)),
            "}",
            "",
        ]) for part, func in [
            ["view", _get_conf_view],
            ["backlink", _get_conf_backlink],
            ["notices", _get_conf_notices],
            ["ui", _get_conf_ui],
            ["feeds", _get_conf_feeds],
            ["sifting", _get_conf_sifting],
            ["users", _get_conf_users],
            ["session", _get_conf_session],
            ["handshake", _get_conf_handshake],
            ["query", _get_conf_query],
            ["answer", _get_conf_answer],
        ]
    ])
