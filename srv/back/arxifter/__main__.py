#!/usr/bin/env python
#
# arxifter: sifting through open archives
# Copyright (c) 2025 Martin Saturka
# Released under the MIT license.
#
"""
Module for calling auxiliary tools:
* for getting the name of environmental variable with configuration path
* for testing the configuration
* for taking and indexing feeds
* for pruning the past indexed feeds
"""

import sys

from .setting import (
    COMMAND_CONFIG,
    COMMAND_FEEDS,
    COMMAND_CONFIG_ENV,
    COMMAND_CONFIG_TEST,
    COMMAND_FEEDS_INGEST,
    COMMAND_FEEDS_PRUNE,
    ENV_CONF_PATH,
)
from .logging import (
    log_message,
    log_info,
    log_error,
)


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
    log_info("starting feed pruning")
    try:
        from .pruner import prune_feeds
        res = prune_feeds()
    except Exception as exc:
        log_error(str(exc))
        res = False
    log_info("ending feed pruning")
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
    ]))


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        log_error("no command provided")
        do_help()
        sys.exit(1)

    if (sys.argv[1] not in [COMMAND_CONFIG, COMMAND_FEEDS]):
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

    log_error("wrong parameters")
    do_help()
    sys.exit(1)
