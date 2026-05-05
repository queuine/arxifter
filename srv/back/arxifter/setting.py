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

import numpy as np

# general use
ENV_CONF_PATH = "ARXIFTER_CONFIG_PATH"
NEW_DIRS_MODE = 0o755

# web server
APP_NAME_WEB_IFCE = "arxifter-web-ifce"
APP_MAX_CONTENT_LENGTH = 100 * 1024
APP_RESPONSE_TIMEOUT = 120

# command line interface
APP_NAME_FEED_INGEST = "arxifter-feed-ingest"
APP_NAME_FEED_PRUNING = "arxifter-feed-pruning"
APP_NAME_SPAN_INGEST = "arxifter-span-ingest"
COMMAND_CONFIG = "conf"
COMMAND_CONFIG_ENV = "env"
COMMAND_CONFIG_TEST = "test"
COMMAND_FEEDS = "feeds"
COMMAND_FEEDS_INGEST = "ingest"
COMMAND_FEEDS_PRUNE = "prune"
COMMAND_SPAN = "spans"
COMMAND_SPAN_INGEST_INCR = "incr"
COMMAND_SPAN_INGEST_FULL = "full"
COMMAND_SPAN_INGEST_DAYS = [str(ind) for ind in range(1, 16)]
COMMAND_TESTS = "test"
COMMAND_TESTS_FEED_PARSING = "feed-parsing"
COMMAND_TESTS_FEED_INDEXING = "feed-indexing"

# general use
TRUTH_VALUES_STR = ["1", "y", "yes", "t", "true", "truth", "on", "ok"]
FALSE_VALUES_STR = ["0", "n", "no", "f", "false", "untrue", "off", "ko"]
REPLACEMENT_CHAR = "□"

# LLM prompts
LLM_PROMPT_COMMENT_START = ";;"
# encoding info into model name
LLM_NAME_SEP = "|"
LLM_NAME_THINK = "think"
LLM_NAME_COT = "cot"
# asking the remote LLM:
LLM_ASKING_RETRY = 0
LLM_ASKING_MAX_CONN = 1000
LLM_ASKING_MAX_CONN_KA = 100
# answers from LLM
ARTICLE_KEY_RANK = "artnum"
ARTICLE_KEY_RANK_VAR = ["art", "num"]
# non-matching answers
LLM_MATCHES_KEYS = ["match"]
LLM_SUGGESTION_KEY = "instead"
# key parts for title start in LLM answers
LLM_TITLE_START_KEYS = ["title", "prefix", "start"]
LLM_TITLE_START_REGS = [
    re.compile("first(.*)two"),
    re.compile("first(.*)words"),
    re.compile("two(.*)words"),
    re.compile("start(.*)words"),
]
# repairing the naswers
JSON_START_REMOVALS = ["```json", "```"]
JSON_END_REMOVALS = ["```"]
JSON_FLANK_START = "```json"
JSON_FLANK_END = "```"
ARTICLE_RECOGNIZING_THRESHOLD = 0.1

# sifting through last counts vs. last days
PRESIFT_LAST_COUNT = "last_count"
PRESIFT_LAST_DAYS = "last_days"
# data storage
DATA_DIR_PERM = "perm"
DATA_DIR_CURR = "curr"
DOCUMENTS_SUBDIR = "docs"
VECTORS_SUBDIR = "vecs"
HNSWDATA_SUBDIR = "hnsw"
# static embeddings
HNSWDATA_SPACE = "ip"
HNSWDATA_INDEX = "hnsw_index.bin"
PRESIFTING_STATIC_OVERHANG = 5
# lib for static embeddings
HNSWLIB_PATCHED_CHECK = "WITH_UNIQUE_DOCS"
HNSWLIB_PATCHED_SEARCH = "hnswlib.cpython*.so"
# tests
DATA_DIR_TEST = "test"
DATA_DIR_TEST_CURR = "curr"
DATA_DIR_TEST_PREV = "prev"

# questions on LLM
MIN_QUERY_LEN = 3
MAX_QUERY_LEN = 1000
# not using "completions", b/c their outputs mix text with reasoning
LLM_API_FORM_RESPONSES = "responses"
LLM_API_FORM_CHAT_COMPLETIONS = "chat-completions"

# data storage
ACTIVE_DATA_DIR_MAKING = "%Y_%m%d_%H%M"
ACTIVE_DATA_DIR_LISTING = re.compile('^[\\d]{4}_[\\d]{4}_[\\d]{4}$')
ATTEMPT_COUNT_DATA_DIR = 3

# config, incl. its presentation to frontend
CONFIG_OTHER_LETTERS = [".", "_", "-"]
JS_FABRIC_PREFIX = "get_fabric_"
INDENT_SIZE = 4

# data embedding info
INFO_FILE_NAME = "info.json"
STATIC_EMBED_MODEL_NAME_KEY = "static_embed_model_name"
DENSE_EMBED_MODEL_NAME_KEY = "dense_embed_model_name"
EMBEDDING_DIMENSION_KEY = "embedding_dimension"

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

# using LLM embeddings
ENV_HF_MUTE = ["HF_HUB_DISABLE_TELEMETRY", "HF_HUB_OFFLINE"]
ENV_HF_MODELS_CACHE_DIR = "HF_HUB_CACHE"
ENV_HF_ASSETS_CACHE_DIR = "HF_ASSETS_CACHE"
HF_MODELS_SUBDIR = "hub"
HF_ASSETS_SUBDIR = "assets"
# local embedding models
HF_MODEL_DIR_PREFIX = "models--"
FE_MODEL_SPEC_FILE_NAME = "info.toml"
FE_DATA_PREC = np.float32
FE_DATA_CAST = "same_kind"

# sending texts to inferring LLM models
LLM_INFERRING_TITLE_THRESHOLD = 1024
LLM_INFERRING_TITLE_CUT_LENGTH = 1000
LLM_INFERRING_ABSTRACT_THRESHOLD = 2048
LLM_INFERRING_ABSTRACT_CUT_LENGTH = 2000
LLM_INFERRING_CUT_NOTICE = "[cut]"

# getting the feeds
ATTEMPT_COUNT_FEED = 6
RSS_FEED_TAKE_SLEEP = 15
RSS_FEED_INDEX_SLEEP = 10
RSS_FEED_TAKE_TIMEOUT = 180
RSS_FEED_URL_BASE = "https://connect.biorxiv.org/biorxiv_xml.php?subject="
RSS_FEED_FILE_NAME = "feed.rss"
RSS_FEED_LINK_SUFFIX_RSS = "?rss=1"
RSS_FEED_LINK_SUFFIX_VERSION = re.compile('v(\\d)$')

# feed and doc parsing
DOI_PREFIX = "doi:"
DOC_DOI_KEY = "doi"
DOC_LINK_KEY = "link"
DOC_SUBJECT_KEY = "category"
DOC_BASE_KEYS = [
    "title",
    "authors",
    "abstract",
    DOC_DOI_KEY,
    "date",
    DOC_LINK_KEY,
    DOC_SUBJECT_KEY,
]
DOC_LINK_START = "https://www.biorxiv.org/content/"
DOC_VERSION_KEY = "version"
DOC_TYPE_KEY = "type"

# config for UI and parsing the feeds
MAX_RECALL_SIFTS_COUNT = 100
BIORXIV_FEED_SIZE = 30
BIORXIV_FEED_MINIMAL_SIZE = 20
BIORXIV_DOI_PREFIX = "doi:"
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
    "bigcirc": " o",
    "nabla": "∇",
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
# lists in PDF texts turn to "O_LI...C_LI" itemization in RSS feeds;
# it is multiline and w/o any brackets, etc. around;
FEED_MATCH_LISTS = re.compile(r"(O_LI)((?!O_LI).*?)C_LI", flags=re.M | re.S)
FEED_FLANK_LISTS = {"O_LI": [" •", " "]}

# LLM-result presentation to frontend
VIEW_WARNING_KEY = "warning"
VIEW_WARNING_ANSWER_WRONG = "an unrecognizable answer from LLM"

# mocking related
MOCK_SUBJECTS_ANSWER = ["all", "cell", "test"]
MOCK_SUBJECTS_SUGGESTED = ["ani", "bio", "gen"]
MOCK_ANSWER_EXPLAINED = "answer_explained.json"
MOCK_SUGGESTED_EXPLAINED = "suggested_explained.json"

BIORXIV_SUBJECT_NAMES = [
    "animal_behavior_and_cognition",
    "biochemistry",
    "bioengineering",
    "bioinformatics",
    "biophysics",
    "cancer_biology",
    "cell_biology",
    "developmental_biology",
    "ecology",
    "evolutionary_biology",
    "genetics",
    "genomics",
    "immunology",
    "microbiology",
    "molecular_biology",
    "neuroscience",
    "paleontology",
    "pathology",
    "pharmacology_and_toxicology",
    "physiology",
    "plant_biology",
    "scientific_communication_and_education",
    "synthetic_biology",
    "systems_biology",
    "zoology",
]
