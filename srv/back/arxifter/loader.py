#!/usr/bin/env python
"""
Usage of the embedded feeds.
It is active when ingested feeds are used for answering user questions.
"""
import os, json
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


def _get_feed_docs(base_path, subject=None):
    for doc_path in sorted(Path(
        base_path,
        DOCUMENTS_SUBDIR,
    ).glob("???.json")):
        yield {
            "content": json.loads(doc_path.read_text(encoding="utf8")),
            "name": doc_path.stem,
            "subject": subject,
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
        [int(item[1]), float(item[0])] for item in
        sorted(
            zip(similarities, range(len(similarities))),
            key=lambda item: item[0],
            reverse=True,
        )
    ]


def _find_closest_articles_by_hnsw_search(
    conf, encoder, base_path, sub_rank, query, logger, debugging
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

    search_labels_found, search_dists_found = p.knn_query(
        query_embedding,
        k=count_to_search,
        **dict([["unique_docs", True]] if hnswlib_with_unique_docs else []),
    )
    search_labels_all = [int(item) for item in search_labels_found[0]]
    search_dists_all = [float(item) for item in search_dists_found[0]]

    presifted_doc_ids = {}
    presifted_doc_specs = []
    doc_count = 0
    for rank, idx in enumerate(search_labels_all):
        doc_id = idx >> 32
        if doc_id in presifted_doc_ids:
            continue
        presifted_doc_ids[doc_id] = True
        presifted_doc_specs.append([
            doc_id,
            search_dists_all[rank],
            sub_rank,
        ])
        doc_count += 1
        if doc_count >= count_to_provide:
            break

    if debugging:
        try:
            documents = list(_get_feed_docs(base_path))
            logger.info("\n".join([
                "sentence-wise presifting:",
                str(base_path),
                str([
                    documents[idx]["name"] for idx in presifted_doc_ids
                ]),
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

    return presifted_doc_specs


def _find_closest_articles_by_vector_comparison(
    conf, encoder, base_path, sub_rank, query, logger, debugging
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
        logger.info("\n".join([
            "document-wise presifting:",
            str(base_path),
            str([
                documents[idx[0]]["name"] for idx in presifted_doc_ids
            ]),
        ]))

    return [
        [item[0], item[1], sub_rank] for item in presifted_doc_ids
    ]


def _presift_the_split_docs_way(
    conf, encoder, data_dir, base_subjects, query, logger, debugging
):
    found_docs = []
    for sub_rank, subject in enumerate(base_subjects):
        base_path = os.path.join(data_dir, subject)

        found_docs.extend(_find_closest_articles_by_hnsw_search(
            conf, encoder, base_path, sub_rank, query, logger, debugging
        ))

    # hnswlib reports distances, thus ordering it from the least ones;
    return [
        [item[0], item[2]] for item in sorted(
            found_docs, key=lambda x: x[1], reverse=False
        )
    ][:conf["sifting"]["pick_count_static"]]


def _presift_the_whole_docs_way(
    conf, encoder, data_dir, base_subjects, query, logger, debugging
):
    found_docs = []
    for sub_rank, subject in enumerate(base_subjects):
        base_path = os.path.join(data_dir, subject)

        found_docs.extend(_find_closest_articles_by_vector_comparison(
            conf, encoder, base_path, sub_rank, query, logger, debugging
        ))

    # dot product is a similarity, thus ordering it from the biggest ones;
    return [
        [item[0], item[2]] for item in sorted(
            found_docs, key=lambda x: x[1], reverse=True
        )
    ][:conf["sifting"]["pick_count_static"]]


def _get_docs_for_the_searching(
    data_dir, base_subjects, ids_split, ids_whole, logger, debugging
):
    documents = [
        list(_get_feed_docs(os.path.join(data_dir, subject), subject))
        for subject in base_subjects
    ]

    try:
        if debugging:
            logger.info("\n".join([
                "overall document-wise presifting:",
                str([
                    [
                        base_subjects[item[1]],
                        documents[item[1]][item[0]]["name"],
                    ] for item in ids_whole
                ]),
                "overall sentence-wise presifting:",
                str([
                    [
                        base_subjects[item[1]],
                        documents[item[1]][item[0]]["name"],
                    ] for item in ids_split
                ]),
            ]))
    except Exception:
        pass

    use_docs = ids_whole[:]

    ids_to_use = {((idx[1] << 32) + idx[0]): True for idx in ids_whole}
    for idx in ids_split:
        effective_id = (idx[1] << 32) + idx[0]
        if effective_id not in ids_to_use:
            ids_to_use[effective_id] = True
            use_docs.append(idx)

    if debugging:
        merged_count = len(use_docs)
        logger.info(f"merged presifting: {merged_count} docs\n" + str([
            [
                base_subjects[item[1]],
                documents[item[1]][item[0]]["name"],
            ] for item in use_docs
        ]))

    return [
        documents[item[1]][item[0]] for item in use_docs
    ]


def presift_docs(conf, encoders, data_dir, base_subjects, query, get_logger):
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
        ids_split = _presift_the_split_docs_way(
            conf,
            encoders["static"],
            data_dir,
            base_subjects,
            query,
            logger,
            debugging,
        )
    except Exception as exc:
        ids_split = []
        logger.warning("\n".join([
            "an error occurred during the split-form presifting:",
            str(data_dir),
            str(base_subjects),
            str(exc),
        ]))
    try:
        ids_whole = _presift_the_whole_docs_way(
            conf,
            encoders["dense"],
            data_dir,
            base_subjects,
            query,
            logger,
            debugging,
        )
    except Exception as exc:
        ids_whole = []
        logger.warning("\n".join([
            "an error occurred during the whole-form presifting:",
            str(data_dir),
            str(base_subjects),
            str(exc),
        ]))
    if (len(ids_split) == 0) and (len(ids_whole) == 0):
        logger.error("\n".join([
            "could not get any article by presifting",
            str(data_dir),
            str(base_subjects),
        ]))
        return None
    try:
        docs = _get_docs_for_the_searching(
            data_dir, base_subjects, ids_split, ids_whole, logger, debugging
        )
    except Exception as exc:
        docs = None
        logger.error("\n".join([
            "an error occurred during the presifting merge:",
            str(data_dir),
            str(base_subjects),
            str(exc),
        ]))

    return docs
