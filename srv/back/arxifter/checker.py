#!/usr/bin/env python
"""
Trying to make sure that the query does not contain attacking parts.
"""

import re
import unicodedata

from .setting import MIN_QUERY_LEN

MESSAGE_LACKING_TEXT = "query is effectively empty"
MESSAGE_DISALLOWED_CHARS = "unrecognized characters within the query"
MESSAGE_DISALLOWED_TEXT = "disallowed expressions within the query"

LETTERS_EXTEND = "αβγδεζηθικλμνξοπρσςτυφχψωäöüɫ€£¥—" + "\n\r\t"
LETTERS_SIMPLE = "abgdezetiklmnxoprsstufxpoaoulely-" + (" " * 3)
EXTEND_TO_SIMPLE = str.maketrans(LETTERS_EXTEND, LETTERS_SIMPLE)

PI_PATTERNS_FIXED = re.compile("(" + ")|(".join([
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[/?inst\]",
    r"sys\.prompt",
    r"assistant:",
    r"user:",
    r"\[system\]",
    r"\[context\]",
    r"\[document\]",
    r"\[end\]",
    r"base64",
]) + ")")

LETTERS_EMPTY = re.compile(r"[^a-zA-Z0-9]+")

EXTENDED_MAPPING = {
    "a": "[a4]",
    "e": "[e3]",
    "i": "[i1l]",
    "l": "[l1i]",
    "o": "[o0]",
    "s": "[s5]",
    "t": "[t7]",
    "y": "[yu]",
}

PI_PATTERNS_VERBS = re.compile("|".join([
    "(" + "".join([
        "(" + EXTENDED_MAPPING.get(char, char) + "+)"
        for char in word
    ]) + ")"
    for word in [
        "ignore",
        "disregard",
        "forget",
        "forgot",
        "override",
        "reset",
        "clear",
        "delete",
        "update",
        "change",
        "modify",
        "modified",
        "stop",
        "execute",
    ]
]))

PI_PATTERNS_NOUNS = re.compile("|".join([
    "(" + "".join([
        "(" + EXTENDED_MAPPING.get(char, char) + "+)"
        for char in word
    ]) + ")"
    for word in [
        "systemprompt",
        "instruction",
        "guideline",
        "persona",
        "developersetting",
        "rule",
        "constraint",
    ]
]))

ALLOWED_CHAR_PATTERN = re.compile(r"^([\u0020-\u007e]*)$")

DASHES_SIMPLIFYING = str.maketrans("—", "-")
DASHED_PARTS = re.compile(r"(-{3,})|((^|\n|\r)(-{2,})(\n|\r|$))")


def _is_empty(query):
    if len([
        char for char in query
        if char.isalpha() and char.isascii()
    ]) < MIN_QUERY_LEN:
        return True
    return False


def _contains_disallowed(query):
    query_simplified = (
        unicodedata.normalize("NFKC", query)
        .lower().translate(EXTEND_TO_SIMPLE)
    )
    if ALLOWED_CHAR_PATTERN.match(query_simplified) is None:
        return [True, MESSAGE_DISALLOWED_CHARS]

    if PI_PATTERNS_FIXED.search(query_simplified) is not None:
        return [True, MESSAGE_DISALLOWED_TEXT]

    query_simplified = LETTERS_EMPTY.sub("", query_simplified)

    if (
        (PI_PATTERNS_VERBS.search(query_simplified) is not None)
        and (PI_PATTERNS_NOUNS.search(query_simplified) is not None)
    ):
        return [True, MESSAGE_DISALLOWED_TEXT]

    return [False, ""]


def _turn_dashdotted(matchobj):
    line_start = "\n" if matchobj.group(0).startswith("\n") else ""
    line_middle = ".".join(char for char in matchobj.group(0).strip())
    line_end = "\n" if matchobj.group(0).endswith("\n") else ""
    return line_start + line_middle + line_end


def check_query(query):
    """
    Checks the query to contain text and to not contain prompt injection.
    """
    if _is_empty(query):
        return False, MESSAGE_LACKING_TEXT

    check_status, check_message = _contains_disallowed(query)
    if check_status:
        return False, check_message

    return True, ""


def adjust_query(query):
    """
    Altering the query parts that could confuse the used LLM otherwise.
    """
    return DASHED_PARTS.sub(
        _turn_dashdotted,
        query.translate(DASHES_SIMPLIFYING),
    )
