#!/usr/bin/env python
"""
Removal of previously ingested feeds.
Look at the [data] part of configuration for the setting of it.
"""

import os, shutil, json
from pathlib import Path
import datetime as dt

from .setting import (
    ENV_CONF_PATH,
    INFO_FILE_NAME,
    STATIC_EMBED_MODEL_NAME_KEY,
    DENSE_EMBED_MODEL_NAME_KEY,
)
from .logging import log_error
from .utils import list_stored_data_dirs
from .config import get_conf


def _has_indexed_storage(day_dir):
    index_found = False
    for subdir in Path(day_dir).glob("*"):
        info_path = os.path.join(str(subdir), INFO_FILE_NAME)
        if os.path.exists(info_path):
            try:
                with open(info_path, encoding="utf8") as fh:
                    embed_desc = json.load(fh)
                    has_desc_keys = True
                    for desc_key in [
                        STATIC_EMBED_MODEL_NAME_KEY,
                        DENSE_EMBED_MODEL_NAME_KEY,
                    ]:
                        if embed_desc.get(desc_key, "") == "":
                            has_desc_keys = False
                            break
                    if has_desc_keys:
                        index_found = True
            except Exception:
                index_found = False
            if index_found:
                break
    return index_found


def _remove_old_stored_day_dirs(conf):
    if not conf["data"]["pruning"]:
        return
    keep_count = conf["data"]["kept_days"]
    current_count = 0
    to_remove = False
    try:
        for day_dir in list_stored_data_dirs(conf):
            if not to_remove:
                if _has_indexed_storage(day_dir):
                    current_count += 1
                if current_count == keep_count:
                    to_remove = True
                continue
            shutil.rmtree(day_dir, ignore_errors=True)
    except Exception:
        pass


def _remove_empty_stored_year_dirs(conf):
    # should keep year-dirs even if empty for today/yesterday times,
    # b/c they could had been just created during an onging feeding
    if not conf["data"]["pruning"]:
        return
    yesterday_year = str(
        (dt.datetime.now(dt.UTC) - dt.timedelta(days=1)).year
    )
    for item in list_stored_data_dirs(conf, years_only=True):
        if not item.is_dir():
            continue
        item_year = item.parts[-1] if len(item.parts) > 0 else ""
        if len(item_year) != 4:
            continue
        if item_year >= yesterday_year:
            continue
        if any(item.iterdir()):
            continue
        try:
            os.rmdir(str(item))
        except Exception:
            pass


def prune_feeds():
    """
    Prunes the ingested feeds.
    The count of kept batches of ingested feeds is set in configuration.
    """
    try:
        conf = get_conf(ENV_CONF_PATH)
        if conf is None:
            log_error("cannot get configuration")
            return False
        _remove_old_stored_day_dirs(conf)
        _remove_empty_stored_year_dirs(conf)
        return True
    except Exception as exc:
        log_error(str(exc))
    return False
