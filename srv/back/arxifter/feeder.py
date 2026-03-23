#!/usr/bin/env python
"""
Management of taking and indexing biorxiv feeds.
The indexing is done locally via embeddings.
"""

import os, time, json
import urllib.request
import datetime as dt
from pathlib import Path

from .setting import (
    DATA_DIR_PERM,
    DATA_DIR_CURR,
    NEW_DIRS_MODE,
    ACTIVE_DATA_DIR_MAKING,
    RSS_FEED_TAKE_SLEEP,
    RSS_FEED_INDEX_SLEEP,
    RSS_FEED_TAKE_TIMEOUT,
    ATTEMPT_COUNT_FEED,
    RSS_FEED_FILE_NAME,
    ENV_CONF_PATH,
    DOCUMENTS_SUBDIR,
    HNSWDATA_SUBDIR,
    VECTORS_SUBDIR,
)
from .logging import (
    log_message,
    log_debug,
    log_info,
    log_warning,
    log_error,
)
from .utils import (
    list_active_data_dir,
    subject_spec_to_feed_url,
    get_current_data_dir,
    load_encoders_info,
    check_encoders_info,
    save_encoders_info,
)
from .config import get_conf
from .parser import parse_feed_save_docs
from .encoder import get_encoders
from .indexer import index_docs
from .spans.depositer import assure_document_suite_stored


def _get_rss_feed_dir(data_dir, subject):
    if data_dir is None:
        return None
    return os.path.join(data_dir, subject)


def _get_rss_feed_path(data_dir, subject):
    if data_dir is None:
        return None
    return os.path.join(data_dir, subject, RSS_FEED_FILE_NAME)


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


def _get_active_dir_docs(data_dir, subject):
    for one_doc_path in sorted(Path(
        data_dir,
        subject,
        DOCUMENTS_SUBDIR,
    ).glob("???.json")):
        yield one_doc_path


def _get_doc_embed_split(data_dir, subject, doc_name_stem):
    split_embed_path = Path(
        data_dir,
        subject,
        HNSWDATA_SUBDIR,
        doc_name_stem + ".npy",
    )

    with open(split_embed_path, "rb") as fh:
        return fh.read()


def _get_doc_embed_whole(data_dir, subject, doc_name_stem):
    whole_embed_path = Path(
        data_dir,
        subject,
        VECTORS_SUBDIR,
        doc_name_stem + ".npy",
    )

    with open(whole_embed_path, "rb") as fh:
        return fh.read()


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
        for subject in conf["feeds"]["subjects"]["list"]:
            os.makedirs(
                os.path.join(data_dir, subject),
                mode=NEW_DIRS_MODE,
                exist_ok=True
            )
        dir_created = True
    except Exception:
        dir_created = False

    return data_dir if dir_created else None


def _take_feeds(conf, data_dir):
    got_error = False
    first_download = True
    for subject in conf["feeds"]["subjects"]["list"]:
        feed_url = subject_spec_to_feed_url(subject)
        feed_path = _get_rss_feed_path(data_dir, subject)
        got_feed = False
        time_to_sleep = RSS_FEED_TAKE_SLEEP
        for attempt in range(ATTEMPT_COUNT_FEED):
            if not first_download:
                time.sleep(time_to_sleep)
            else:
                first_download = False
            time_to_sleep *= 2
            if conf["debugging"]["feed_ingest"]:
                log_debug(f"taking {subject}: attempt #{attempt + 1}")
            try:
                with open(feed_path, "wb") as fh:
                    with urllib.request.urlopen(
                        feed_url, timeout=RSS_FEED_TAKE_TIMEOUT
                    ) as response:
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
    for subject in conf["feeds"]["subjects"]["list"]:
        try:
            if not parse_feed_save_docs(
                _get_rss_feed_path(data_dir, subject), subject
            ):
                got_error = True
                log_error(f"could not parse a feed: {subject}")
                break
        except Exception as exc:
            got_error = True
            log_error(f"feed parsing failed on {subject}:\n" + str(exc))
            break
    return not got_error


def _get_prev_feed_dir(conf, encoders):
    # the dir from where embedding vectors can be reused
    # is the current data dir, but that only if the encoders
    # used then and to be used now are the same;
    prev_data_dir = get_current_data_dir(conf)
    if prev_data_dir is None:
        log_info("there are no previously ingested feeds present")
        return None

    if not check_encoders_info(
        load_encoders_info(prev_data_dir),
        encoders,
    ):
        log_info("cannot reuse previous vectors, b/c encoders differ")
        return None

    return prev_data_dir


def _index_feeds(conf, data_dir, prev_data_dir, encoders):
    got_error = False
    time_spans = []
    first_subject = True
    for subject in conf["feeds"]["subjects"]["list"]:
        if not first_subject:
            time.sleep(RSS_FEED_INDEX_SLEEP)
        else:
            first_subject = False

        time_start = time.time()
        res = index_docs(
            conf,
            encoders,
            _get_rss_feed_dir(data_dir, subject),
            _get_rss_feed_dir(prev_data_dir, subject),
        )
        time_spans.append(time.time() - time_start)
        if not res:
            got_error = True
            break

    log_info(f"indexing took {sum(time_spans)} s overall")
    if conf["debugging"]["feed_ingest"]:
        log_message(str(time_spans))

    return not got_error


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


def _put_feed_to_spans(conf, current_dt, data_dir, encoders):
    for subject in conf["feeds"]["subjects"]["list"]:
        for doc_path in _get_active_dir_docs(data_dir, subject):
            try:
                with open(doc_path, encoding="utf8") as fh:
                    doc_data = json.load(fh)

                split_embed_blob = _get_doc_embed_split(
                    data_dir,
                    subject,
                    doc_path.stem,
                )

                whole_embed_blob = _get_doc_embed_whole(
                    data_dir,
                    subject,
                    doc_path.stem,
                )

                if not assure_document_suite_stored(
                    conf,
                    subject,
                    current_dt,
                    doc_data,
                    split_embed_blob,
                    whole_embed_blob,
                    encoders,
                ):
                    log_warning("\n".join([
                        "could not put doc suite to depo",
                        str(doc_path),
                    ]))
            except Exception as exc:
                log_warning("\n".join([
                    "cannot put a doc suite to the depo",
                    str(subject),
                    str(doc_path),
                    str(exc),
                ]))


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
        encoders = get_encoders(conf)
        if encoders is None:
            log_error("cannot get the encoders")
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
        prev_data_dir = _get_prev_feed_dir(conf, encoders)
        if not _index_feeds(conf, data_dir, prev_data_dir, encoders):
            log_error("cannot index feeds")
            return False
        if not save_encoders_info(data_dir, encoders):
            log_error("cannot save the encoders-data info")
            return False
        if not _make_data_dir_active(conf, current_dt):
            log_error("cannot make data dir active")
            return False
        if not _unlink_prev_active_dirs(conf, current_dt):
            # a failure here is not critical
            log_error("cannot remove previous active dirs")

        # it can work even if docs/vecs do not get put to depo
        _put_feed_to_spans(conf, current_dt, data_dir, encoders)

        return True
    except Exception as exc:
        log_error(str(exc))
    return False
