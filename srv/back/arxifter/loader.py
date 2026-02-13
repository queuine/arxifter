#!/usr/bin/env python
"""
Usage of the embedded feeds.
It is active when ingested feeds are used for answering user questions.
"""
import json
from pathlib import Path

import numpy as np
try:
    # presifting uses spacy only at debugging,
    # thus it does not need to be present here;
    import spacy
except Exception:
    pass

from .setting import (
    DOCUMENTS_SUBDIR,
    VECTORS_SUBDIR,
    HNSWDATA_SUBDIR,
    HNSWDATA_SPACE,
    HNSWDATA_INDEX,
    INFO_FILE_NAME,
    STATIC_EMBED_MODEL_NAME_KEY,
    DENSE_EMBED_MODEL_NAME_KEY,
    EMBEDDING_DIMENSION_KEY,
    PRESIFTING_STATIC_OVERHANG,
)
from .utils import (
    load_encoders_info,
    check_encoders_info,
)
from .logging import log_message


def _check_used_embed_model_names(base_path, encoders, logger):
    is_correct = True

    try:
        encoders_info = load_encoders_info(base_path)
        is_correct = check_encoders_info(encoders_info, encoders)
        if not is_correct:
            past_static_encoder_name = encoders_info.get(
                STATIC_EMBED_MODEL_NAME_KEY, None
            )
            past_dense_encoder_name = encoders_info.get(
                DENSE_EMBED_MODEL_NAME_KEY, None
            )
            curr_static_encoder_name = encoders["static"]["name"]
            curr_dense_encoder_name = encoders["dense"]["name"]
            logger.error("\n".join([
                "encoders have changed since the last doc indexing:",
                (
                    f"static past: {past_static_encoder_name} "
                    f"current: {curr_static_encoder_name}"
                ),
                (
                    f"dense past: {past_dense_encoder_name}"
                    f"current: {curr_dense_encoder_name}"
                ),
                str(base_path),
            ]))
    except Exception as exc:
        is_correct = False
        logger.error("\n".join([
            "cannot read encoders info:",
            str(base_path),
            str(exc),
        ]))

    return is_correct


def _get_static_embedding_dimension(data_dir, logger):
    embedding_dimension = 0
    data_info_path = Path(data_dir, INFO_FILE_NAME)
    try:
        with open(data_info_path, encoding="utf8") as fh:
            embedding_dimension = int(json.load(fh)[
                EMBEDDING_DIMENSION_KEY
            ])
    except Exception as exc:
        embedding_dimension = 0
        logger.error("\n".join([
            "cannot get static-embedding dimension from the info file:",
            str(data_info_path),
            str(exc),
        ]))

    return embedding_dimension


def _get_feed_docs(base_path):
    for doc_path in sorted(Path(
        base_path,
        DOCUMENTS_SUBDIR,
    ).glob("???.json")):
        yield {
            "content": json.loads(doc_path.read_text(encoding="utf8")),
            "name": doc_path.stem,
        }


def _get_dense_feed_vectors(base_path):
    for vec_path in sorted(Path(
        base_path,
        VECTORS_SUBDIR,
    ).glob("???.npy")):
        yield np.load(
            vec_path,
            allow_pickle=False,
        )


def _compare_dense_vectors(feed_vectors, query_vector):
    feed_vectors = list(feed_vectors)

    similarities = [
        # here assuming all the vectors are (alike) numpy vectors;
        # the fastembed library does that for dense embeddings;
        query_vector.dot(doc_vector)
        for doc_vector in feed_vectors
    ]

    return [
        int(item[1]) for item in
        sorted(
            zip(similarities, range(len(similarities))),
            key=lambda item: item[0],
            reverse=True,
        )
    ]


def _find_closest_articles_by_hnsw_search(
    conf, encoder, base_path, query, logger, debugging
):
    query_embedding = encoder["method"](query, is_query=True)
    embedding_dimension = _get_static_embedding_dimension(
        Path(
            base_path,
            HNSWDATA_SUBDIR,
        ),
        logger,
    )
    if query_embedding.shape[0] != embedding_dimension:
        raise OSError(
            "dimension of static embedding differs "
            "for the query vs. saved docs"
        )

    p = conf["libs"]["hnswlib"]["module"].Index(
        space=HNSWDATA_SPACE, dim=embedding_dimension
    )
    p.load_index(str(Path(
        base_path,
        HNSWDATA_SUBDIR,
        HNSWDATA_INDEX,
    )))

    hnswlib_with_unique_docs = conf["libs"]["hnswlib"]["with_unique_docs"]
    count_to_provide = conf["sifting"]["pick_count_static"]
    count_to_search = count_to_provide + (
        0 if hnswlib_with_unique_docs else PRESIFTING_STATIC_OVERHANG
    )

    search_labels_found, _ = p.knn_query(
        query_embedding,
        k=count_to_search,
        **dict([["unique_docs", True]] if hnswlib_with_unique_docs else []),
    )
    search_labels_all = [int(item) for item in search_labels_found[0]]

    presifted_doc_ids = list({
        (idx >> 32): True for idx in search_labels_all
    })[:count_to_provide]

    if debugging:
        try:
            documents = list(_get_feed_docs(base_path))
            logger.info("sentence-wise presifting:\n" + str([
                documents[idx]["name"] for idx in presifted_doc_ids
            ]))
            nlp = spacy.blank("en")
            nlp.add_pipe("sentencizer")
            for idx in search_labels_all:
                doc_id, sent_id = [idx >> 32, idx & ((1 << 32) - 1)]
                curr_doc = documents[doc_id]
                curr_sent = (
                    curr_doc["content"]["title"] if (sent_id == 0) else
                    str(list(
                        nlp(curr_doc["content"]["abstract"]).sents
                    )[sent_id - 1])
                )
                log_message(str([
                    documents[doc_id]["name"], sent_id, curr_sent
                ]))
        except Exception:
            logger.debug("could not get the info on individual sentences")

    return presifted_doc_ids


def _find_closest_articles_by_vector_comparison(
    conf, encoder, base_path, query, logger, debugging
):
    query_vec = encoder["method"](
        query,
        is_query=True,
    )

    presifted_doc_ids = _compare_dense_vectors(
        _get_dense_feed_vectors(base_path),
        query_vec,
    )[:conf["sifting"]["pick_count_dense"]]

    if debugging:
        documents = list(_get_feed_docs(base_path))
        logger.info("document-wise presifting:\n" + str([
            documents[idx]["name"] for idx in presifted_doc_ids
        ]))

    return presifted_doc_ids


def _get_docs_for_the_searching(
    base_path, ids_split, ids_whole, logger, debugging
):
    ids_to_use = {idx: True for idx in ids_whole}
    for idx in ids_split:
        if idx not in ids_to_use:
            ids_to_use[idx] = True

    ids_to_use = list(ids_to_use)

    documents = list(_get_feed_docs(base_path))

    if debugging:
        merged_count = len(ids_to_use)
        logger.info(f"merged presifting: {merged_count} docs\n" + str([
            documents[idx]["name"] for idx in ids_to_use
        ]))

    return [
        documents[item] for item in ids_to_use
    ]


def presift_docs(conf, encoders, data_dir, base_path, query, get_logger):
    """
    Provides articles with content similar to the given query.
    """
    logger = get_logger(__name__)
    if not _check_used_embed_model_names(
        data_dir, encoders, logger
    ):
        return None

    docs = None
    debugging = conf["debugging"]["query_sifting"]
    try:
        ids_split = _find_closest_articles_by_hnsw_search(
            conf, encoders["static"], base_path, query, logger, debugging
        )
    except Exception as exc:
        ids_split = []
        logger.warning("\n".join([
            "an error occurred during the split-form presifting:",
            str(base_path),
            str(exc),
        ]))
    try:
        ids_whole = _find_closest_articles_by_vector_comparison(
            conf, encoders["dense"], base_path, query, logger, debugging
        )
    except Exception as exc:
        ids_whole = []
        logger.warning("\n".join([
            "an error occurred during the whole-form presifting:",
            str(base_path),
            str(exc),
        ]))
    if (len(ids_split) == 0) and (len(ids_whole) == 0):
        logger.error("\n".join([
            "could not get any article by presifting",
            str(base_path),
        ]))
        return None
    try:
        docs = _get_docs_for_the_searching(
            base_path, ids_split, ids_whole, logger, debugging
        )
    except Exception as exc:
        docs = None
        logger.error("\n".join([
            "an error occurred during the presifting merge:",
            str(base_path),
            str(exc),
        ]))

    return docs
