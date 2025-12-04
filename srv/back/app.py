#!/usr/bin/env python

import os, pathlib

from flask import Flask, Response, send_file, request, jsonify

from arxifter.subjects import get_subjects_js
from arxifter.asking import answer_query_inner

CURR_DIR = pathlib.Path(__file__).parent.resolve()
BASE_DIR = os.path.join(CURR_DIR, "..")
WEB_DIR = os.path.join(BASE_DIR, "webs")
STATIC_DIR = os.path.join(WEB_DIR, "static")
WEBPAGE_PATH = os.path.join(WEB_DIR, "page.html")
BASE_DATA_DIR = os.path.join(BASE_DIR, "data")
BASE_KEYS_DIR = os.path.join(BASE_DIR, "keys")
BASE_MOCK_DIR = os.path.join(BASE_DIR, "mock")
LLM_MOCKING = False


app = Flask(__name__, static_folder = STATIC_DIR)


@app.route("/", methods=["GET"])
def main_page():
    return send_file(WEBPAGE_PATH)


@app.route("/list/subjects/js/<func_name>", methods=["GET"])
def get_subjects_for_js(func_name):
    return Response(get_subjects_js(func_name), mimetype="text/javascript")


@app.route("/query/<subject_id>", methods=["POST"])
def answer_query(subject_id):
    if request.method != "POST":
        return jsonify(
            statusCode=405,
            message="Method Not Allowed")

    paths = {
        "dir_keys": BASE_KEYS_DIR,
        "dir_data": BASE_DATA_DIR,
        "dir_mock": BASE_MOCK_DIR,
    }
    res = answer_query_inner(request, subject_id, paths, LLM_MOCKING)

    return jsonify(
        isError=(not res["ok"]),
        statusCode=(200 if res["ok"] else 409),
        message=res["message"],
        answer=(res["answer"] if res["ok"] else [res["message"]])
    )
