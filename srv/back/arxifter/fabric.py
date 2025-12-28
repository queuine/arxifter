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


def _get_conf_urls(conf):
    return {
        _camelize("path_prefix"): conf["urls"]["path_prefix"],
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


def _get_conf_popup(conf):
    return {
        _camelize("back_name"): conf["popup"]["back_name"],
        _camelize("back_link"): conf["popup"]["back_link"],
        _camelize("note_text"): conf["popup"]["note_text"]["content"],
    }


def _get_conf_ui(conf):
    return {
        _camelize("retain"): conf["ui"]["retain"],
        _camelize("user_id"): conf["ui"]["user_id"],
        _camelize("to_explain"): conf["ui"]["to_explain"],
        _camelize("subject_name"): conf["ui"]["subject_name"],
    }


def _get_conf_feeds(conf):
    return {
        _camelize("subjects"): list(conf["feeds"]["subjects"]["list"]),
        _camelize("default_subject"): conf["feeds"]["default_subject"],
        _camelize("feed_size"): conf["feeds"]["feed_size"],
    }


def _get_conf_llms(conf):
    return {
        _camelize("query_top_count"): conf["llms"]["query_top_count"],
    }


def _get_conf_users(conf):
    return {
        _camelize("with_guest"): conf["users"]["with_guest"],
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
            ["urls", _get_conf_urls],
            ["session", _get_conf_session],
            ["handshake", _get_conf_handshake],
            ["query", _get_conf_query],
            ["answer", _get_conf_answer],
            ["popup", _get_conf_popup],
            ["ui", _get_conf_ui],
            ["feeds", _get_conf_feeds],
            ["llms", _get_conf_llms],
            ["users", _get_conf_users],
        ]
    ])
