#!/usr/bin/env python
"""
Access to span indexes and to respective docs.
"""

import json
from pathlib import Path

from .setting import (
    HNSWDATA_SPACE,
    INDEX_DOCS_SPLIT,
    INDEX_DOCS_WHOLE,
)
from .utils import (
    check_last_encoding_info,
)
from .namer import (
    get_one_doc_info,
)
from .depositer import (
    get_one_doc_path,
    get_one_doc_data,
)


def _get_similar_docs_for_subject(
    conf,
    sub_rank,
    subj_dir,
    on_split,
    query_embedding,
    vec_dim,
    count_to_search,
    search_unique_docs,
):
    p = conf["libs"]["hnswlib"]["module"].Index(
        space=HNSWDATA_SPACE, dim=vec_dim
    )
    p.load_index(str(Path(
        subj_dir,
        INDEX_DOCS_SPLIT if on_split else INDEX_DOCS_WHOLE,
    )))

    search_labels_found, search_dists_found = p.knn_query(
        query_embedding,
        k=count_to_search,
        **dict([["unique_docs", True]] if search_unique_docs else []),
    )
    search_labels_all = [int(item) for item in search_labels_found[0]]
    search_dists_all = [float(item) for item in search_dists_found[0]]

    presifted_doc_specs = []
    for rank, idx in enumerate(search_labels_all):
        doc_id = idx >> 32
        presifted_doc_specs.append([
            doc_id,
            search_dists_all[rank],
            sub_rank,
        ])

    return presifted_doc_specs


def _get_similar_docs_split(
    conf, encoder, data_dir, base_subjects, query
):
    count_to_provide = conf["sifting"]["pick_count_static"]
    query_embedding = encoder["method"](query, is_query=True)

    found_docs = []
    for sub_rank, subject in enumerate(base_subjects):
        subj_dir = Path(data_dir, subject)
        found_docs.extend(_get_similar_docs_for_subject(
            conf,
            sub_rank,
            subj_dir,
            True,
            query_embedding,
            encoder["dim"],
            count_to_provide,
            True,
        ))

    # hnswlib reports distances, thus ordering it from the least ones;
    return [
        [item[0], item[2]] for item in sorted(
            found_docs, key=lambda x: x[1], reverse=False
        )
    ][:conf["sifting"]["pick_count_static"]]


def _get_similar_docs_whole(
    conf, encoder, data_dir, base_subjects, query
):
    count_to_provide = conf["sifting"]["pick_count_dense"]
    query_embedding = encoder["method"](query, is_query=True)

    found_docs = []
    for sub_rank, subject in enumerate(base_subjects):
        subj_dir = Path(data_dir, subject)
        found_docs.extend(_get_similar_docs_for_subject(
            conf,
            sub_rank,
            subj_dir,
            False,
            query_embedding,
            encoder["dim"],
            count_to_provide,
            False,
        ))

    # hnswlib reports distances, thus ordering it from the least ones;
    return [
        [item[0], item[2]] for item in sorted(
            found_docs, key=lambda x: x[1], reverse=False
        )
    ][:conf["sifting"]["pick_count_dense"]]


def get_doc_depo_path(conf, doc_id, subject, data_dir):
    """
    Provides depo path to a given doc of the given span.
    It is used for docs selected by LLM from a presifted set of docs.
    """
    data_root = conf["data"]["storage_dir"]["path"]
    subj_dir = Path(data_dir, subject)
    doc_data_status, doc_data = get_one_doc_info(subj_dir, doc_id)
    if not doc_data_status:
        return None
    doc_data["category"] = subject
    return get_one_doc_path(data_root, doc_data)


def _combine_presifted_doc_lists(
    conf, data_dir, base_subjects, ids_whole, ids_split, logger
):
    data_root = conf["data"]["storage_dir"]["path"]
    debugging = conf["debugging"]["query_sifting"]

    if ids_whole is None:
        ids_whole = []
    if ids_split is None:
        ids_split = []

    use_docs = ids_whole[:]

    ids_to_use = {((idx[1] << 32) + idx[0]): True for idx in ids_whole}
    for idx in ids_split:
        effective_id = (idx[1] << 32) + idx[0]
        if effective_id not in ids_to_use:
            ids_to_use[effective_id] = True
            use_docs.append(idx)

    presifted_docs = []
    presifted_docs_debug = []
    for doc_id, subj_id in use_docs:
        subject = base_subjects[subj_id]

        subj_dir = Path(data_dir, subject)
        doc_base_status, doc_base_info = get_one_doc_info(subj_dir, doc_id)
        if not doc_base_status:
            logger.warning("\n".join([
                "could not load info of a presifted doc",
                str(subj_dir),
                str([doc_id, subject]),
            ]))
            continue

        doc_base_data = {
            "category": subject,
            "date": doc_base_info["date"],
            "doi": doc_base_info["doi"],
            "version": doc_base_info["version"],
        }
        if debugging:
            presifted_docs_debug.append(doc_base_data)
        doc_info = get_one_doc_data(data_root, doc_base_data)
        presifted_docs.append({
            "content": doc_info,
            "name": doc_id,
            "subject": subject,
        })
    if debugging:
        logger.info("\n".join([
            (
                f"depo-system: overall ({len(presifted_docs)} docs) "
                "presifted info:"
            ),
            "\n".join([str(item) for item in presifted_docs_debug]),
        ]))

    return presifted_docs


def presift_docs_last(
    conf, encoders, data_dir, base_subjects, query, get_logger
):
    """
    Provides docs that are similar to a given query.
    The similarity is measured according to respective embeddings.
    """
    logger = get_logger(__name__)
    debugging = conf["debugging"]["query_sifting"]

    if not check_last_encoding_info(encoders, data_dir):
        logger.error("incompatible encoders info")
        return False

    ids_split = _get_similar_docs_split(
        conf, encoders["static"], data_dir, base_subjects, query
    )
    if debugging:
        ids_split_debug = None
        if ids_split is not None:
            ids_split_debug = []
            for item in ids_split:
                doc_subject = base_subjects[item[1]]
                doc_id = item[0]
                doc_path = get_doc_depo_path(
                    conf, item[0], base_subjects[item[1]], data_dir
                )
                with open(doc_path, encoding="utf8") as fh:
                    doc_title = json.load(fh)["title"]
                ids_split_debug.append([
                    doc_subject, doc_id, doc_path, doc_title
                ])
        logger.info("\n".join([
            "depo-system: presifted split docs ids:",
            "[(\n  " + "\n),(\n  ".join([
                "\n  ".join([str(subitem) for subitem in item])
                for item in ids_split_debug
            ]) + "\n)]",
        ]))

    ids_whole = _get_similar_docs_whole(
        conf, encoders["dense"], data_dir, base_subjects, query
    )
    if debugging:
        ids_whole_debug = None
        if ids_whole is not None:
            ids_whole_debug = []
            for item in ids_whole:
                doc_subject = base_subjects[item[1]]
                doc_id = item[0]
                doc_path = get_doc_depo_path(
                    conf, item[0], base_subjects[item[1]], data_dir
                )
                with open(doc_path, encoding="utf8") as fh:
                    doc_title = json.load(fh)["title"]
                ids_whole_debug.append([
                    doc_subject, doc_id, doc_path, doc_title
                ])
        logger.info("\n".join([
            "depo-system: presifted whole docs ids:",
            "[(\n  " + "\n),(\n  ".join([
                "\n  ".join([str(subitem) for subitem in item])
                for item in ids_whole_debug
            ]) + "\n)]",
        ]))

    presifted_docs = _combine_presifted_doc_lists(
        conf, data_dir, base_subjects, ids_whole, ids_split, logger
    )
    if presifted_docs == []:
        return None
    return presifted_docs
