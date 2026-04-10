#!/usr/bin/env python
"""
The last-30 articles per subject has the 30-article sets spanned over
quite varying time scales: from 1-2 days of the neuroscience subject
to half a year of the paleontology subject.
It asks for adding a view that would have some fixed count of days.
This module is aimed to provide a storage access for that.
Contrary to the last-30 articles view, here the docs and vectors
are to be stored named by their DOIs and versions,
as that identifies them: possibly even w/o the versions,
b/c it does not make sense to have an article stored several times.
"""

import os, re, urllib, json, time
from pathlib import Path
import datetime as dt

from ..setting import (
    COMMAND_SPAN_INGEST_INCR,
    COMMAND_SPAN_INGEST_FULL,
    COMMAND_SPAN_INGEST_DAYS,
    NEW_DIRS_MODE,
    ENV_CONF_PATH,
)
from ..logging import (
    log_debug,
    log_warning,
    log_error,
)
from ..config import get_conf
from .setting import (
    DATA_DIR_LAST,
    DATA_DIR_SPAN,
    ACTIVE_SPAN_DIR_LISTING,
    SPAN_DATETIME_GLOB,
    API_FEED_TAKE_SLEEP,
    API_FEED_TAKE_TIMEOUT,
    API_FEED_TAKE_ATTEMPTS,
    API_FEED_TAKE_PAUSE,
)
from .utils import (
    set_last_encoding_info,
    span_format_current_dt,
)
from .depositer import (
    assure_document_stored,
    assure_depo_vectors,
)
from .indexer import index_span_vectors


def _get_span_api_url(date_from, date_upto, offset):
    return "/".join([
        "https://api.biorxiv.org/details/biorxiv",
        date_from.strftime("%Y-%m-%d"),
        date_upto.strftime("%Y-%m-%d"),
        str(offset),
    ])


def _download_span(date_from, date_upto, offset, debugging):
    span_url = _get_span_api_url(date_from, date_upto, offset)
    dose_data = None
    for atempt in range(API_FEED_TAKE_ATTEMPTS):
        if (offset != 0) or (atempt != 0):
            time.sleep(API_FEED_TAKE_SLEEP)
        try:
            if debugging:
                log_debug(f"downloading from: {span_url}")
            with urllib.request.urlopen(
                span_url, timeout=API_FEED_TAKE_TIMEOUT
            ) as response:
                dose_data = response.read()
                break
        except Exception as exc:
            log_warning("\n".join([
                "a dose-download attempt failed",
                str(exc),
            ]))
            dose_data = None

    if dose_data is None:
        log_error("\n".join([
            "could not download an API dose json file",
        ]))
    return dose_data


def _parse_api_response(api_response, debugging):
    try:
        collection_data = json.loads(api_response)
        if debugging:
            try:
                if collection_data is None:
                    log_debug("taking collection data failed")
                else:
                    log_debug("\n".join([
                        "parts of one collection data:",
                        " ".join([
                            "status of taken collection data:",
                            str(collection_data["messages"][0]["status"])
                        ]),
                        " ".join([
                            "length of the data part:",
                            str(len(collection_data["collection"]))
                        ]),
                    ]))
            except Exception as exc:
                log_debug("\n".join([
                    "could not take debug info on the taken collection data",
                    str(exc),
                ]))
        collection_info = collection_data["messages"][0]
        if collection_info["status"] != "ok":
            # no more data were taken while they were still expected;
            # it may but need not be an error:
            # the biorxiv API sometimes provides inaccurate values;
            log_warning(
                "did not take expected collection data, "
                "expecting that it is the end of the overall data dose"
            )
            if "total" not in collection_info:
                collection_info["total"] = None
            if "count" not in collection_info:
                collection_info["count"] = 0
        chunk_data = list(collection_data["collection"])
        if len(chunk_data) != collection_info["count"]:
            collection_info["count"] = len(chunk_data)
            log_warning("inconsistent size info on the taken collection part")
        return {
            "info": {
                "total_size": (
                    int(collection_info["total"])
                    if type(collection_info["total"]) in [int, str]
                    else None
                ),
                "chunk_size": (
                    int(collection_info["count"])
                    if type(collection_info["count"]) in [int, str]
                    else 0
                ),
            },
            "docs": chunk_data,
        }
    except Exception as exc:
        log_error("\n".join([
            "error during parsing the API json response",
            str(exc),
        ]))
        return None


def _save_read_part(conf, collection_docs):
    for one_doc in collection_docs:
        try:
            missed_req_part = None
            for part in ["title", "doi", "date", "category", "abstract"]:
                if part not in one_doc:
                    missed_req_part = part
                    break
            if missed_req_part is not None:
                log_warning("a doc misses a required part: " + part)
                continue
            one_doc["category"] = one_doc["category"].replace(" ", "_")
            if one_doc["category"] not in conf["feeds"]["subjects"]["list"]:
                continue
            if not assure_document_stored(conf, one_doc):
                log_warning("could not save a doc")
        except Exception as exc:
            log_warning("an error during saving a doc: " + str(exc))
            return False
    return True


def _take_one_part(collection_info, debugging):
    collection_data = _download_span(
        collection_info["date_from"],
        collection_info["date_upto"],
        collection_info["offset"],
        debugging,
    )
    if debugging:
        try:
            if collection_data is None:
                log_debug("taking a data dose has failed")
            else:
                log_debug(f"byte-size of data dose is {len(collection_data)}")
        except Exception as exc:
            log_debug("\n".join([
                "taking the byte-size of data dose has failed",
                str(exc),
            ]))
    if collection_data is None:
        return None
    collection_parsed = _parse_api_response(collection_data, debugging)
    if collection_parsed is None:
        return None
    if collection_info["overall_count"] is None:
        collection_info["overall_count"] = (
            collection_parsed["info"]["total_size"]
        )
        if collection_info["overall_count"] is None:
            log_error("apparently no data at all in the asked-for date range")
            return None
        if debugging:
            log_debug(" ".join([
                "expected count of docs in the date range:",
                str(collection_info["overall_count"]),
            ]))
    elif (
        collection_info["overall_count"]
        != collection_parsed["info"]["total_size"]
    ):
        log_warning("changed overall size info")
        collection_info["overall_count"] = (
            collection_parsed["info"]["total_size"]
            if (collection_parsed["info"]["total_size"] is not None)
            else 0
        )
    collection_info["offset"] += collection_parsed["info"]["chunk_size"]
    if len(collection_parsed["docs"]) == 0:
        # if the advertized doc count were correct (sometimes they are not),
        # this situation would mean a failure to take the data;
        # but since the advertized counts are sort-of fuzzy,
        # this situation can happen w/o meaning that an error occurred;
        return []
    return collection_parsed["docs"]


def _take_span_dir(conf, current_dt, relative=False):
    return Path(
        ".." if relative else conf["data"]["storage_dir"]["path"],
        DATA_DIR_SPAN,
        span_format_current_dt(current_dt),
    )


def _prepare_span_dir(conf, current_dt):
    data_dir = _take_span_dir(conf, current_dt, False)
    if data_dir.exists():
        return None

    try:
        os.makedirs(str(data_dir), mode=NEW_DIRS_MODE, exist_ok=True)
    except Exception as exc:
        log_error("\n".join([
            "error during making new span dir",
            str(exc),
        ]))
        return None
    return data_dir


def _set_span_as_active(conf, current_dt):
    try:
        active_path = Path(
            conf["data"]["storage_dir"]["path"],
            DATA_DIR_LAST,
            span_format_current_dt(current_dt),
        )
        os.makedirs(
            str(active_path.parents[0]), mode=NEW_DIRS_MODE, exist_ok=True
        )
        os.symlink(
            str(_take_span_dir(conf, current_dt, True)),
            str(active_path),
        )
        return True
    except Exception as exc:
        log_error("\n".join([
            "error during linking to new span dir",
            str(exc),
        ]))
        return False


def _remove_prev_active_span_dirs(conf, current_dt):
    current_dt_formatted = span_format_current_dt(current_dt)

    error_occurred = False
    for one_path in sorted(Path(
        conf["data"]["storage_dir"]["path"],
        DATA_DIR_LAST,
    ).glob(SPAN_DATETIME_GLOB)):
        if not one_path.is_dir():
            continue
        if re.match(ACTIVE_SPAN_DIR_LISTING, one_path.parts[-1]) is None:
            continue
        if current_dt_formatted <= str(one_path.parts[-1]):
            continue

        try:
            one_path.unlink(missing_ok=True)
        except Exception as exc:
            error_occurred = True
            log_warning("\n".join([
                "cannot unlink",
                str(one_path),
                str(exc)
            ]))

    return not error_occurred


def _save_span(conf, date_from, date_upto, debugging):
    overall_docs_count = 0
    collection_info = {
        "overall_count": None,
        "date_from": date_from,
        "date_upto": date_upto,
        "offset": 0,
    }
    got_error = False
    while True:
        collection_docs = _take_one_part(collection_info, debugging)
        if collection_docs is None:
            got_error = True
            log_error("could not take a span collection")
            break
        dose_count = len(collection_docs)
        if dose_count == 0:
            # the advertized counts of docs (with that info stored
            # in collection_info) are approximative only;
            # and by that it can happen that no doc is received
            # even when expecting to still get some doc;
            log_warning("no doc in a span collection")
            break
        overall_docs_count += dose_count
        if not _save_read_part(conf, collection_docs):
            got_error = True
            log_error("could not save a span collection")
            break
        if debugging:
            log_debug(" <= ".join([
                f"comparing: {collection_info['overall_count']}",
                f"{overall_docs_count}",
            ]))
        if collection_info["overall_count"] <= overall_docs_count:
            if debugging:
                log_debug("the comparison got true")
            break
        if debugging:
            log_debug("the comparison got false")

    if got_error:
        log_error("taking a span failed")
        return False

    if debugging:
        log_debug(" ".join([
            "total count of docs taken from the date range:",
            str(overall_docs_count),
        ]))

    return True


def _turn_span(conf, date_from, date_upto):
    if not assure_depo_vectors(conf, date_from, date_upto):
        log_error("embedding a span failed")
        return False

    return True


def _load_span(conf, current_dt, date_from, date_upto):
    curr_dir = _prepare_span_dir(conf, current_dt)
    if curr_dir is None:
        log_error("\n".join([
            "could not make the spanner directory",
            "preparing a span loading failed",
        ]))
        return False

    if not set_last_encoding_info(conf, curr_dir):
        log_error("could not set the encoding info")
        return False

    if not index_span_vectors(conf, curr_dir, date_from, date_upto):
        log_error("indexing a span failed")
        return False

    if not _set_span_as_active(conf, current_dt):
        log_error("activating a span failed")
        return False

    if not _remove_prev_active_span_dirs(conf, current_dt):
        log_warning("cleaning on a span failed")

    return True


def _write_passage_time_info(start_time, pause_time, passage_type):
    overall_time = time.time() - start_time
    compute_time = overall_time - pause_time
    log_debug(", ".join([
        f"overall {passage_type} time: {overall_time}",
        f"from that computing time: {compute_time}",
    ]))


def ingest_span(ingest_form):
    """
    Ingests doc data from the JSON API.
    The taken doc data are saved to depo, their embeddings are made
    and saved in depo (if that is not already present in the depo),
    and a new span with indexes (of docs and embeddings) is created.
    """
    conf = get_conf(ENV_CONF_PATH)
    if conf is None:
        log_error("cannot get configuration")
        return False
    current_dt = dt.datetime.now(dt.UTC)
    debugging = conf["debugging"]["feed_ingest"]

    if ingest_form == COMMAND_SPAN_INGEST_FULL:
        date_span_save = conf["data"]["depo_depth"]
    elif ingest_form == COMMAND_SPAN_INGEST_INCR:
        date_span_save = conf["data"]["depo_renew"]
    elif ingest_form in COMMAND_SPAN_INGEST_DAYS:
        date_span_save = int(ingest_form)
    else:
        return False

    date_span_turn = conf["data"]["depo_depth"]
    date_span_load = conf["data"]["depo_depth"]

    if (
        (type(date_span_save) is not int)
        or (type(date_span_turn) is not int)
        or (type(date_span_load) is not int)
        or (date_span_save <= 0)
        or (date_span_turn <= 0)
        or (date_span_load <= 0)
    ):
        log_error("date spans have to be positive integers")
        return False

    if not _save_span(
        conf,
        date_from=(current_dt - dt.timedelta(days=date_span_save)),
        date_upto=current_dt,
        debugging=debugging,
    ):
        log_error("saving a span failed")
        return False

    turn_start_time = time.time()
    turn_pause_time = (
        API_FEED_TAKE_PAUSE * len(conf["feeds"]["subjects"]["list"])
    )
    if not _turn_span(
        conf,
        date_from=(current_dt - dt.timedelta(days=date_span_turn)),
        date_upto=current_dt,
    ):
        log_error("turning a span failed")
        if debugging:
            _write_passage_time_info(
                turn_start_time, turn_pause_time, "embedding"
            )
        return False
    if debugging:
        _write_passage_time_info(
            turn_start_time, turn_pause_time, "embedding"
        )

    load_start_time = time.time()
    load_pause_time = (
        2 * API_FEED_TAKE_PAUSE * len(conf["feeds"]["subjects"]["list"])
    )
    if not _load_span(
        conf,
        current_dt,
        date_from=(current_dt - dt.timedelta(days=date_span_load)),
        date_upto=current_dt,
    ):
        log_error("loading a span failed")
        if debugging:
            _write_passage_time_info(
                load_start_time, load_pause_time, "indexing"
            )
        return False
    if debugging:
        _write_passage_time_info(
            load_start_time, load_pause_time, "indexing"
        )

    return True
