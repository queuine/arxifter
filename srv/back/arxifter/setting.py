#!/usr/bin/env python
"""
Various inner settings for the arxifter.
These settings are not expected to be changed.
Those settings that are meant to be set by administrators
of arxifter deployments are in a TOML file
that is read at the "config" module.
"""

import re
import unicodedata as ud

# general use
ENV_CONF_PATH = "ARXIFTER_CONFIG_PATH"
NEW_DIRS_MODE = 0o755

# web server
APP_NAME = "arxifter"
APP_MAX_CONTENT_LENGTH = 1024 * 1024
APP_RESPONSE_TIMEOUT = 120

# command line interface
COMMAND_CONFIG = "conf"
COMMAND_CONFIG_ENV = "env"
COMMAND_CONFIG_TEST = "test"
COMMAND_FEEDS = "feeds"
COMMAND_FEEDS_INGEST = "ingest"
COMMAND_FEEDS_PRUNE = "prune"
COMMAND_TESTS = "test"
COMMAND_TESTS_FEED_PARSING = "feed-parsing"

# general use
TRUTH_VALUES_STR = ["1", "y", "yes", "t", "true", "truth", "on", "ok"]
FALSE_VALUES_STR = ["0", "n", "no", "f", "false", "untrue", "off", "ko"]
REPLACEMENT_CHAR = "□"

# answers from LLM
ARTICLE_KEY_RANK = "artnum"
ARTICLE_KEY_RANK_VAR = ["art", "num"]
# non-matching answers
LLM_MATCHES_KEYS = ["match"]
LLM_SUGGESTION_KEY = "instead"

# data storage
DATA_DIR_PERM = "perm"
DATA_DIR_CURR = "curr"
DOCUMENTS_SUBDIR = "docs"
DOCUMENTS_FOR_VECTORS_SUBDIR = "docs4vecs"
VECTORS_SUBDIR = "vecs"

# questions on LLM
MIN_QUERY_LEN = 3
MAX_QUERY_LEN = 1000

# data storage
ACTIVE_DATA_DIR_MAKING = "%Y_%m%d_%H%M"
ACTIVE_DATA_DIR_LISTING = re.compile('^[\\d]{4}_[\\d]{4}_[\\d]{4}$')
ATTEMPT_COUNT_DATA_DIR = 3

# config, incl. its presentation to frontend
CONFIG_OTHER_LETTERS = [".", "_", "-"]
JS_FABRIC_PREFIX = "get_fabric_"
INDENT_SIZE = 4

# data embedding
INFO_FILE_NAME = "info.json"
EMBED_MODEL_NAME_KEY = "embed_model_name"

# handling guest users
SESSION_EXPIRED_KEY = "expired"
GUEST_ID_LENGTH = 32
HEXDIGITS = "0123456789abcdef"
HEXDIGITS_REV = "".join(reversed(list(HEXDIGITS)))
GUEST_IDS_LIST_SIZE = 1
GUEST_FILENAME_MAKING = "%Y_%m_%d_%H"
GUEST_FILENAME_LISTING = re.compile(
    '^([\\d]{4})_([\\d]{2})_([\\d]{2})_([\\d]{2})$'
)
# communication with frontend
SESSION_CLUE_LEN_BASE = len(HEXDIGITS)

# making the LLM embedding
ATTEMPT_COUNT_INDEX = 3
VEC_FEED_INDEX_SLEEP = 120

# getting the feeds
ATTEMPT_COUNT_FEED = 6
RSS_FEED_TAKE_SLEEP = 15
RSS_FEED_URL_BASE = "https://connect.biorxiv.org/biorxiv_xml.php?subject="
RSS_FEED_FILE_NAME = "feed.rss"

# config for UI and parsing the feeds
MAX_RECALL_SEARCHES_COUNT = 100
BIORXIV_FEED_SIZE = 30
BIORXIV_FEED_MINIMAL_SIZE = 20
BIORXIV_DOI_START = "10.64898"
BIORXIV_DOI_ENDS = ["v", "?"]

# parsing the feeds
# only the lower-case letters, w/o ending-sigma, are included
NAMED_GREEK_LETTERS = {
    ud.name(chr(code)).strip().split(" ")[-1].lower(): chr(code)
    for code in range(0x3b1, 0x3ca) if code != 0x3c2
}
# the unicode-name spelling of λ is lamda;
NAMED_GREEK_LETTERS["lambda"] = "λ"

# parsing the feeds
FEED_REPLS_ENT_SHORT = {
    "~": "∼",
    "A": "Å",
    "1/4": "¼",
    "1/3": "⅓",
    "1/2": "½",
    "2/3": "⅔",
    "3/4": "¾",
}
FEED_MATCH_ENT_SHORT = re.compile("".join([
    r"\[(",
    "|".join(map(re.escape, FEED_REPLS_ENT_SHORT.keys())),
    r")\]",
]))
FEED_REPLS_ENT = {
    "lt": "<",
    "le": "≤",
    "gt": ">",
    "ge": "≥",
    "eq": "=",
    "ne": "≠",
}
FEED_MATCH_ENT = re.compile("".join([
    r"\[(.?)\&(",
    "|".join(map(re.escape, FEED_REPLS_ENT.keys())),
    r");(.?)\]",
]))
FEED_IMPUT_ONOFF = "_"
FEED_MATCH_ONOFF = re.compile(r"\b(k)(on|off)\b")
FEED_IMPUT_SYMS_SUP = "^"
FEED_MATCH_SYMS_SUP = re.compile(
    r"\{superscript(?:\s*)([^\s\{\}]{1,3})\}"
)
FEED_REPLS_SYMS = {
    "infty": "∞",
    "+/-": "±",
    "approx": "≈",
    "degrees": "°",
    "square": "□",
    "checkmark": "✓",
    "middle dot": "·",
    "micro": "μ",
}
for letter_name, letter_symbol in NAMED_GREEK_LETTERS.items():
    FEED_REPLS_SYMS[letter_name] = letter_symbol
    # some of the var-name forms could have differing letters too;
    # it could be for ε/ϵ, θ/ϑ, κ/ϰ, π/ϖ, ρ/ϱ, σ/ς, φ/ϕ pairs;
    FEED_REPLS_SYMS["var" + letter_name] = letter_symbol
    FEED_REPLS_SYMS[letter_name.capitalize()] = letter_symbol.upper()
FEED_MATCH_SYMS = re.compile("".join([
    r"\{(",
    "|".join(map(re.escape, FEED_REPLS_SYMS.keys())),
    r")\}",
]))

# LLM-result presentation to frontend
VIEW_WARNING_KEY = "warning"
VIEW_WARNING_ANSWER_WRONG = "an unrecognizable answer from LLM"

# mocking related
MOCK_SUBJECTS_ANSWER = ["all", "cell", "test"]
MOCK_SUBJECTS_SUGGESTED = ["ani", "bio", "gen"]
MOCK_ANSWER_PLAIN = "answer_plain.json"
MOCK_ANSWER_EXPLAINED = "answer_explained.json"
MOCK_SUGGESTED_PLAIN = "suggested_plain.json"
MOCK_SUGGESTED_EXPLAINED = "suggested_explained.json"
