#!/usr/bin/env python
"""
Testing the feed handling.
"""

from pathlib import Path

from .setting import (
    RSS_FEED_FILE_NAME,
    ENV_CONF_PATH,
    DOCUMENTS_SUBDIR,
    DATA_DIR_TEST,
    DATA_DIR_TEST_CURR,
    DATA_DIR_TEST_PREV,
)
from .logging import (
    log_debug,
    log_info,
    log_error,
)
from .config import get_conf
from .utils import (
    load_encoders_info,
    check_encoders_info,
    save_encoders_info,
)


def test_feed_parsing():
    """
    Tests how well the feed parser works.
    """
    from .parser import parse_feed_save_docs

    try:
        got_error = False
        conf = get_conf(ENV_CONF_PATH)
        if conf is None:
            log_error("cannot get configuration")
            return False
        test_dir = Path(
            conf["data"]["storage_dir"]["path"],
            DATA_DIR_TEST,
            DATA_DIR_TEST_CURR,
        )
        if not test_dir.is_dir():
            raise OSError("data test dir does not exist")
        for item in sorted(test_dir.glob("*")):
            if not item.is_dir():
                continue
            feed_path = item / RSS_FEED_FILE_NAME
            if not feed_path.is_file():
                log_debug("\n".join([
                    "a feed file does not exist:",
                    str(feed_path),
                ]))
                continue
            if not parse_feed_save_docs(str(feed_path)):
                got_error = True
                log_error("\n".join([
                    "cannot parse the feed:",
                    str(feed_path),
                ]))
        return not got_error
    except Exception as exc:
        log_error(str(exc))
    return False


def test_feed_index():
    """
    Tests how well the feed indexing works.
    """
    from .encoder import get_encoders
    from .indexer import index_docs

    try:
        got_error = False
        conf = get_conf(ENV_CONF_PATH)
        if conf is None:
            log_error("cannot get configuration")
            return False
        test_dir_base = Path(
            conf["data"]["storage_dir"]["path"],
            DATA_DIR_TEST,
        )
        test_dir_curr = Path(
            test_dir_base,
            DATA_DIR_TEST_CURR,
        )
        test_dir_prev = str(Path(
            test_dir_base,
            DATA_DIR_TEST_PREV,
        ))
        # needs encoders for the indexing
        encoders = get_encoders(conf)
        if encoders is None:
            log_error("cannot get doc encoders")
            return False
        # possibly can reuse previously indexed docs
        prev_enc_info = load_encoders_info(test_dir_prev)
        if not check_encoders_info(prev_enc_info, encoders):
            log_info("cannot reuse previously made vectors")
            test_dir_prev = None
        # does indexing over individual subjects
        if not test_dir_curr.is_dir():
            raise OSError("data test dir does not exist")
        for item in sorted(test_dir_curr.glob("*")):
            if not item.is_dir():
                continue
            prev_item = (
                Path(test_dir_prev, item.name)
                if test_dir_prev is not None else None
            )
            doc_path = item / DOCUMENTS_SUBDIR
            if not doc_path.is_dir():
                log_debug("\n".join([
                    "a feed doc-dir does not exist:",
                    str(doc_path),
                ]))
                continue
            if not index_docs(
                conf,
                encoders,
                str(item),
                str(prev_item) if prev_item is not None else None,
            ):
                got_error = True
                log_error("\n".join([
                    "cannot index the feed:",
                    str(item),
                ]))
        # saving the info on what encoders were used
        if not save_encoders_info(test_dir_curr, encoders):
            log_error("cannot save the encoders-data info")
            got_error = True

        return not got_error
    except Exception as exc:
        log_error(str(exc))
    return False
