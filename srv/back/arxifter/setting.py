#!/usr/bin/env python
"""
Various inner settings for the arxifter.
These settings are not expected to be changed.
Those settings that are meant to be set by administrators
of arxifter deployments are in a TOML file
that is read at the "config" module.
"""

import re

APP_NAME = "arxifter"
APP_MAX_CONTENT_LENGTH = 1024 * 1024
APP_RESPONSE_TIMEOUT = 120

COMMAND_CONFIG = "conf"
COMMAND_CONFIG_ENV = "env"
COMMAND_CONFIG_TEST = "test"
COMMAND_FEEDS = "feeds"
COMMAND_FEEDS_INGEST = "ingest"
COMMAND_FEEDS_PRUNE = "prune"

TRUTH_VALUES_STR = ["1", "y", "yes", "t", "true", "truth", "on", "ok"]
FALSE_VALUES_STR = ["0", "n", "no", "f", "false", "untrue", "off", "ko"]

ARTICLE_KEY_RANK = "artnum"
ARTICLE_KEY_RANK_VAR = ["art", "num"]
LLM_MATCHES_KEYS = ["match"]
LLM_SUGGESTION_KEY = "instead"

DATA_DIR_PERM = "perm"
DATA_DIR_CURR = "curr"
DOCUMENTS_SUBDIR = "docs"
DOCUMENTS_FOR_VECTORS_SUBDIR = "docs4vecs"
VECTORS_SUBDIR = "vecs"

MIN_QUERY_LEN = 3
MAX_QUERY_LEN = 1000

ACTIVE_DATA_DIR_MAKING = "%Y_%m%d_%H%M"
ACTIVE_DATA_DIR_LISTING = re.compile('^[\\d]{4}_[\\d]{4}_[\\d]{4}$')
ATTEMPT_COUNT_DATA_DIR = 3

ENV_CONF_PATH = "ARXIFTER_CONFIG_PATH"
JS_FABRIC_PREFIX = "get_fabric_"

INFO_FILE_NAME = "info.json"
EMBED_MODEL_NAME_KEY = "embed_model_name"

GUEST_ID_LENGTH = 32
HEXDIGITS = "0123456789abcdef"
HEXDIGITS_REV = "".join(reversed(list(HEXDIGITS)))
GUEST_IDS_LIST_SIZE = 1
GUEST_FILENAME_MAKING = "%Y_%m_%d_%H"
GUEST_FILENAME_LISTING = re.compile(
    '^([\\d]{4})_([\\d]{2})_([\\d]{2})_([\\d]{2})$'
)

INDENT_SIZE = 4
SESSION_CLUE_LEN_BASE = len(HEXDIGITS)
NEW_DIRS_MODE = 0o755

ATTEMPT_COUNT_INDEX = 3
VEC_FEED_INDEX_SLEEP = 120

ATTEMPT_COUNT_FEED = 6
RSS_FEED_TAKE_SLEEP = 15
RSS_FEED_URL_BASE = "https://connect.biorxiv.org/biorxiv_xml.php?subject="
RSS_FEED_FILE_NAME = "feed.rss"

BIORXIV_FEED_SIZE = 30
BIORXIV_DOI_START = "10.64898"
BIORXIV_DOI_ENDS = ["v", "?"]

VIEW_WARNING_KEY = "warning"
VIEW_WARNING_ANSWER_WRONG = "an unrecognizable answer from LLM"

MOCK_SUBJECTS_ANSWER = ["all", "bio"]
MOCK_SUBJECTS_SUGGESTED = ["ani"]
MOCK_ANSWER_PLAIN = "answer_plain.json"
MOCK_ANSWER_EXPLAINED = "answer_explained.json"
MOCK_SUGGESTED_PLAIN = "suggested_plain.json"
MOCK_SUGGESTED_EXPLAINED = "suggested_explained.json"
