#!/usr/bin/env python
"""
Taking, parsing and checking the configuration.
"""

import os, tomllib, string, importlib
from pathlib import Path
from urllib.parse import urlparse

from .setting import (
    SPEC_PATH_PREFIX,
    CONFIG_ITEM_COMMENT,
    CONFIG_OTHER_LETTERS,
    NEW_DIRS_MODE,
    SESSION_CLUE_LEN_BASE,
    MAX_RECALL_SIFTS_COUNT,
    BIORXIV_SUBJECT_NAMES,
    BIORXIV_FEED_SIZE,
    ENV_HF_MODELS_CACHE_DIR,
    ENV_HF_ASSETS_CACHE_DIR,
    HF_MODELS_SUBDIR,
    HF_ASSETS_SUBDIR,
    HNSWLIB_PATCHED_CHECK,
    HNSWLIB_PATCHED_SEARCH,
    PRESIFT_LAST_COUNT,
    PRESIFT_LAST_DAYS,
    LLM_API_FORM_RESPONSES,
    LLM_API_FORM_CHAT_COMPLETIONS,
    LLM_PROMPT_COMMENT_START,
)
from .utils import (
    subject_spec_to_base_subjects,
    take_access_list,
)
from .logging import (
    log_error,
)


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
                f"configuration: {conf_part['value']}\n{conf_part['path']}\n"
                "has to be a directory"
            )
    else:
        if not os.path.isfile(conf_part["path"]):
            raise OSError(
                f"configuration: {conf_part['value']}\n{conf_part['path']}\n"
                "has to be a file"
            )

    if not os.access(conf_part["path"], os.R_OK):
        raise OSError(
            f"configuration: {conf_part['value']}\n{conf_part['path']}\n"
            "has to be readable"
        )

    if not writable:
        return

    if (
        (not os.access(conf_part["path"], os.W_OK))
    ):
        raise OSError(
            f"configuration: {conf_part['value']}\n{conf_part['path']}\n"
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
    for item in subject_list:
        if item.find(" ") > -1:
            raise OSError(
                "configuration: subject names cannot contain spaces: "
                f"{item}"
            )

    conf_part["catalog"] = {
        item: subject_spec_to_base_subjects(item)
        for item in subject_list if item != ""
    }
    if len(conf_part["catalog"]) == 0:
        raise OSError(
            "configuration: subject list (feeds/subjects) has to have "
            f"at least one item\n{str(conf_part["path"])}"
        )

    conf_part["bare"] = {}
    for _, base_subjects in conf_part["catalog"].items():
        for subject in base_subjects:
            if subject not in BIORXIV_SUBJECT_NAMES:
                raise OSError(
                    "configuration: subject list (feeds/subjects) contains "
                    f"an unknown subject: {subject}"
                )
            conf_part["bare"][subject] = True

    conf_part["list"] = sorted(list(conf_part["bare"]))


def _set_model_dirs(conf_embed):
    conf_embed["models_cache_dir"] = {
        "path": os.path.join(
            conf_embed["models_base_dir"]["path"],
            HF_MODELS_SUBDIR,
        ),
    }
    os.environ[ENV_HF_MODELS_CACHE_DIR] = (
        conf_embed["models_cache_dir"]["path"]
    )

    conf_embed["assets_cache_dir"] = {
        "path": os.path.join(
            conf_embed["models_base_dir"]["path"],
            HF_ASSETS_SUBDIR,
        ),
    }
    os.environ[ENV_HF_ASSETS_CACHE_DIR] = (
        conf_embed["assets_cache_dir"]["path"]
    )

    _check_conf_path_access(conf_embed["models_base_dir"], is_dir=True)
    _check_conf_path_access(conf_embed["models_cache_dir"], is_dir=True)


def _check_conf_header_origin(header_origin):
    if header_origin == "":
        return

    origin_parts = urlparse(header_origin)

    if origin_parts.scheme not in ["http", "https"]:
        raise OSError(
            "configuration: 'server'/'header_origin' "
            "must either be empty or start with http(s)://\n"
            f"it is: {header_origin}"
        )

    if (
        (len(origin_parts.netloc) == 0)
        or (len(origin_parts.path) != 0)
        or (len(origin_parts.params) != 0)
        or (len(origin_parts.query) != 0)
        or (len(origin_parts.fragment) != 0)
    ):
        raise OSError(
            "configuration: wrong 'server'/'header_origin' spec; "
            "when filled, it must be http(s)://domain.name(:port)\n"
            f"it is: {header_origin}"
        )

    try:
        if origin_parts.hostname is None:
            raise OSError("hostname missing")
        if origin_parts.port is not None:
            if type(origin_parts.port) is not int:
                raise OSError("port is not integer")
    except Exception as exc:
        raise OSError(
            "configuration: malformed 'server'/'header_origin' spec\n"
            f"it is: {header_origin}"
        ) from exc


def _load_hnswlib(conf_libs):
    if conf_libs["hnswlib"]["value"] == "":
        raise OSError("only the patched version of hnswlib is supported")

    _check_conf_path_access(conf_libs["hnswlib"], is_dir=True)
    found_libraries = list(Path(conf_libs["hnswlib"]["path"]).glob(
        HNSWLIB_PATCHED_SEARCH
    ))
    if len(found_libraries) != 1:
        raise OSError("cannot find the customized hnswlib")
    try:
        spec = importlib.util.spec_from_file_location(
            "hnswlib", found_libraries[0]
        )
        conf_libs["hnswlib"]["module"] = (
            importlib.util.module_from_spec(spec)
        )
    except Exception as exc:
        raise OSError("cannot import the customized hnswlib") from exc

    try:
        conf_libs["hnswlib"]["with_unique_docs"] = (
            getattr(conf_libs["hnswlib"]["module"], HNSWLIB_PATCHED_CHECK)
            if hasattr(conf_libs["hnswlib"]["module"], HNSWLIB_PATCHED_CHECK)
            else False
        )
        if not conf_libs["hnswlib"]["with_unique_docs"]:
            raise OSError(
                "the imported hnswlib is without support "
                "for knn search with unique docs"
            )
    except Exception as exc:
        raise OSError("check of the imported hnswlib has failed") from exc


def _load_access_specs(conf_access, with_guest):
    conf_access["user_allow_list"]["list"] = []
    conf_access["user_block_list"]["list"] = []
    conf_access["guest_allow_list"]["list"] = []
    conf_access["guest_block_list"]["list"] = []

    for spec in ([
        "user_allow_list",
        "user_block_list",
    ] + ([
        "guest_allow_list",
        "guest_block_list",
    ] if with_guest else [])):
        if conf_access[spec]["value"] != "":
            _check_conf_path_access(conf_access[spec])

        if conf_access[spec]["value"] != "":
            if not take_access_list(conf_access[spec], True, log_error):
                raise OSError("\n".join([
                    "cannot take IP-address range specifications from:",
                    conf_access[spec]["path"],
                ]))


def _check_llm_api_form(conf_llm):
    known_api_forms = [
        LLM_API_FORM_RESPONSES,
        LLM_API_FORM_CHAT_COMPLETIONS,
    ]
    if conf_llm["asking_form"] not in known_api_forms:
        raise OSError("\n".join([
            "configuration: 'llms'/'asking_form' "
            f"has to be one of {known_api_forms}"
        ]))


def _setup_prompt_parts(conf):
    conf["prompts"]["main_part"]["content"] = _read_prompt_template(
        conf["prompts"]["main_part"]["path"]
    ).replace(
        "{max_count}",
        str(conf["sifting"]["answer_max_count"]),
    )

    conf["prompts"]["asking_honest"]["content"] = _read_prompt_template(
        conf["prompts"]["asking_honest"]["path"]
    ) if conf["llms"]["ask_honest"] else ""
    if conf["prompts"]["asking_honest"]["content"] != "":
        conf["prompts"]["asking_honest"]["content"] = (
            "\n" + conf["prompts"]["asking_honest"]["content"]
        )

    conf["prompts"]["query_part"]["content"] = _read_prompt_template(
        conf["prompts"]["query_part"]["path"]
    )

    conf["prompts"]["asking_think"]["content"] = _read_prompt_template(
        conf["prompts"]["asking_think"]["path"]
    )

    conf["prompts"]["asking_cot"]["content"] = _read_prompt_template(
        conf["prompts"]["asking_cot"]["path"]
    )


def _complete_conf(conf):
    _check_conf_header_origin(conf["server"]["header_origin"])

    _load_access_specs(conf["access"], conf["users"]["with_guest"])

    if (conf["session"]["clue_len"] % SESSION_CLUE_LEN_BASE) != 0:
        raise OSError(
            "configuration: 'session'/'clue_len' "
            f"has to be mutiple of {SESSION_CLUE_LEN_BASE}"
        )

    _read_conf_file(conf["view"]["main_page"])
    conf["view"]["main_page"]["rendered"] = (
        conf["view"]["main_page"]["content"].replace(
            "{path_prefix}",
            conf["view"]["path_prefix"],
        )
    )

    _check_conf_path_access(conf["view"]["static_dir"], is_dir=True)

    _read_conf_file(conf["notices"]["note_users"])

    if conf["ui"]["recall_sifts"] > MAX_RECALL_SIFTS_COUNT:
        raise OSError(
            "configuration: 'ui'/'recall_sifts' "
            f"has to at most {MAX_RECALL_SIFTS_COUNT}"
        )

    _read_subject_list(conf["feeds"]["subjects"])
    if (
        conf["feeds"]["default_subject"] not in
        conf["feeds"]["subjects"]["catalog"]
    ):
        raise OSError(
            "configuration: 'feeds'/'default_subject' "
            "has to be one of the (combinations of) subjects "
            "listed at the 'feeds'/'subjects' file"
        )
    if conf["feeds"]["feed_size"] != BIORXIV_FEED_SIZE:
        raise OSError(
            "configuration: 'feeds'/'feed_size' "
            f"has to be set to {BIORXIV_FEED_SIZE}"
        )

    _check_conf_path_access(
        conf["data"]["storage_dir"],
        is_dir=True,
        writable=True,
    )

    if (
        (conf["data"]["depo_kept_days"] != 0)
        and (
            conf["data"]["depo_kept_days"] < (
                conf["data"]["depo_depth"]
                + conf["data"]["kept_days"]
            )
        )
    ):
        raise OSError(" ".join([
            "configuration: 'data'/'depo_kept_days'",
            "(" + str(conf["data"]["depo_kept_days"]) + ")",
            "if nonzero",
            "cannot be lesser than the sum of 'data'/'depo_depth'",
            "(" + str(conf["data"]["depo_depth"]) + ")",
            "and of 'data'/'kept_days'",
            "(" + str(conf["data"]["kept_days"]) + ")",
            "with the sum being:",
            str(conf["data"]["depo_depth"] + conf["data"]["kept_days"]),
        ]))

    _load_hnswlib(conf["libs"])

    _setup_prompt_parts(conf)

    _check_llm_api_form(conf["llms"])

    _set_model_dirs(conf["embed"])

    if (
        (conf["embed"]["dense_embed_model"] == "")
        or (conf["embed"]["static_embed_model"] == "")
    ):
        raise OSError(
            "configuration: 'embed', model names have to be filled "
            "both for 'dense_embed_model' and 'static_embed_model'"
        )

    if (
        (
            conf["sifting"]["pick_count_dense"]
            + conf["sifting"]["pick_count_static"]
        )
        < conf["sifting"]["answer_max_count"]
    ):
        raise OSError(
            "configuration: 'sifting', "
            "it does not make sense to have 'answer_max_count' "
            "bigger than the sum of 'pick_count_dense' "
            "and 'pick_count_static'"
        )

    _check_conf_path_access(conf["users"]["regular_users"])

    if conf["users"]["with_guest"]:
        _check_conf_path_access(
            conf["users"]["guest_ids"],
            is_dir=True,
            writable=True,
        )

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
            ["server", ["header_origin", "address"]],
            ["view", ["path_prefix"]],
            ["backlink", ["name", "link", "title"]],
            ["feeds", ["default_subject"]],
            ["embed", ["dense_embed_model", "static_embed_model"]],
            ["llms", ["model_name", "base_url", "asking_form"]],
        ]:
            for item in itemlist:
                conf[part][item] = str(conf_raw[part][item])
                if conf[part][item].lower().startswith(SPEC_PATH_PREFIX):
                    item_path = os.path.normpath(
                        os.path.join(
                            conf_dir,
                            conf[part][item][len(SPEC_PATH_PREFIX):],
                        )
                    )
                    with open(item_path, encoding="utf8") as fh:
                        conf[part][item] = " ".join([
                            line.strip() for line in fh
                            if not line.startswith(CONFIG_ITEM_COMMENT)
                        ]).strip()

        for part, itemlist in [
            ["ui", ["user_id", "storage_prefix"]],
        ]:
            for item in itemlist:
                conf[part][item] = str(conf_raw[part][item])
                for c in list(conf[part][item]):
                    if (
                        (c not in string.ascii_letters)
                        and (c not in string.digits)
                        and (c not in CONFIG_OTHER_LETTERS)
                    ):
                        raise OSError(
                            f"configuration: {part}/{item} has to be "
                            "a string of ascii letters, digits and/or the "
                            f"{CONFIG_OTHER_LETTERS} characters"
                        )

        for part, itemlist in [
            ["access", [
                "user_allow_list",
                "user_block_list",
                "guest_allow_list",
                "guest_block_list",
            ]],
            ["view", ["main_page", "static_dir"]],
            ["notices", ["note_users"]],
            ["feeds", ["subjects"]],
            ["data", ["storage_dir"]],
            ["libs", ["hnswlib"]],
            ["embed", ["models_base_dir"]],
            ["prompts", [
                "main_part",
                "query_part",
                "asking_honest",
                "asking_think",
                "asking_cot",
            ]],
            ["users", ["regular_users", "guest_ids"]],
            ["keys", ["regular_users", "guest_user"]],
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
            ["server", ["behind_proxy"]],
            ["access", [
                "user_default_allow",
                "user_show_blocked_ip",
                "guest_default_allow",
                "guest_show_blocked_ip",
            ]],
            ["notices", ["note_users_html"]],
            ["feeds", ["allow_combinations"]],
            ["data", ["pruning"]],
            ["llms", ["ask_honest"]],
            ["users", ["with_guest"]],
            ["mocking", ["to_mock"]],
            ["debugging", ["query_sifting", "feed_ingest"]],
        ]:
            for item in itemlist:
                conf[part][item] = conf_raw[part][item]
                if type(conf[part][item]) is not bool:
                    raise OSError(
                        f"configuration: {part}/{item} has to be a boolean"
                    )

        for part, itemlist in [
            ["ui", ["retain_user", "recall_sifts"]],
            ["data", ["depo_kept_days"]],
            ["sifting", [
                "pick_count_dense",
                "pick_count_static",
                "answer_max_count",
            ]],
            ["llms", ["max_tokens"]],
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
            ["server", ["port"]],
            ["data", ["kept_days", "depo_depth", "depo_renew"]],
            ["embed", ["dense_embed_dim", "static_embed_dim"]],
            ["sifting", ["answer_max_count"]],
            ["llms", ["timeout"]],
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
            if line.startswith(LLM_PROMPT_COMMENT_START):
                continue
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


def _add_to_conf(conf):
    # this value has to be kept fixed equal to the actual size
    # of individual biorxiv RSS feeds
    conf["feeds"]["feed_size"] = BIORXIV_FEED_SIZE

    # parts of conf with mostly arbitrary values
    conf["session"] = {
        "clue_vis": "clue_one",
        "clue_hid": "clue_two",
        "clue_str": "clue_three",
        "clue_len": 16,
        "provided": "available",
    }
    conf["handshake"] = {
        "count": 2,
        "first_bits": 8,
    }
    # handshake_start is an auxiliary variable used during inital handshakes
    # between a user and the arxifter server when a query is put to LLM
    handshake_start = 2
    for _ in range(conf["handshake"]["first_bits"] - 1):
        handshake_start <<= 2
        handshake_start += 2
    conf["handshake"]["handshake_start"] = handshake_start
    conf["query"] = {
        "query_text": "query",
        "feed_type": "last",
        "feed_type_days": PRESIFT_LAST_DAYS,
        "feed_type_counts": PRESIFT_LAST_COUNT,
        "user_id": "user",
        "is_guest": "guest",
    }
    conf["answer"] = {
        "llm_response": "answer",
        "sys_message": "message",
    }

    return conf


def get_conf(conf_env_name):
    """
    Provides the configuration in a parsed form.
    Requires the path to the configuration file to be set
    in the env. variable setting:ENV_CONF_PATH.
    """
    conf = {
        "server": {},
        "access": {},
        "view": {},
        "backlink": {},
        "notices": {},
        "ui": {},
        "feeds": {},
        "data": {},
        "libs": {},
        "embed": {},
        "sifting": {},
        "prompts": {},
        "llms": {},
        "users": {},
        "keys": {},
        "mocking": {},
        "debugging": {},
    }
    try:
        _fill_conf(conf, _get_conf_path(conf_env_name))
        _add_to_conf(conf)
        _complete_conf(conf)
    except Exception as exc:
        conf = None
        log_error("\n".join([
            "cannot read config",
            str(exc),
        ]))

    return conf
