#!/usr/bin/env python
"""
Management of taking and indexing biorxiv feeds.
The indexing is done as an embedding via an LLM.
"""

import os, json, time
import urllib.request
import datetime as dt

from .setting import (
    DATA_DIR_PERM,
    DATA_DIR_CURR,
    NEW_DIRS_MODE,
    ACTIVE_DATA_DIR_MAKING,
    INFO_FILE_NAME,
    EMBED_MODEL_NAME_KEY,
    RSS_FEED_TAKE_SLEEP,
    ATTEMPT_COUNT_FEED,
    RSS_FEED_FILE_NAME,
    ENV_CONF_PATH,
)
from .logging import (
    log_debug,
    log_error,
)
from .utils import (
    list_active_data_dir,
    subject_spec_to_feed_url,
)
from .config import get_conf
from .parser import parse_feed_save_docs
from .indexer import index_docs


def _get_rss_feed_dir(data_dir, subject_fs):
    return os.path.join(data_dir, subject_fs)


def _get_rss_feed_path(data_dir, subject_fs):
    return os.path.join(data_dir, subject_fs, RSS_FEED_FILE_NAME)


def _get_data_dir_perm_parts(current_dt):
    return [
        DATA_DIR_PERM,
        str(current_dt.year).zfill(4),
        "".join([
            str(current_dt.month).zfill(2),
            str(current_dt.day).zfill(2),
        ]),
        "".join([
            str(current_dt.hour).zfill(2),
            str(current_dt.minute).zfill(2)
        ])
    ]


def _prepare_data_dirs(conf, current_dt):
    active_dir = os.path.join(
        conf["data"]["storage_dir"]["path"],
        DATA_DIR_CURR,
    )
    try:
        os.makedirs(active_dir, mode=NEW_DIRS_MODE, exist_ok=True)
        dir_created = True
    except Exception:
        dir_created = False
    if not dir_created:
        return None

    data_dir = os.path.join(
        conf["data"]["storage_dir"]["path"],
        *_get_data_dir_perm_parts(current_dt),
    )
    try:
        os.makedirs(data_dir, mode=NEW_DIRS_MODE, exist_ok=False)
        for _, subject_fs in conf["feeds"]["subjects"]["catalog"].items():
            os.makedirs(
                os.path.join(data_dir, subject_fs),
                mode=NEW_DIRS_MODE,
                exist_ok=True
            )
        dir_created = True
    except Exception:
        dir_created = False

    return data_dir if dir_created else None


def _take_feeds(conf, data_dir):
    got_error = False
    for subject_spec, subject_fs in (
        conf["feeds"]["subjects"]["catalog"].items()
    ):
        feed_url = subject_spec_to_feed_url(subject_spec)
        feed_path = _get_rss_feed_path(data_dir, subject_fs)
        got_feed = False
        time_to_sleep = RSS_FEED_TAKE_SLEEP
        for attempt in range(ATTEMPT_COUNT_FEED):
            time.sleep(time_to_sleep)
            time_to_sleep *= 2
            if conf["debugging"]["feed_taking"]:
                log_debug(f"taking {subject_spec}: attempt #{attempt + 1}")
            try:
                with open(feed_path, "wb") as fh:
                    with urllib.request.urlopen(feed_url) as response:
                        fh.write(response.read())
                got_feed = True
            except Exception:
                got_feed = False
            if got_feed:
                break
        if not got_feed:
            got_error = True
            break
    return not got_error


def _parse_feeds(conf, data_dir):
    got_error = False
    for _, subject_fs in conf["feeds"]["subjects"]["catalog"].items():
        try:
            if not parse_feed_save_docs(
                _get_rss_feed_path(data_dir, subject_fs),
            ):
                got_error = True
                log_error(f"could not parse a feed: {subject_fs}")
                break
        except Exception as exc:
            got_error = True
            log_error(f"feed parsing failed on {subject_fs}:\n" + str(exc))
            break
    return not got_error


def _index_feeds(conf, data_dir):
    got_error = False
    for _, subject_fs in conf["feeds"]["subjects"]["catalog"].items():
        if not index_docs(
            conf,
            _get_rss_feed_dir(data_dir, subject_fs),
        ):
            got_error = True
            break
    return not got_error


def _write_data_info(conf, data_dir):
    file_path = os.path.join(
        data_dir,
        INFO_FILE_NAME,
    )
    data_info = {
        EMBED_MODEL_NAME_KEY: conf["llms"]["embed_model_name"],
    }
    try:
        with open(file_path, "w", encoding="utf8") as fh:
            json.dump(data_info, fh)
        info_written = True
    except Exception:
        info_written = False

    return info_written


def _get_dt_active_dir(dt_obj):
    return dt_obj.strftime(ACTIVE_DATA_DIR_MAKING)


def _make_data_dir_active(conf, current_dt):
    link_src = os.path.join(
        "..",
        *_get_data_dir_perm_parts(current_dt),
    )
    link_dst = os.path.join(
        conf["data"]["storage_dir"]["path"],
        DATA_DIR_CURR,
        _get_dt_active_dir(current_dt),
    )
    try:
        os.symlink(link_src, link_dst)
        done = True
    except Exception:
        done = False
    return done


def _unlink_prev_active_dirs(conf, current_dt):
    active_dir = _get_dt_active_dir(current_dt)

    has_removed = True
    for item in list_active_data_dir(conf):
        if active_dir <= str(item.parts[-1]):
            continue
        try:
            item.unlink(missing_ok=True)
        except Exception:
            has_removed = False

    return has_removed


def ingest_feeds():
    """
    Manages the overall process of:
    * downloading RSS feeds from biorxiv,
    * parsing the feeds and saving the respective data as JSON docs,
    * putting relevant parts of teh docs to LLM for embedding,
    * saving the embedded data and related information.
    """
    try:
        conf = get_conf(ENV_CONF_PATH)
        if conf is None:
            log_error("cannot get configuration")
            return False
        current_dt = dt.datetime.now(dt.UTC)
        data_dir = _prepare_data_dirs(conf, current_dt)
        if data_dir is None:
            log_error("cannot get data directory")
            return False
        if not _take_feeds(conf, data_dir):
            log_error("cannot take feeds")
            return False
        if not _parse_feeds(conf, data_dir):
            log_error("cannot parse feeds")
            return False
        if not _index_feeds(conf, data_dir):
            log_error("cannot index feeds")
            return False
        if not _write_data_info(conf, data_dir):
            log_error("cannot write data info")
            return False
        if not _make_data_dir_active(conf, current_dt):
            log_error("cannot make data dir active")
            return False
        if not _unlink_prev_active_dirs(conf, current_dt):
            # a failure here is not critical
            log_error("cannot remove previous active dirs")
        return True
    except Exception as exc:
        log_error(str(exc))
    return False
