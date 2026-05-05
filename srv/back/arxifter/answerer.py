#!/usr/bin/env python
"""
Attempts to parse LLM answers on user queries.
"""

import json

from json_repair import repair_json

from .setting import (
    JSON_START_REMOVALS,
    JSON_END_REMOVALS,
    JSON_FLANK_START,
    JSON_FLANK_END,
)


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
