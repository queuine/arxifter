#!/usr/bin/env python
"""
Dealing with mocked versions of LLM answers.
Used for developing/debugging purposes.
"""

import os
from pathlib import Path

from .setting import (
    MOCK_SUBJECTS_ANSWER,
    MOCK_SUBJECTS_SUGGESTED,
    MOCK_ANSWER_PLAIN,
    MOCK_ANSWER_EXPLAINED,
    MOCK_SUGGESTED_PLAIN,
    MOCK_SUGGESTED_EXPLAINED,
)


def get_mocked_answer(conf, subject, to_explain):
    """
    Provides several forms of mocked LLM answers.
    """
    mock_file_name = None

    for prefix in MOCK_SUBJECTS_ANSWER:
        if subject.startswith(prefix):
            mock_file_name = (
                MOCK_ANSWER_EXPLAINED if to_explain
                else MOCK_ANSWER_PLAIN
            )
            break

    for prefix in MOCK_SUBJECTS_SUGGESTED:
        if subject.startswith(prefix):
            mock_file_name = (
                MOCK_SUGGESTED_EXPLAINED if to_explain
                else MOCK_SUGGESTED_PLAIN
            )
            break

    if mock_file_name is None:
        raise OSError("unknown subject")

    return Path(
        os.path.join(
            conf["mocking"]["answers_dir"]["path"],
            mock_file_name,
        )
    ).read_text(encoding="utf8").strip()
