#!/usr/bin/env python
"""
Logging functions for situations when different actions
can ask for different levels of logging.
"""

import sys, time, inspect
from pathlib import Path
import unicodedata

from .setting import REPLACEMENT_CHAR


def _get_caller_module(rank):
    try:
        mod_name = Path(str(inspect.getmodule(
            inspect.stack()[rank][0]
        ).__file__)).stem
    except Exception:
        mod_name = None
    return mod_name


def log_message(
    message,
    message_type=None,
    caller_module=None,
    add_datetime=False,
):
    """
    Logs generally a message.
    """
    start = (
        time.strftime("[%Y-%m-%d %H:%M:%S] ", time.gmtime())
        if add_datetime else ""
    )
    if message_type is not None:
        start = start + "[" + str(message_type) + "] "
    if caller_module is not None:
        start = start + "in " + caller_module + ": "

    message = start + str(message)
    message = "".join([
        (
            c if (
                c in ["\r", "\n", "\t"]
                or (unicodedata.category(c)[0] != "C")
            )
            else REPLACEMENT_CHAR
        )
        for c in message
    ])

    sys.stderr.write(message + ("" if message.endswith("\n") else "\n"))
    sys.stderr.flush()


def log_debug(message):
    """
    Logs message corresponding to debugging level.
    """
    log_message(
        message,
        message_type="DEBUG",
        caller_module=_get_caller_module(2),
        add_datetime=True,
    )


def log_info(message):
    """
    Logs message corresponding to info level.
    """
    log_message(
        message,
        message_type="INFO",
        caller_module=_get_caller_module(2),
        add_datetime=True,
    )


def log_error(message):
    """
    Logs message corresponding to error level.
    """
    if len(str(message)) == 0:
        message = "an error occurred"
    log_message(
        message,
        message_type="ERROR",
        caller_module=_get_caller_module(2),
        add_datetime=True,
    )
