#!/usr/bin/env python
"""
Various fixed settings used at the depo/span part of the arxifter.
"""

import re

DATA_DIR_LAST = "last"
DATA_DIR_DEPO = "depo"
DATA_DIR_SPAN = "span"
ACTIVE_SPAN_DIR_LISTING = re.compile('^[\\d]{4}_[\\d]{4}_[\\d]{4}$')
CURRENT_DATETIME_FORMAT = "%Y_%m%d_%H%M"
SPAN_DATETIME_GLOB = ("?" * 4) + "_" + ("?" * 4) + "_" + ("?" * 4)

SUBDIR_DOCS = "docs"
SUBDIR_EMBED_SPLIT = "embed_split"
SUBDIR_EMBED_WHOLE = "embed_whole"
DOI_PREFIX = "doi:"

LAST_DATA_DIR_LISTING = re.compile('^[\\d]{4}_[\\d]{4}_[\\d]{4}$')

DOC_NAMING_DB = "doc_names.db"

HNSWDATA_SPACE = "ip"
INDEX_DOCS_SPLIT = "hnsw_split.bin"
INDEX_DOCS_WHOLE = "hnsw_whole.bin"

API_FEED_TAKE_SLEEP = 10
STATIC_EMBED_MODEL_DIM_KEY = "static_embed_model_dim"
DENSE_EMBED_MODEL_DIM_KEY = "dense_embed_model_dim"
API_FEED_TAKE_TIMEOUT = 180
API_FEED_TAKE_ATTEMPTS = 3
API_FEED_TAKE_PAUSE = 10
