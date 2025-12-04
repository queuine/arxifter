#!/usr/bin/env python

import os, sys, json
from pathlib import Path

from .subjects import get_subjects
from .setting import LLM_DEBUGGING, VECTORS_SUBDIR, set_llm_key
from .loader import load_index
from .querier import make_query


def answer_query_mocked(subject, mock_dir):
    if not subject.startswith("a"):
        return {
            "ok": False,
            "message": "unknown subject",
        }

    err_message = ""
    mock_llm_answer = ""
    got_mock_answer = False
    try:
        mock_llm_answer = Path(
            os.path.join(mock_dir, "answer.json")
        ).read_text(encoding="utf8").strip()
        got_mock_answer = True
    except Exception as exc:
        mocked_answer = ""
        err_message = str(exc)
        got_mock_answer = False

    if not got_mock_answer:
        return {
            "ok": False,
            "message": err_message,
        }

    try:
        mocked_answer = json.loads(str(mock_llm_answer))
    except Exception:
        mocked_answer = mock_llm_answer

    return {
        "ok": True,
        "message": "Success",
        "answer": mocked_answer,
    }


def answer_query_inner(request, subject, paths, mock):
    if mock:
        return answer_query_mocked(subject, paths["dir_mock"])

    if subject not in get_subjects():
        return {
            "ok": False,
            "message": "unknown subject",
        }

    query_text = None
    got_query = False
    err_message = ""
    try:
        data = request.get_json()
        query_text = str(data["query"])
        got_query = True
    except Exception as exc:
        err_message = str(exc)
        got_query = False

    if not got_query:
        return {
            "ok": False,
            "message": err_message,
        }

    llm_answer = None
    got_answer = False

    try:
        set_llm_key(paths["dir_keys"])
        vecs_dir = os.path.join(paths["dir_data"], subject, VECTORS_SUBDIR)
        llm_index = load_index(vecs_dir)
        llm_answer = make_query(llm_index, query_text)
        got_answer = True
        if LLM_DEBUGGING:
            print("llm_answer:", file=sys.stderr)
            print(llm_answer, file=sys.stderr)
    except Exception as exc:
        err_message = ["an error occurred", str(exc)]
        got_answer = False

    if not got_answer:
        return {
            "ok": False,
            "message": err_message,
        }

    parsed_answer = None
    has_parsed = False
    try:
        parsed_answer = json.loads(str(llm_answer))
        has_parsed = True
    except Exception:
        parsed_answer = llm_answer
        has_parsed = False

    return {
        "ok": has_parsed,
        "message": "Success" if has_parsed else err_message,
        "answer": parsed_answer if has_parsed else None,
    }
