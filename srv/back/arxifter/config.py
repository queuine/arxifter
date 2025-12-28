#!/usr/bin/env python
"""
Taking, parsing and checking the configuration.
"""

from pathlib import Path
import os, tomllib

from .setting import (
    NEW_DIRS_MODE,
    SESSION_CLUE_LEN_BASE,
    BIORXIV_FEED_SIZE,
)
from .logging import log_error


def _get_conf_path(conf_env_name):
    conf_path = os.environ.get(conf_env_name, None)
    if conf_path is None:
        raise OSError(
            f"environment does not have {conf_env_name} defined.\n"
            "it has to contain path to arxifter configuration file."
        )
    return conf_path


def _read_conf_raw(conf_path):
    try:
        with open(conf_path, "rb") as fh:
            conf_raw = tomllib.load(fh)
    except Exception as exc:
        raise OSError(
            f"cannot get the configuration from {conf_path}.\n"
            + str(exc)
        ) from exc
    return conf_raw


def _check_conf_path_access(conf_part, is_dir=False, writable=False):
    if is_dir and writable:
        os.makedirs(conf_part["path"], mode=NEW_DIRS_MODE, exist_ok=True)

    if is_dir:
        if not os.path.isdir(conf_part["path"]):
            raise OSError(
                f"configuration: {conf_part['value']}/{conf_part['path']} "
                "has to be a directory"
            )
    else:
        if not os.path.isfile(conf_part["path"]):
            raise OSError(
                f"configuration: {conf_part['value']}/{conf_part['path']} "
                "has to be a file"
            )

    if not os.access(conf_part["path"], os.R_OK):
        raise OSError(
            f"configuration: {conf_part['value']}/{conf_part['path']} "
            "has to be readable"
        )

    if not writable:
        return

    if (
        (not os.access(conf_part["path"], os.W_OK))
    ):
        raise OSError(
            f"configuration: {conf_part['value']}/{conf_part['path']} "
            "has to be writable"
        )


def _read_conf_file(conf_part):
    conf_part["content"] = Path(
        conf_part["path"]
    ).read_text(encoding="utf8")


def _read_subject_list(conf_part):
    with open(conf_part["path"], encoding="utf8") as fh:
        subject_list = [
            line.strip() for line in fh if not line.startswith("#")
        ]
    conf_part["list"] = [item for item in subject_list if item != ""]
    if len(conf_part["list"]) == 0:
        raise OSError(
            "configuration: subject list (feeds/subjects) has to have "
            f"at least one item\n{str(conf_part["path"])}"
        )


def _complete_conf(conf):
    if (conf["session"]["clue_len"] % SESSION_CLUE_LEN_BASE) != 0:
        raise OSError(
            "configuration: 'session'/'clue_len' "
            f"has to be mutiple of {SESSION_CLUE_LEN_BASE}"
        )

    _read_conf_file(conf["view"]["main_page"])
    conf["view"]["main_page"]["rendered"] = (
        conf["view"]["main_page"]["content"].replace(
            "{path_prefix}",
            conf["urls"]["path_prefix"],
        )
    )

    _check_conf_path_access(conf["view"]["static_dir"], is_dir=True)

    _read_conf_file(conf["popup"]["note_text"])

    _read_subject_list(conf["feeds"]["subjects"])

    if conf["feeds"]["feed_size"] != BIORXIV_FEED_SIZE:
        raise OSError(
            "configuration: 'feeds'/'feed_size' "
            f"has to be set to {BIORXIV_FEED_SIZE}"
        )

    _check_conf_path_access(
        conf["data"]["storage_dir"],
        is_dir=True,
        writable=True
    )

    conf["prompts"]["plain"]["content"] = _read_prompt_template(
        conf["prompts"]["plain"]["path"]
    )
    conf["prompts"]["explained"]["content"] = _read_prompt_template(
        conf["prompts"]["explained"]["path"]
    )

    _check_conf_path_access(conf["users"]["regular_users"])

    if conf["users"]["with_guest"]:
        _check_conf_path_access(
            conf["users"]["guest_ids"],
            is_dir=True,
            writable=True
        )

    _check_conf_path_access(conf["keys"]["indexer"])

    _check_conf_path_access(conf["keys"]["regular_users"], is_dir=True)

    if conf["users"]["with_guest"]:
        _check_conf_path_access(conf["keys"]["guest_user"])

    if conf["mocking"]["to_mock"]:
        _check_conf_path_access(conf["mocking"]["answers_dir"], is_dir=True)


def _fill_conf(conf, conf_path):
    conf_dir = os.path.dirname(conf_path)
    conf_raw = _read_conf_raw(conf_path)
    try:
        for part, itemlist in [
            ["urls", ["path_prefix"]],
            ["session", ["clue_vis", "clue_hid", "clue_str", "provided"]],
            ["query", ["query_text", "to_explain", "user_id", "is_guest"]],
            ["answer", ["llm_response", "sys_message"]],
            ["popup", ["back_name", "back_link"]],
            ["ui", ["user_id", "to_explain", "subject_name"]],
            ["feeds", ["default_subject"]],
            ["llms", ["embed_model_name", "model_name"]],
        ]:
            for item in itemlist:
                conf[part][item] = str(conf_raw[part][item])

        for part, itemlist in [
            ["view", ["main_page", "static_dir"]],
            ["popup", ["note_text"]],
            ["feeds", ["subjects"]],
            ["data", ["storage_dir"]],
            ["prompts", ["plain", "explained"]],
            ["users", ["regular_users", "guest_ids"]],
            ["keys", ["indexer", "regular_users", "guest_user"]],
            ["mocking", ["answers_dir"]],
        ]:
            for item in itemlist:
                conf[part][item] = {
                    "value": conf_raw[part][item],
                    "path": os.path.normpath(
                        os.path.join(conf_dir, conf_raw[part][item])
                    ),
                }

        for part, itemlist in [
            ["data", ["pruning"]],
            ["users", ["with_guest"]],
            ["mocking", ["to_mock"]],
            ["debugging", ["llm_answers", "feed_taking"]],
        ]:
            for item in itemlist:
                conf[part][item] = conf_raw[part][item]
                if type(conf[part][item]) is not bool:
                    raise OSError(
                        f"configuration: {part}/{item} has to be a boolean"
                    )

        for part, itemlist in [
            ["ui", ["retain"]],
            ["mocking", ["mocking_delay"]],
        ]:
            for item in itemlist:
                conf[part][item] = conf_raw[part][item]
                if (
                    (type(conf[part][item]) is not int)
                    or (conf[part][item] < 0)
                ):
                    raise OSError(
                        f"configuration: {part}/{item} has to be "
                        "a non-negative integer"
                    )

        for part, itemlist in [
            ["session", ["clue_len"]],
            ["handshake", ["count", "first_bits"]],
            ["feeds", ["feed_size"]],
            ["data", ["kept_days"]],
            ["llms", ["embed_batch_size", "query_top_count"]],
            ["users", ["guest_span"]],
        ]:
            for item in itemlist:
                conf[part][item] = conf_raw[part][item]
                if (
                    (type(conf[part][item]) is not int)
                    or (conf[part][item] <= 0)
                ):
                    raise OSError(
                        f"configuration: {part}/{item} has to be "
                        "a positive integer"
                    )

    except Exception as exc:
        raise OSError(
            f"cannot parse the configuration from {conf_path}.\n"
            + str(exc)
        ) from exc

    return conf


def _read_prompt_template(file_path):
    lines = []
    with open(file_path, encoding="utf8") as fh:
        complete_line = []
        for line in fh:
            if line.endswith("\n"):
                # to get rid of the trailing new-line character
                line = line[:-1]
            if line.endswith("\\"):
                # this line is continued by the next line
                complete_line.append(line[:-1])
            else:
                # this line is not continued by the next line
                complete_line.append(line)
                lines.append("".join(complete_line))
                complete_line = []
        if len(complete_line) > 0:
            lines.append("".join(complete_line))
            complete_line = []
    return "\n".join(lines)


def get_conf(conf_env_name):
    """
    Provides the configuration in a parsed form.
    Requires the path to the configuration file to be set
    in the env. variable setting:ENV_CONF_PATH.
    """
    conf = {
        "urls": {},
        "session": {},
        "handshake": {},
        "query": {},
        "answer": {},
        "view": {},
        "popup": {},
        "ui": {},
        "feeds": {},
        "data": {},
        "prompts": {},
        "llms": {},
        "users": {},
        "keys": {},
        "mocking": {},
        "debugging": {},
    }
    try:
        _fill_conf(conf, _get_conf_path(conf_env_name))
        _complete_conf(conf)
    except Exception as exc:
        conf = None
        log_error("\n".join([
            "cannot read config",
            str(exc),
        ]))

    return conf
