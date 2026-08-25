#!/usr/bin/env python
"""
Attempts to parse LLM answers on user queries.
"""

import re, json

from json_repair import repair_json

from .setting import (
    JSON_START_REMOVALS,
    JSON_END_REMOVALS,
    JSON_FLANK_START,
    JSON_FLANK_END,
    ARTICLE_VALUE_REASON_ENDING,
)

ANSWER_ARTICLE_KEY_ARTNUM = "artnum"
ANSWER_ARTICLE_KEY_TITLE_PREFIX = "title_prefix"
ANSWER_ARTICLE_KEY_REASON = "reason"
ANSWER_ARTICLE_KEY_MATCHES = "matches"
ANSWER_ARTICLE_KEYS = [
    ANSWER_ARTICLE_KEY_ARTNUM,
    ANSWER_ARTICLE_KEY_TITLE_PREFIX,
    ANSWER_ARTICLE_KEY_REASON,
    ANSWER_ARTICLE_KEY_MATCHES,
]
ANSWER_LINE_EMPTY = re.compile("".join([
    r"^",
    r"([^\w\d]*)",
    r"$",
]), re.I | re.U)
ANSWER_LINE_FIELD = re.compile("".join([
    r"^",
    r"(?:[_\W]*)",
    r"(",
    r"|".join([
        r"(?:" + line_key + r"(?:[\w]*))"
        for line_key in ANSWER_ARTICLE_KEYS
    ]),
    r")",
    r"(?:[\W]*)",
    r":",
    r"(?:[^\w\d]*)",
    r"((?:[\w\d])(?:.*))",
    r"$",
]), re.I | re.U)
ANSWER_LINE_KEY = re.compile("".join([
    r"^",
    r"|".join([
        line_key for line_key in ANSWER_ARTICLE_KEYS
    ]),
]), re.I | re.U)
ANSWER_LINE_VALUE_NUMBER = re.compile("".join([
    r"^([\d]+)(?:[^\d]*)$",
]), re.I | re.U)
ANSWER_LINE_VALUE_TRUE = "true"
ANSWER_LINE_VALUE_FALSE = "false"
ANSWER_LINE_VALUE_BOOLEAN = re.compile("".join([
    r"^(",
    ANSWER_LINE_VALUE_TRUE,
    r"|",
    ANSWER_LINE_VALUE_FALSE,
    r")(?:.*)$",
]), re.I | re.U)
ANSWER_LINE_VALUE_TEXT = re.compile("".join([
    r"^(.+)(?:[^\d\w]*)$",
]), re.I | re.U)
ANSWER_LINE_VALUE_ENDING = re.compile("".join([
    r"(?:[^\d\w]*)$",
]), re.I | re.U)


def _simple_repairing(answer):
    answer = answer.strip()

    # some LLMs flank their answers as: ```json...```
    for part in JSON_START_REMOVALS:
        if answer.startswith(part):
            answer = answer[len(part):]
    for part in JSON_END_REMOVALS:
        if answer.endswith(part):
            answer = answer[:-len(part)]
    answer = answer.strip()

    # some met broken answers had single-instead-of-double quotes
    return answer.replace("'\n", '"\n').replace("',\n", '",\n')


def _last_json_in_text(answer):
    # some provider/LLMs services return the answer along with reasoning;
    # it is not clear whether the inference providers fail in separating
    # the reasoning from the actual output, or whether those LLMs fail it,
    # but the actual output lacks any separating tokens then;
    # when the eventual json is at least flanked by ```json and ```,
    # it is possible to take it as the last occurrence of it;
    last_start = answer.rfind(JSON_FLANK_START)
    if last_start < 0:
        return None
    answer = answer[last_start+len(JSON_FLANK_START):]
    last_end = answer.rfind(JSON_FLANK_END)
    if last_end < 0:
        return None
    answer = answer[:last_end]
    if not answer.strip():
        return None
    return _simple_repairing(answer)


def _thorough_repairing(answer):
    answer = _simple_repairing(answer)

    # thorough repairing with the use of the json_repair package
    repaired_json = repair_json(answer, skip_json_loads=True)
    if repaired_json == "":
        raise OSError("too broken JSON even for json_repair")

    return repaired_json


def _last_data_in_text(answer):
    # some provider/LLMs services return the single nonmatching
    # article without its data put into JSON list/structure;
    article = {
        art_key: None
        for art_key in ANSWER_ARTICLE_KEYS
    }

    for line in reversed(answer.splitlines()):
        all_filled = True
        for art_key, art_val in article.items():
            if art_val is None:
                all_filled = False
                break
        if all_filled:
            break

        if ANSWER_LINE_EMPTY.match(line):
            continue
        line_field = ANSWER_LINE_FIELD.match(line)
        if line_field is None:
            break
        if len(line_field.groups()) != 2:
            # this should not occur
            continue
        line_key = ANSWER_LINE_KEY.search(line_field.group(1))
        if line_key is None:
            # this should not occur
            continue
        line_key = line_key.group(0).lower()

        if line_key == ANSWER_ARTICLE_KEY_ARTNUM:
            line_value = ANSWER_LINE_VALUE_NUMBER.match(line_field.group(2))
            if line_value is None:
                continue
            if len(line_value.groups()) != 1:
                # this should not occur
                continue
            try:
                article[line_key] = int(line_value.group(1))
            except Exception:
                # this should not occur
                pass
            continue

        if line_key == ANSWER_ARTICLE_KEY_MATCHES:
            line_value = ANSWER_LINE_VALUE_BOOLEAN.match(line_field.group(2))
            if line_value is None:
                continue
            if len(line_value.groups()) != 1:
                # this should not occur
                continue
            item_value = line_value.group(1).lower()
            if item_value == ANSWER_LINE_VALUE_TRUE:
                article[line_key] = True
            elif item_value == ANSWER_LINE_VALUE_FALSE:
                article[line_key] = False
            else:
                # this should not occur
                pass
            continue

        line_value = ANSWER_LINE_VALUE_TEXT.match(line_field.group(2))
        if line_value is None:
            continue
        if len(line_value.groups()) != 1:
            # this should not occur
            continue
        item_value = line_value.group(1)
        item_end = ""
        if line_key == ANSWER_ARTICLE_KEY_REASON:
            line_ending = ANSWER_LINE_VALUE_ENDING.search(item_value)
            if line_ending is not None:
                item_value = item_value[:line_ending.start()]
            if not item_value:
                continue
            if not item_value.endswith(ARTICLE_VALUE_REASON_ENDING):
                item_end = ARTICLE_VALUE_REASON_ENDING
        article[line_key] = item_value + item_end

    if (
        (article[ANSWER_ARTICLE_KEY_ARTNUM] is None)
        and (article[ANSWER_ARTICLE_KEY_TITLE_PREFIX] is None)
    ):
        return None

    for art_key in ANSWER_ARTICLE_KEYS:
        if article[art_key] is None:
            del article[art_key]

    return json.dumps([article])


def parse_llm_answer(conf, get_logger, answer):
    """
    Tries to parse the LLM answer:
    * as it is,
    * with minor tweaks,
    * with large repairing
    """
    logger = get_logger(__name__)
    parsed_answer = None
    err_msgs = []

    repair_methods = [
        [
            lambda answer: answer,
            None,
            False,
        ],
        [
            _simple_repairing,
            "LLM answer had minor issues (fixed automatically)",
            False,
        ],
        [
            _last_json_in_text,
            "LLM answer was apparently returned mixed with reasoning",
            False,
        ],
        [
            _thorough_repairing,
            "LLM answer was a more broken JSON (repaired by json_repair)",
            False,
        ],
        [
            _last_data_in_text,
            "some data salvaged from the answer lacking JSON format",
            True,
        ],
    ]

    for method, message, spout in repair_methods:
        if parsed_answer is not None:
            break
        try:
            parsed_answer = json.loads(
                method(str(answer))
            )
            if (
                (message is not None)
                and (
                    spout or conf["debugging"]["query_sifting"]
                )
            ):
                logger.warning(message)
        except Exception as exc:
            parsed_answer = None
            err_msgs.append(str(exc))

    if parsed_answer is None:
        logger.error(
            "LLM answer was a generally invalid and too broken JSON"
        )
        raise OSError("\n".join(err_msgs))

    return parsed_answer
