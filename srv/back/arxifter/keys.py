#!/usr/bin/env python
"""
Management of LLM API-keys.
"""

import os
from pathlib import Path
import datetime as dt

from .guests import list_guest_id_files


def _check_user_id_is_guest(conf, user_id, curr_dt):
    if not conf["users"]["with_guest"]:
        return False

    for file_path_obj, hour_diff in list_guest_id_files(conf, curr_dt):
        if hour_diff >= (conf["users"]["guest_span"] + 1):
            break
        try:
            if (
                user_id
                == Path(file_path_obj).read_text(encoding="utf8").strip()
            ):
                return True
        except Exception:
            continue

    return False


def _get_llm_key_guest(conf, user_id):
    curr_dt = dt.datetime.now(dt.UTC)
    if _check_user_id_is_guest(conf, user_id, curr_dt):
        return Path(
            conf["keys"]["guest_user"]["path"]
        ).read_text(encoding="utf8").strip()

    return None


def _get_key_found_user(conf, key_file_name):
    key_path = os.path.join(
        conf["keys"]["regular_users"]["path"],
        key_file_name
    )
    return Path(key_path).read_text(encoding="utf8").strip()


def _get_llm_key_user(conf, user_id=None):
    # searching for the provided user Id
    with open(conf["users"]["regular_users"]["path"], encoding="utf8") as fh:
        at_user_id_line = True
        with_following_key = False
        for line in fh:
            if line.startswith("#"):
                continue
            line = line.strip()
            if line == "":
                continue
            if at_user_id_line:
                if user_id == line:
                    with_following_key = True
            elif with_following_key:
                return _get_key_found_user(conf, line)
            at_user_id_line = not at_user_id_line

    # if here, the provided user Id did not match any user
    return None


def get_user_api_key(conf, user_id, is_guest):
    """
    Provides LLM API-keys for user questions on the indexed feeds.
    """
    if user_id is None:
        return None
    user_id = user_id.strip()
    if user_id == "":
        return None

    if is_guest:
        key = _get_llm_key_guest(conf, user_id)
        return key if ((key is not None) and (key != "")) else None

    key = _get_llm_key_user(conf, user_id)
    if (key is not None) and (key != ""):
        return key

    return None
