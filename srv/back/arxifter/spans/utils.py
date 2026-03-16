#!/usr/bin/env python
"""
Assorted auxiliary functions.
"""

import os, re, json, shutil
from pathlib import Path

from ..setting import (
    ATTEMPT_COUNT_DATA_DIR,
    INFO_FILE_NAME,
    STATIC_EMBED_MODEL_NAME_KEY,
    DENSE_EMBED_MODEL_NAME_KEY,
)
from ..logging import (
    log_warning,
    log_error,
)
from .setting import (
    DATA_DIR_DEPO,
    DATA_DIR_LAST,
    LAST_DATA_DIR_LISTING,
    STATIC_EMBED_MODEL_DIM_KEY,
    DENSE_EMBED_MODEL_DIM_KEY,
)


def list_active_data_dir(conf):
    """
    Provides the symlinks (to spans) within the 'last' directory.
    """
    data_dir_curr = os.path.join(
        conf["data"]["storage_dir"]["path"],
        DATA_DIR_LAST,
    )
    for item in sorted(Path(data_dir_curr).glob("*"), reverse=True):
        if not item.is_dir():
            continue
        if re.match(LAST_DATA_DIR_LISTING, item.parts[-1]) is None:
            continue
        yield item


def get_last_data_dir(conf):
    """
    Provides the newest symlink (to a span) from the 'last' directory.
    """
    dir_path = None
    for _ in range(ATTEMPT_COUNT_DATA_DIR):
        try:
            dir_test = None
            for item in list_active_data_dir(conf):
                dir_test = str(item)
                break
            if dir_test is not None:
                dir_test = str(Path(dir_test).resolve())
                if Path(dir_test).exists():
                    dir_path = dir_test
        except Exception as exc:
            log_warning("\n".join([
                "an issue with taking the current 'last' dir",
                str(exc),
            ]))
            dir_path = None
        if dir_path is not None:
            break
    return dir_path


def _get_depo_enc_info_path(conf):
    data_root = conf["data"]["storage_dir"]["path"]
    depo_dir = Path(data_root, DATA_DIR_DEPO)
    return depo_dir / INFO_FILE_NAME


def _get_last_enc_info_path(curr_dir):
    return Path(curr_dir, INFO_FILE_NAME)


def _compare_enc_info(info_path, encoders):
    with open(info_path, encoding="utf8") as fh:
        past_enc_info = json.load(fh)
        if (
            (
                past_enc_info[STATIC_EMBED_MODEL_NAME_KEY]
                != encoders["static"]["name"]
            )
            or (
                past_enc_info[STATIC_EMBED_MODEL_DIM_KEY]
                != encoders["static"]["dim"]
            )
        ):
            return False
        if (
            (
                past_enc_info[DENSE_EMBED_MODEL_NAME_KEY]
                != encoders["dense"]["name"]
            )
            or (
                past_enc_info[DENSE_EMBED_MODEL_DIM_KEY]
                != encoders["dense"]["dim"]
            )
        ):
            return False
    return True


def assure_depo_encoding_info(conf, encoders):
    """
    Stores the encoding info of the current encoders into the depo
    directory if there is no such info stored yet.
    If there is an encoding info already stored in the depo directory,
    it is checked whether it is the same as that of the current encoders.
    """
    try:
        depo_info_path = _get_depo_enc_info_path(conf)
        if depo_info_path.exists():
            if not _compare_enc_info(depo_info_path, encoders):
                return False

        with open(depo_info_path, "w", encoding="utf8") as fh:
            json.dump({
                STATIC_EMBED_MODEL_NAME_KEY: encoders["static"]["name"],
                STATIC_EMBED_MODEL_DIM_KEY: encoders["static"]["dim"],
                DENSE_EMBED_MODEL_NAME_KEY: encoders["dense"]["name"],
                DENSE_EMBED_MODEL_DIM_KEY: encoders["dense"]["dim"],
            }, fh)

    except Exception as exc:
        log_error("\n".join([
            "could not assure encoding info in depo",
            str(exc),
        ]))
        return False

    return True


def set_last_encoding_info(conf, curr_dir):
    """
    Stores the current encoding info into the given span directory.
    """
    try:
        depo_info_path = _get_depo_enc_info_path(conf)
        last_info_path = _get_last_enc_info_path(curr_dir)
        shutil.copy2(depo_info_path, last_info_path)
    except Exception as exc:
        log_error("\n".join([
            "could not set the encoding info in the current span dir",
            str(exc),
        ]))
        return False

    return True


def check_last_encoding_info(encoders, curr_dir):
    """
    Checks whether the encoding info of the given span directory
    is the same as that of the currently used encoders.
    """
    try:
        last_info_path = _get_last_enc_info_path(curr_dir)
        if last_info_path.exists():
            if not _compare_enc_info(last_info_path, encoders):
                return False
    except Exception as exc:
        log_error("\n".join([
            "could not check the encoding info at the current span dir",
            str(exc),
        ]))
        return False

    return True


def load_last_encoding_info(curr_dir):
    """
    Provides the encoding info of the given span directory.
    """
    try:
        last_info_path = _get_last_enc_info_path(curr_dir)
        if last_info_path.exists():
            with open(last_info_path, encoding="utf8") as fh:
                return json.load(fh)
    except Exception as exc:
        log_error("\n".join([
            "could not take encoding info from the current span dir",
            str(exc),
        ]))
        return None
    return None
