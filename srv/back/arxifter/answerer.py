#!/usr/bin/env python
"""
Attempts to parse LLM answers on user queries.
"""

import json

from json_repair import repair_json


def _simple_repairing(answer):
    # the met broken answers had single-instead-of-double quotes
    return answer.replace("'", '"')


def _thorough_repairing(answer):
    # thorough repairing with the use of the json_repair package
    repaired_json = repair_json(answer, skip_json_loads=True)
    if repaired_json == "":
        raise OSError("too broken JSON even for json_repair")

    return repaired_json


def parse_llm_answer(logger, answer):
    """
    Tries to parse the LLM answer:
    * as it is,
    * with minor tweaks,
    * with large repairing
    """
    parsed_answer = None
    err_msgs = []

    repair_methods = [
        [
            lambda answer: answer,
            None,
        ],
        [
            _simple_repairing,
            "LLM answer had some single quotes instead of double quotes",
        ],
        [
            _thorough_repairing,
            "LLM answer was a more broken JSON (repaired by json_repair)",
        ],
    ]

    for method, message in repair_methods:
        if parsed_answer is not None:
            break
        try:
            parsed_answer = json.loads(
                method(str(answer))
            )
            if message is not None:
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
