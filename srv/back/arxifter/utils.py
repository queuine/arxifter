#!/usr/bin/env python
"""
Assorted auxiliary functions.
"""

import os, re
from pathlib import Path

from .setting import (
    ACTIVE_DATA_DIR_LISTING,
    DATA_DIR_PERM,
    DATA_DIR_CURR,
    ATTEMPT_COUNT_DATA_DIR,
)


def list_stored_data_dirs(conf, years_only=False):
    """
    The directories where the batches of ingested feeds are stored.
    """
    data_dir_stored = os.path.join(
        conf["data"]["storage_dir"]["path"],
        DATA_DIR_PERM,
    )
    for item_year in sorted(Path(data_dir_stored).glob("*"), reverse=True):
        if not item_year.is_dir():
            continue
        if years_only:
            yield item_year
            continue
        for item_day in sorted(item_year.glob("*"), reverse=True):
            if not item_day.is_dir():
                continue
            yield item_day


def list_active_data_dir(conf):
    """
    The directories that are prepared to be used for loading ingested feeds.
    Each such directory corresponds to one batch of the feeds.
    """
    data_dir_curr = os.path.join(
        conf["data"]["storage_dir"]["path"],
        DATA_DIR_CURR,
    )
    for item in sorted(Path(data_dir_curr).glob("*"), reverse=True):
        if not item.is_dir():
            continue
        if re.match(ACTIVE_DATA_DIR_LISTING, item.parts[-1]) is None:
            continue
        yield item


def get_current_data_dir(conf):
    """
    Directory to be used as the current batch of ingested feeds.
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
        except Exception:
            dir_path = None
        if dir_path is not None:
            break
    return dir_path


def get_doc_name(rank):
    """
    Name of a JSON doc with data from an entry of a RSS feed.
    """
    return str(rank).zfill(3) + ".json"
