#!/usr/bin/env python
"""
Attempts to parse LLM answers on user queries.
"""

import json

from json_repair import repair_json

from .setting import (
    JSON_START_REMOVALS,
    JSON_END_REMOVALS,
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
