#!/usr/bin/env python
"""
Preparation of embedded texts of feed articles.
The articles get encoded in two different ways:
* via a simpler static encoding done on individual sentences,
* via a dense encoding done on overall texts.

These feed embeddings are done as batches during the stage
when RSS feeds are downloaded and ingested.
"""

import os, json, itertools, shutil
from pathlib import Path

import numpy as np
import spacy
import hnswlib

from .setting import (
    NEW_DIRS_MODE,
    DOCUMENTS_SUBDIR,
    VECTORS_SUBDIR,
    HNSWDATA_SUBDIR,
    HNSWDATA_SPACE,
    HNSWDATA_INDEX,
    HNSWDATA_LABELS,
    HNSWDATA_PARTS,
    INFO_FILE_NAME,
    EMBEDDING_DIMENSION_KEY,
)
from .logging import log_error


def _make_vec_dir(base_path):
    vec_dir = os.path.join(base_path, VECTORS_SUBDIR)
    hnsw_dir = os.path.join(base_path, HNSWDATA_SUBDIR)
    try:
        os.makedirs(
            vec_dir,
            mode=NEW_DIRS_MODE,
            exist_ok=True
        )
        os.makedirs(
            hnsw_dir,
            mode=NEW_DIRS_MODE,
            exist_ok=True
        )
    except Exception as exc:
        log_error("\n".join([
            "could not prepare dirs to save embedded texts of a feed:",
            str(vec_dir),
            str(exc),
        ]))
        return False
    return True


def _copy_doc_vectors(
    curr_base_path, curr_doc_name, prev_base_path, prev_doc_name
):
    for subdir in [VECTORS_SUBDIR, HNSWDATA_SUBDIR]:
        prev_vec = Path(
            prev_base_path,
            subdir,
            prev_doc_name + ".npy",
        )
        curr_vec = Path(
            curr_base_path,
            subdir,
            curr_doc_name + ".npy",
        )
        try:
            if prev_vec.exists() and prev_vec.is_file():
                shutil.copy2(prev_vec, curr_vec)
        except Exception:
            pass


def _copy_present_vectors(base_path, prev_base_path):
    """
    Checking the articles according to DOI only, b/c RSS feeds
    do not have version information, apparently only providing v.1 docs.
    Even if doc version would get changed, it would hardly alter much
    the embedding vectors, b/c version change does not change the topic.
    """
    prev_docs = {}
    if prev_base_path is not None:
        for prev_doc_path in sorted(Path(
            prev_base_path,
            DOCUMENTS_SUBDIR,
        ).glob("???.json")):
            try:
                with open(prev_doc_path, encoding="utf8") as prev_fh:
                    prev_doi = json.load(prev_fh).get("doi", None)
                    if prev_doi not in [None, ""]:
                        prev_docs[prev_doi] = prev_doc_path.stem
            except Exception:
                pass

    for doc_path in sorted(Path(
        base_path,
        DOCUMENTS_SUBDIR,
    ).glob("???.json")):
        with open(doc_path, encoding="utf8") as fh:
            try:
                doc_doi = json.load(fh).get("doi", None)
            except Exception:
                doc_doi = None
            if doc_doi in prev_docs:
                _copy_doc_vectors(
                    base_path,
                    doc_path.stem,
                    prev_base_path,
                    prev_docs[doc_doi],
                )


def _index_docs_sentences(encoder, base_path, debugging=False):
    """
    Does the RSS embedding via:
    * reading the saved docs previously made from RSS feeds,
    * embedding sentences of the docs via a local embedding model,
    * saving the embedded data indexed via the hnswlib.
    """
    error_occurred = False

    # preparing the lib for text splitting
    try:
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
    except Exception as exc:
        error_occurred = True
        log_error("\n".join([
            "cannot initialize the article-text splitter",
            str(exc),
        ]))
        error_occurred = True

    if error_occurred:
        return None

    # taking and embedding sentences of the articles
    embeddings = []
    lengths = []
    sentences_all = []
    for doc_path in sorted(Path(
        base_path,
        DOCUMENTS_SUBDIR,
    ).glob("???.json")):
        vecs_path = Path(base_path, HNSWDATA_SUBDIR, doc_path.stem + ".npy")
        got_vecs = False
        if vecs_path.exists():
            try:
                doc_vecs = list(np.load(vecs_path, allow_pickle=False))
                embeddings.append(doc_vecs)
                lengths.append(len(doc_vecs))
                got_vecs = True
                if debugging:
                    sentences_all.append([""] * len(doc_vecs))
            except Exception:
                got_vecs = False
        if got_vecs:
            continue

        try:
            doc = json.loads(doc_path.read_text(encoding="utf8"))
            sentences = [doc["title"]] + [
                str(item) for item in nlp(doc["abstract"]).sents
            ]
            if debugging:
                sentences_all.append(sentences)
            doc_vecs = encoder["method"](sentences)
            embeddings.append(doc_vecs)
            lengths.append(len(doc_vecs))
            np.save(
                vecs_path,
                np.array(doc_vecs),
                allow_pickle=False,
            )
        except Exception as exc:
            error_occurred = True
            log_error("\n".join([
                "error during split-wise feed indexing:",
                str(doc_path),
                str(exc),
            ]))
            break

    if error_occurred:
        return None

    # debugging-only part
    if debugging:
        try:
            with open(
                Path(
                    base_path,
                    HNSWDATA_SUBDIR,
                    HNSWDATA_PARTS,
                ),
                "w",
                encoding="utf8",
            ) as fh:
                json.dump(list(itertools.chain(*sentences_all)), fh)
        except Exception as exc:
            error_occurred = True
            log_error("\n".join([
                "cannot save debugging information",
                str(exc),
            ]))
            error_occurred = True

    if error_occurred:
        return None

    # taking the embedding-vector dimension that is eventually returned
    embed_dims_var = False
    embed_dim = 0
    for embed_set in embeddings:
        if len(embed_set) > 0:
            if embed_dim == 0:
                embed_dim = embed_set[0].shape[0]
            elif embed_dim != embed_set[0].shape[0]:
                embed_dims_var = True
    if embed_dim == 0:
        log_error("no split-text embedding was created")
        return None
    if embed_dims_var:
        log_error("split-text embedding vectors have varying dimensions")
        return None

    # putting the embedded text parts into an index set via hnswlib,
    try:
        labels = []
        item_count = sum(lengths)
        p = hnswlib.Index(space=HNSWDATA_SPACE, dim=embed_dim)
        p.init_index(max_elements=item_count)
        start_item_idx = 0
        for doc_idx, doc_embeds in enumerate(embeddings):
            doc_sntc_count = lengths[doc_idx]
            ids = np.arange(start_item_idx, start_item_idx + doc_sntc_count)
            start_item_idx += lengths[doc_idx]
            p.add_items(doc_embeds, ids)
            labels += ([doc_idx] * doc_sntc_count)
        p.save_index(str(Path(
            base_path,
            HNSWDATA_SUBDIR,
            HNSWDATA_INDEX,
        )))
        np.save(
            Path(
                base_path,
                HNSWDATA_SUBDIR,
                HNSWDATA_LABELS,
            ),
            np.array(labels),
            allow_pickle=False,
        )
    except Exception as exc:
        error_occurred = True
        log_error("\n".join([
            "cannot save the hnswlib-indexed data",
            str(exc),
        ]))
        error_occurred = True

    if error_occurred:
        return None

    return embed_dim


def _index_docs_whole(encoder, base_path, prev_base_path):
    """
    Does the RSS embedding via:
    * reading the saved docs previously made from RSS feeds,
    * embedding the docs via a local embedding model,
    * saving the embedded data along the original docs.
    """
    copied_vec = False
    embed_dim = 0
    error_occurred = False
    for doc_path in sorted(Path(
        base_path,
        DOCUMENTS_SUBDIR,
    ).glob("???.json")):
        if Path(
            base_path,
            VECTORS_SUBDIR,
            doc_path.stem + ".npy",
        ).exists():
            copied_vec = True
            continue

        try:
            doc = json.loads(doc_path.read_text(encoding="utf8"))
            vec = encoder["method"](
                "\n".join([
                    "title: " + doc["title"],
                    "abstract: " + doc["abstract"],
                ]),
                is_query=False,
            )
            np.save(
                Path(
                    base_path,
                    VECTORS_SUBDIR,
                    doc_path.stem,
                ),
                vec,
                allow_pickle=False,
            )
            if embed_dim == 0:
                embed_dim = vec.shape[0]
        except Exception as exc:
            error_occurred = True
            log_error("\n".join([
                "error during feed indexing:",
                str(doc_path),
                str(exc),
            ]))
            break

    if error_occurred:
        return None

    prev_embed_dim = (
        _get_embedding_dimension(Path(prev_base_path, VECTORS_SUBDIR))
        if copied_vec else 0
    )
    if embed_dim == 0:
        if prev_embed_dim == 0:
            log_error("no whole-text embedding was created/copied")
            return None
        embed_dim = prev_embed_dim

    if prev_embed_dim not in [0, embed_dim]:
        log_error(
            "dims of whole-text embeddings differ for the "
            f"created {embed_dim} vs. copied {prev_embed_dim} ones"
        )
        return None

    return embed_dim


def _get_embedding_dimension(dir_path):
    if dir_path is None:
        return 0

    dim = 0
    try:
        with open(Path(dir_path, INFO_FILE_NAME), encoding="utf8") as fh:
            dim = int(json.load(fh)[EMBEDDING_DIMENSION_KEY])
    except Exception:
        dim = 0
    return dim


def _save_embedding_dimensions(
    base_path,
    static_embed_dim,
    dense_embed_dim
):
    error_occurred = False

    split_text_info_path = Path(
        base_path,
        HNSWDATA_SUBDIR,
        INFO_FILE_NAME,
    )
    try:
        split_text_info_path.write_text(
            json.dumps({
                EMBEDDING_DIMENSION_KEY: static_embed_dim,
            }),
            encoding="utf8",
        )
    except Exception as exc:
        error_occurred = True
        log_error("\n".join([
            "cannot write info on the split-text embedding:",
            str(split_text_info_path),
            str(exc),
        ]))

    whole_text_info_path = Path(
        base_path,
        VECTORS_SUBDIR,
        INFO_FILE_NAME,
    )
    try:
        whole_text_info_path.write_text(
            json.dumps({
                EMBEDDING_DIMENSION_KEY: dense_embed_dim,
            }),
            encoding="utf8",
        )
    except Exception as exc:
        error_occurred = True
        log_error("\n".join([
            "cannot write info on the whole-text embedding:",
            str(split_text_info_path),
            str(exc),
        ]))

    return not error_occurred


def index_docs(encoders, base_path, prev_base_path, debugging=False):
    """
    Feed texts get indexed here:
    * in a split-text way via a static encoder,
    * in a whole-text way via a dense encoder.
    If some articles already have embeddings created from a previous batch,
    they get reused to limit the computational needs.
    """
    if not _make_vec_dir(base_path):
        return False

    if prev_base_path is not None:
        _copy_present_vectors(base_path, prev_base_path)

    static_embed_dim = _index_docs_sentences(
        encoders["static"], base_path, debugging
    )
    if static_embed_dim is None:
        return False

    dense_embed_dim = _index_docs_whole(
        encoders["dense"], base_path, prev_base_path
    )
    if dense_embed_dim is None:
        return False

    return _save_embedding_dimensions(
        base_path, static_embed_dim, dense_embed_dim
    )
