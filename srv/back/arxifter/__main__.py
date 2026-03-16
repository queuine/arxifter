#!/usr/bin/env python
#
# arxifter: sifting through open archives
# Copyright (c) 2025-2026 Martin Saturka
# Released under the MIT license.
#
"""
Module for calling auxiliary tools:
* for getting the name of environmental variable with configuration path
* for testing the configuration
* for taking and indexing feeds
* for pruning the past indexed feeds
* for testing the feed parsing/indexing
"""

import sys, time

from setproctitle import setproctitle

from .setting import (
    COMMAND_CONFIG,
    COMMAND_FEEDS,
    COMMAND_CONFIG_ENV,
    COMMAND_CONFIG_TEST,
    COMMAND_FEEDS_INGEST,
    COMMAND_FEEDS_PRUNE,
    COMMAND_SPAN,
    COMMAND_SPAN_INGEST_INCR,
    COMMAND_SPAN_INGEST_FULL,
    COMMAND_TESTS,
    COMMAND_TESTS_FEED_PARSING,
    COMMAND_TESTS_FEED_INDEXING,
    ENV_CONF_PATH,
    APP_NAME_FEED_INGEST,
    APP_NAME_FEED_PRUNING,
    APP_NAME_SPAN_INGEST,
)
from .logging import (
    log_message,
    log_info,
    log_error,
)
from .utils import mute_hf


def do_config_env():
    """
    Provides the env. variable for path to configuration file.
    """
    try:
        sys.stdout.write(ENV_CONF_PATH)
        res = True
    except Exception as exc:
        log_error(str(exc))
        res = False
    return res


def do_config_test():
    """
    Checks configuration via taking it.
    """
    try:
        from .config import get_conf
        conf = get_conf(ENV_CONF_PATH)
        if conf is None:
            log_error("taking the configuration failed")
        res = conf is not None
    except Exception as exc:
        log_error(str(exc))
        res = False
    return res


def do_feeds_ingest():
    """
    Ingests RSS feeds: via downloading, indexing and saving them.
    """
    setproctitle(APP_NAME_FEED_INGEST)
    log_info("starting feed ingest")
    try:
        from .feeder import ingest_feeds
        res = ingest_feeds()
    except Exception as exc:
        log_error(str(exc))
        res = False
    log_info("ending feed ingest")
    return res


def do_feeds_prune():
    """
    Prunes individual batches of the previously ingested feeds.
    """
    setproctitle(APP_NAME_FEED_PRUNING)
    log_info("starting feed pruning")
    try:
        from .pruner import prune_feeds
        res = prune_feeds()
    except Exception as exc:
        log_error(str(exc))
        res = False
    log_info("ending feed pruning")
    return res


def do_span_ingest(full):
    """
    Ingests JSON API feeds: via downloading, indexing and saving them.
    """
    setproctitle(APP_NAME_SPAN_INGEST)
    log_info("starting span ingest")
    try:
        from .spans.ingester import ingest_span
        res = ingest_span(full)
    except Exception as exc:
        log_error(str(exc))
        res = False
    log_info("ending span ingest")
    return res


def do_test_feed_parsing():
    """
    Tests the feed-parsing process
    """
    time_start = time.time()
    try:
        from .tests import test_feed_parsing
        res = test_feed_parsing()
    except Exception as exc:
        log_error(str(exc))
        res = False
    log_message(f"parsing took {time.time() - time_start}s")
    return res


def do_test_feed_index():
    """
    Tests the feed-indexing process
    """
    time_start = time.time()
    try:
        from .tests import test_feed_index
        res = test_feed_index()
    except Exception as exc:
        log_error(str(exc))
        res = False
    log_message(f"indexing took {time.time() - time_start}s")
    return res


def do_help():
    """
    Writes how to use these arxifter tools.
    """
    log_message("\n".join([
        "use it as either of:",
        f"python -m arxifter {COMMAND_CONFIG} {COMMAND_CONFIG_ENV}",
        "    for providing name of env. variable that is to be set",
        "    to the path where the configuration file is located",
        f"python -m arxifter {COMMAND_CONFIG} {COMMAND_CONFIG_TEST}",
        "    for testing the configuration (no output means it is correct)",
        "    it needs to have the configuration env. variable set",
        f"python -m arxifter {COMMAND_FEEDS} {COMMAND_FEEDS_INGEST}",
        "    for taking and indexing feeds (it is meant to be run by cron)",
        "    it needs to have the configuration env. variable set",
        f"python -m arxifter {COMMAND_FEEDS} {COMMAND_FEEDS_PRUNE}",
        "    for pruning the past feeds (it is meant to be run by cron)",
        "    it needs to have the configuration env. variable set",
        f"python -m arxifter {COMMAND_SPAN} "
        f"{COMMAND_SPAN_INGEST_INCR}|{COMMAND_SPAN_INGEST_FULL}",
        "    for ingesting biorxiv data (it is meant to be run by cron)",
        "    it needs to have the configuration env. variable set",
        f"python -m arxifter {COMMAND_TESTS} {COMMAND_TESTS_FEED_PARSING}",
        "    for testing the feed-parsing process (used during development)",
        "    it needs to have the configuration env. variable set",
        f"python -m arxifter {COMMAND_TESTS} {COMMAND_TESTS_FEED_INDEXING}",
        "    for testing the feed-indexing process (used during development)",
        "    it needs to have the configuration env. variable set",
    ]))


if __name__ == "__main__":
    mute_hf()

    if len(sys.argv) <= 1:
        log_error("no command provided")
        do_help()
        sys.exit(1)

    if (sys.argv[1] not in [
        COMMAND_CONFIG,
        COMMAND_FEEDS,
        COMMAND_TESTS,
        COMMAND_SPAN,
    ]):
        log_error("unknown command")
        do_help()
        sys.exit(1)

    if len(sys.argv) == 3:
        if sys.argv[1] == COMMAND_CONFIG:
            if sys.argv[2] == COMMAND_CONFIG_ENV:
                sys.exit(0 if do_config_env() else 2)
            elif sys.argv[2] == COMMAND_CONFIG_TEST:
                sys.exit(0 if do_config_test() else 2)
        elif sys.argv[1] == COMMAND_FEEDS:
            if sys.argv[2] == COMMAND_FEEDS_INGEST:
                sys.exit(0 if do_feeds_ingest() else 2)
            elif sys.argv[2] == COMMAND_FEEDS_PRUNE:
                sys.exit(0 if do_feeds_prune() else 2)
        elif sys.argv[1] == COMMAND_SPAN:
            if sys.argv[2] == COMMAND_SPAN_INGEST_INCR:
                sys.exit(0 if do_span_ingest(full=False) else 2)
            if sys.argv[2] == COMMAND_SPAN_INGEST_FULL:
                sys.exit(0 if do_span_ingest(full=True) else 2)
        elif sys.argv[1] == COMMAND_TESTS:
            if sys.argv[2] == COMMAND_TESTS_FEED_PARSING:
                sys.exit(0 if do_test_feed_parsing() else 2)
            if sys.argv[2] == COMMAND_TESTS_FEED_INDEXING:
                sys.exit(0 if do_test_feed_index() else 2)

    log_error("wrong parameters")
    do_help()
    sys.exit(1)
