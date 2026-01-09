#!/usr/bin/env python
"""
Testing the feed handling.
"""

from pathlib import Path

from .setting import (
    RSS_FEED_FILE_NAME,
    ENV_CONF_PATH,
)
from .logging import (
    log_debug,
    log_error,
)
from .config import get_conf
from .parser import parse_feed_save_docs


def test_feed_parsing():
    """
    Tests how well the feed parser works.
    """
    try:
        got_error = False
        conf = get_conf(ENV_CONF_PATH)
        if conf is None:
            log_error("cannot get configuration")
            return False
        test_dir = Path(
            conf["data"]["storage_dir"]["path"],
            "test",
        )
        if not test_dir.is_dir():
            raise OSError("data test dir does not exist")
        for item in test_dir.glob("*"):
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
