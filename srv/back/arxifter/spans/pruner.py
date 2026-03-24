#!/usr/bin/env python
"""
Removal of previously ingested feeds from the depo/span feed parts.
Look at the [data] part of configuration for the setting of it.
"""

import shutil
import datetime as dt

from ..setting import (
    ENV_CONF_PATH,
    STATIC_EMBED_MODEL_NAME_KEY,
    DENSE_EMBED_MODEL_NAME_KEY,
)
from ..logging import log_error
from ..config import get_conf
from .setting import (
    SPAN_DATA_DIR_DATE_INFO_LEN,
)
from .utils import (
    list_span_data_dir,
    load_last_encoding_info,
    list_depo_subject_dirs,
    span_format_current_dt,
)


def _valid_indexed_spec(embed_desc):
    if embed_desc is None:
        return False
    try:
        for desc_key in [
            STATIC_EMBED_MODEL_NAME_KEY,
            DENSE_EMBED_MODEL_NAME_KEY,
        ]:
            if embed_desc.get(desc_key, "") == "":
                return False
    except Exception:
        return False

    return True


def _too_old_depo_subdir(conf, current_dt, date_dir_name, subject):
    base_date = current_dt.date()
    try:
        days_diff = (
            base_date - dt.datetime.strptime(
                date_dir_name + " UTC", "%Y_%m_%d %Z"
            ).date()
        ).days
        if days_diff > conf["data"]["depo_kept_days"]:
            return True
    except Exception as exc:
        log_error("\n".join([
            "could not find whether a 'depo' dir is too old",
            subject,
            date_dir_name,
            str(exc),
        ]))

    return False


def _remove_old_span_dirs(conf, current_dt):
    keep_count = conf["data"]["kept_days"]
    if keep_count == 0:
        return

    current_count = 0
    to_remove = False
    last_date_spec = None
    curr_dt_name = span_format_current_dt(current_dt)
    try:
        for span_dir in list_span_data_dir(conf):
            span_dir_name = span_dir.parts[-1]
            if curr_dt_name < span_dir_name:
                continue
            if not to_remove:
                if not _valid_indexed_spec(
                    load_last_encoding_info(span_dir)
                ):
                    continue
                span_date_spec = span_dir_name[:SPAN_DATA_DIR_DATE_INFO_LEN]
                if span_date_spec == last_date_spec:
                    continue
                last_date_spec = span_date_spec
                current_count += 1
                if current_count == (keep_count + 1):
                    to_remove = True
            if to_remove:
                shutil.rmtree(span_dir, ignore_errors=True)
    except Exception as exc:
        log_error("\n".join([
            "could not prune the 'span' feed part",
            str(exc),
        ]))


def _remove_old_depo_dirs(conf, current_dt):
    if conf["data"]["depo_kept_days"] == 0:
        return

    for subject in conf["feeds"]["subjects"]["list"]:
        for date_dir in list_depo_subject_dirs(conf, subject):
            try:
                if _too_old_depo_subdir(
                    conf, current_dt, date_dir.parts[-1], subject
                ):
                    shutil.rmtree(date_dir, ignore_errors=True)
            except Exception as exc:
                log_error("\n".join([
                    "could not prune a 'depo' feed subpart",
                    str(date_dir),
                    str(exc),
                ]))


def prune_span_depo_feeds(conf=None, current_dt=None):
    """
    Prunes the ingested depo-wise feeds.
    The count of kept batches of ingested feeds is set in configuration.
    """
    if current_dt is None:
        current_dt = dt.datetime.now(dt.UTC)
    try:
        if conf is None:
            conf = get_conf(ENV_CONF_PATH)
            if conf is None:
                log_error("cannot get configuration")
                return False
        if not conf["data"]["pruning"]:
            return True
        _remove_old_span_dirs(conf, current_dt)
        _remove_old_depo_dirs(conf, current_dt)
        return True
    except Exception as exc:
        log_error("\n".join([
            "could not prune the depo/span feed parts",
            str(exc),
        ]))

    return False
