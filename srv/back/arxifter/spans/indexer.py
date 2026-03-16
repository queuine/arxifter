#!/usr/bin/env python
"""
Making and saving of indexes of embeddings of docs from a depo date range.
"""

import os, time
from pathlib import Path

import numpy as np

from ..setting import (
    NEW_DIRS_MODE,
)
from ..logging import (
    log_error,
)
from .setting import (
    HNSWDATA_SPACE,
    INDEX_DOCS_SPLIT,
    INDEX_DOCS_WHOLE,
    STATIC_EMBED_MODEL_DIM_KEY,
    DENSE_EMBED_MODEL_DIM_KEY,
    API_FEED_TAKE_PAUSE,
)
from .utils import (
    load_last_encoding_info,
)
from .depositer import (
    DATA_DIR_DEPO,
    get_span_docs,
    get_doc_embed_split_count,
    get_doc_embed_split,
    get_doc_embed_whole,
)
from .namer import (
    prepare_doc_naming,
    set_doc_rank,
    set_doc_parts_count,
    get_span_parts_count,
    get_span_docs_count,
    get_span_docs_info,
)


def _get_index_path_split(subj_dir):
    return Path(subj_dir, INDEX_DOCS_SPLIT)


def _get_index_path_whole(subj_dir):
    return Path(subj_dir, INDEX_DOCS_WHOLE)


def _index_span_vectors_split(conf, curr_dir, enc_info):
    depo_dir = Path(conf["data"]["storage_dir"]["path"], DATA_DIR_DEPO)
    for subject in conf["feeds"]["subjects"]["list"]:
        time.sleep(API_FEED_TAKE_PAUSE)
        subj_dir = Path(curr_dir, subject)
        index_path = _get_index_path_split(subj_dir)
        overall_count_status, overall_count = get_span_parts_count(subj_dir)
        if (not overall_count_status) or (overall_count is None):
            return False

        p = conf["libs"]["hnswlib"]["module"].Index(
            space=HNSWDATA_SPACE, dim=enc_info[STATIC_EMBED_MODEL_DIM_KEY]
        )
        p.init_index(max_elements=overall_count)

        docs_info_status, docs_info = get_span_docs_info(subj_dir)
        if not docs_info_status:
            log_error("could not get the info on docs")
            return False
        for one_doc_info in docs_info:
            doc_idx = one_doc_info["id"]
            doc_embeds = get_doc_embed_split(depo_dir / subject, one_doc_info)
            ids = (doc_idx << 32) + np.arange(len(doc_embeds))
            p.add_items(doc_embeds, ids)

        p.save_index(str(index_path))

    return True


def _index_span_vectors_whole(conf, curr_dir, enc_info):
    depo_dir = Path(conf["data"]["storage_dir"]["path"], DATA_DIR_DEPO)
    for subject in conf["feeds"]["subjects"]["list"]:
        time.sleep(API_FEED_TAKE_PAUSE)
        subj_dir = Path(curr_dir, subject)
        index_path = _get_index_path_whole(subj_dir)
        overall_count_status, overall_count = get_span_docs_count(subj_dir)
        if (not overall_count_status) or (overall_count is None):
            return False

        p = conf["libs"]["hnswlib"]["module"].Index(
            space=HNSWDATA_SPACE, dim=enc_info[DENSE_EMBED_MODEL_DIM_KEY]
        )
        p.init_index(max_elements=overall_count)

        docs_info_status, docs_info = get_span_docs_info(subj_dir)
        if not docs_info_status:
            log_error("could not get the info on docs")
            return False
        for one_doc_info in docs_info:
            doc_idx = one_doc_info["id"]
            doc_embed = get_doc_embed_whole(depo_dir / subject, one_doc_info)
            p.add_items(doc_embed, doc_idx << 32)

        p.save_index(str(index_path))

    return True


def _prepare_names(conf, curr_dir, date_from, date_upto):
    depo_dir = Path(conf["data"]["storage_dir"]["path"], DATA_DIR_DEPO)
    for subject in conf["feeds"]["subjects"]["list"]:
        subj_dir = Path(curr_dir, subject)
        os.makedirs(str(subj_dir), mode=NEW_DIRS_MODE, exist_ok=True)
        prepare_doc_naming(subj_dir)
        for one_doc in get_span_docs(
            conf, subject, date_from, date_upto
        ):
            is_set, doc_id = set_doc_rank(subj_dir, one_doc)
            if is_set and (doc_id is not None):
                set_doc_parts_count(
                    subj_dir,
                    doc_id,
                    get_doc_embed_split_count(depo_dir / subject, one_doc),
                )


def index_span_vectors(conf, curr_dir, date_from, date_upto):
    """
    Makes and saves indexes for the whole-docs and sentence-wise embeddings
    of docs of a given date range of depo.
    """
    try:
        _prepare_names(conf, curr_dir, date_from, date_upto)
    except Exception as exc:
        log_error("\n".join([
            "could not prepare names",
            str(exc),
        ]))
        return False

    try:
        enc_info = load_last_encoding_info(curr_dir)
    except Exception as exc:
        log_error("\n".join([
            "could not take the used encoder info",
            str(exc),
        ]))
        return False

    try:
        if not _index_span_vectors_split(conf, curr_dir, enc_info):
            return False
    except Exception as exc:
        log_error("\n".join([
            "could not index split-docs vectors",
            str(exc),
        ]))
        return False

    try:
        if not _index_span_vectors_whole(conf, curr_dir, enc_info):
            return False
    except Exception as exc:
        log_error("\n".join([
            "could not index whole-docs vectors",
            str(exc),
        ]))
        return False

    return True
