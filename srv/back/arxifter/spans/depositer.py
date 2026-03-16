#!/usr/bin/env python
"""
Access to and actions on docs stored within the depo directory.
"""

import os, json, time
from pathlib import Path
import datetime as dt

import numpy as np

from ..setting import (
    NEW_DIRS_MODE,
)
from ..logging import (
    log_warning,
    log_error,
)
from ..encoder import (
    get_encoders,
)
from .setting import (
    DATA_DIR_DEPO,
    SUBDIR_DOCS,
    SUBDIR_EMBED_SPLIT,
    SUBDIR_EMBED_WHOLE,
    DOI_PREFIX,
    API_FEED_TAKE_PAUSE,
)
from .utils import (
    assure_depo_encoding_info
)
from .embedder import (
    make_embed_split,
    make_embed_whole,
)


def _check_doi_safe(doc_doi):
    is_correct = True

    for letter in doc_doi:
        if not letter.isascii():
            is_correct = False
            break
        if (
            (not letter.isalnum())
            and (letter not in [".", ",", "_", "-", "/"])  # "/" gets replaced
        ):
            is_correct = False
            break

    if not is_correct:
        raise OSError(f"doi contains unallowed character: {doc_doi}")


def _get_subj_dir(data_root, subject):
    return Path(
        data_root,
        DATA_DIR_DEPO,
        subject,
    )


def _get_doc_name(doc_doi, doc_version):
    _check_doi_safe(doc_doi)
    return doc_doi.replace("/", "--") + "__v" + str(doc_version) + ".json"


def _get_embed_name(doc_doi, doc_version):
    _check_doi_safe(doc_doi)
    return doc_doi.replace("/", "--") + "__v" + str(doc_version) + ".npy"


def _get_doc_name_pattern(doc_doi):
    _check_doi_safe(doc_doi)
    return doc_doi.replace("/", "--") + "__v*.json"


def _get_vec_name_pattern(doc_doi):
    _check_doi_safe(doc_doi)
    return doc_doi.replace("/", "--") + "__v*.npy"


def _get_path_doc(data_root, doc_data):
    doc_date = doc_data["date"]
    doc_subject = doc_data["category"]
    doc_doi = doc_data["doi"]
    doc_version = str(doc_data.get("version", "1"))

    return Path(
        data_root,
        DATA_DIR_DEPO,
        doc_subject,
        doc_date.replace("-", "_"),
        SUBDIR_DOCS,
        _get_doc_name(doc_doi, doc_version),
    )


def _get_path_embed_whole(subj_dir, doc_data):
    return Path(
        subj_dir,
        doc_data["date"].replace("-", "_"),
        SUBDIR_EMBED_WHOLE,
        _get_embed_name(doc_data["doi"], doc_data["version"]),
    )


def _get_path_embed_split(subj_dir, doc_data):
    return Path(
        subj_dir,
        doc_data["date"].replace("-", "_"),
        SUBDIR_EMBED_SPLIT,
        _get_embed_name(doc_data["doi"], doc_data["version"]),
    )


def _save_path_embed_whole(subj_dir, one_doc_info, embed_data_whole):
    try:
        save_path = _get_path_embed_whole(subj_dir, one_doc_info)
        os.makedirs(
            str(save_path.parents[0]), mode=NEW_DIRS_MODE, exist_ok=True
        )
        np.save(
            save_path,
            np.array(embed_data_whole),
            allow_pickle=False,
        )
        return True
    except Exception as exc:
        log_error("\n".join([
            "cannot save a whole-embed file",
            str(one_doc_info),
            str(exc),
        ]))
        return None


def _save_path_embed_split(subj_dir, one_doc_info, embed_data_split):
    try:
        save_path = _get_path_embed_split(subj_dir, one_doc_info)
        os.makedirs(
            str(save_path.parents[0]), mode=NEW_DIRS_MODE, exist_ok=True
        )
        np.save(
            save_path,
            np.array(embed_data_split),
            allow_pickle=False,
        )
        return True
    except Exception as exc:
        log_error("\n".join([
            "cannot save a split-embed file",
            str(one_doc_info),
            str(exc),
        ]))
        return None


def _get_span_dirs(conf, subject, date_from, date_upto):
    data_root = conf["data"]["storage_dir"]["path"]

    if date_from > date_upto:
        return

    day_delta = dt.timedelta(days=1)
    use_date = date_from
    while use_date <= date_upto:
        dir_path = Path(
            data_root,
            DATA_DIR_DEPO,
            subject,
            use_date.strftime("%Y_%m_%d"),
            SUBDIR_DOCS,
        )
        if dir_path.exists():
            yield dir_path
        use_date += day_delta


def get_doc_vector(conf, doc_subject, doc_date, doc_doi, doc_version, split):
    """
    Provides a stored embedding of a given doc.
    """
    data_root = conf["data"]["storage_dir"]["path"]
    doc_path = None

    for test_path in sorted(list(Path(
        data_root,
        DATA_DIR_DEPO,
        doc_subject,
        doc_date.replace("-", "_"),
        SUBDIR_EMBED_SPLIT if split else SUBDIR_EMBED_WHOLE,
        _get_doc_name(doc_doi, doc_version),
    ).glob(_get_vec_name_pattern(doc_doi))), reverse=True):
        if test_path.is_file():
            doc_path = test_path
            break

    return doc_path


def get_span_docs(conf, subject, date_from, date_upto):
    """
    Provides docs of a given span.
    """
    for use_dir in sorted(
        _get_span_dirs(conf, subject, date_from, date_upto)
    ):
        for doc_path in sorted(Path(use_dir).glob("*__v*.json")):
            with open(doc_path, encoding="utf8") as fh:
                yield json.load(fh)


def assure_document_stored(conf, doc_data):
    """
    Store a given doc into depo if it is not already stored.
    A doc taken from JSON API is resaved if the previously stored
    doc was taken from RSS though.
    """
    data_root = conf["data"]["storage_dir"]["path"]

    doc_path = _get_path_doc(data_root, doc_data)
    doc_dir = doc_path.parents[0]

    if doc_path.exists():
        # if the stored doc is from RSS feeds, it lacks some info,
        # and then it is better to resave it from the JSON API data;
        to_resave = False
        if "type" in doc_data:
            with open(doc_path, encoding="utf8") as fh:
                if "type" not in json.load(fh):
                    to_resave = True
        if not to_resave:
            return True

    try:
        os.makedirs(str(doc_dir), mode=NEW_DIRS_MODE, exist_ok=True)
        with open(doc_path, "w", encoding="utf8") as fh:
            json.dump(doc_data, fh)
        return True
    except Exception as exc:
        log_error("\n".join([
            "cannot save doc data",
            str(doc_path),
            str(exc),
        ]))
        return False


def assure_depo_vectors(conf, date_from, date_upto):
    """
    Make and store both embeddings of a given doc into depo
    if the embeddings are not already stored there.
    """
    encoders = get_encoders(conf, logging=None)
    if not assure_depo_encoding_info(conf, encoders):
        return False

    data_root = conf["data"]["storage_dir"]["path"]
    if encoders is None:
        log_error("cannot get embedders")
        return False

    for subject in conf["feeds"]["subjects"]["list"]:
        time.sleep(API_FEED_TAKE_PAUSE)
        subj_dir = Path(
            data_root,
            DATA_DIR_DEPO,
            subject,
        )
        for one_doc_info in get_span_docs(
            conf, subject, date_from, date_upto
        ):
            path_embed_split = _get_path_embed_split(subj_dir, one_doc_info)
            if not path_embed_split.exists():
                embed_data_split = make_embed_split(
                    encoders,
                    _get_path_doc(data_root, one_doc_info),
                )
                if embed_data_split is not None:
                    if not _save_path_embed_split(
                        subj_dir, one_doc_info, embed_data_split
                    ):
                        log_error("cannot save split-embed data")
                        return False
                else:
                    log_error("cannot make split embedding")
                    return False

            path_embed_whole = _get_path_embed_whole(subj_dir, one_doc_info)
            if not path_embed_whole.exists():
                embed_data_whole = make_embed_whole(
                    encoders,
                    _get_path_doc(data_root, one_doc_info),
                )
                if embed_data_whole is not None:
                    if not _save_path_embed_whole(
                        subj_dir, one_doc_info, embed_data_whole
                    ):
                        log_error("cannot save whole-embed data")
                        return False
                else:
                    log_error("cannot make whole embedding")
                    return False

    return True


def get_doc_embed_whole(subj_dir, one_doc_info):
    """
    Retrieve the already stored whole-doc embedding of a given doc.
    """
    embed_path = _get_path_embed_whole(subj_dir, one_doc_info)
    try:
        return np.load(embed_path, allow_pickle=False)
    except Exception as exc:
        log_error("\n".join([
            "cannot take a whole-embed file",
            str(one_doc_info),
            str(exc),
        ]))
        return None


def get_doc_embed_split(subj_dir, one_doc_info):
    """
    Retrieve the already stored sentence-wise embedding of a given doc.
    """
    embed_path = _get_path_embed_split(subj_dir, one_doc_info)
    try:
        return np.load(embed_path, allow_pickle=False)
    except Exception as exc:
        log_error("\n".join([
            "cannot take a split-embed file",
            str(one_doc_info),
            str(embed_path),
            str(exc),
        ]))
        return None


def get_doc_embed_split_count(subj_dir, one_doc_info):
    """
    Retrieve the count of sentences of an already stored sentence-wise
    embedding of a given doc.
    """
    embed_data = get_doc_embed_split(subj_dir, one_doc_info)
    if embed_data is None:
        return None
    try:
        return len(list(embed_data))
    except Exception as exc:
        log_error("\n".join([
            "cannot take length of parts of a split-embed data",
            str(one_doc_info),
            str(exc),
        ]))
        return None


def assure_document_suite_stored(
    conf,
    subject,
    current_dt,
    doc_data,
    split_embed_blob,
    whole_embed_blob,
    encoders,
):
    """
    Store a given doc and its both embeddings if they are not already stored.
    """
    if not assure_depo_encoding_info(conf, encoders):
        return False

    max_doc_age = dt.timedelta(days=(conf["data"]["depo_depth"] + 1))
    data_root = conf["data"]["storage_dir"]["path"]
    subject = subject.replace(" ", "_")
    if subject not in conf["feeds"]["subjects"]["list"]:
        log_warning("\n".join([
            f"not saving a doc of an unsupported subject: {subject}",
            doc_data,
        ]))
    try:
        for key in ["title", "abstract", "doi", "date"]:
            if key not in doc_data:
                log_error("\n".join([
                    f"required key '{key}' not present in doc data",
                    str(doc_data),
                ]))
                return False

        if max_doc_age < (
            current_dt - dt.datetime.strptime(
                doc_data["date"],
                "%Y-%m-%d",
            ).replace(tzinfo=dt.timezone.utc)
        ):
            return True

        if doc_data["doi"].startswith(DOI_PREFIX):
            doc_data["doi"] = doc_data["doi"][len(DOI_PREFIX):]
        _check_doi_safe(doc_data["doi"])

        if "version" not in doc_data:
            doc_data["version"] = "1"
        doc_data["category"] = subject

        doc_path = _get_path_doc(data_root, doc_data)
        if not doc_path.exists():
            os.makedirs(
                str(doc_path.parents[0]),
                mode=NEW_DIRS_MODE,
                exist_ok=True,
            )
            with open(doc_path, "w", encoding="utf8") as fh:
                json.dump(doc_data, fh)

        subj_dir = _get_subj_dir(data_root, subject)

        embed_split_path = _get_path_embed_split(subj_dir, doc_data)
        if not embed_split_path.exists():
            os.makedirs(
                str(embed_split_path.parents[0]),
                mode=NEW_DIRS_MODE,
                exist_ok=True,
            )
            with open(embed_split_path, "wb") as fh:
                fh.write(split_embed_blob)

        embed_whole_path = _get_path_embed_whole(subj_dir, doc_data)
        if not embed_whole_path.exists():
            os.makedirs(
                str(embed_whole_path.parents[0]),
                mode=NEW_DIRS_MODE,
                exist_ok=True,
            )
            with open(embed_whole_path, "wb") as fh:
                fh.write(whole_embed_blob)
    except Exception as exc:
        log_error("\n".join([
            "error during assuring a doc being stored in depo",
            str(exc),
        ]))
        return False

    return True


def get_one_doc_path(data_root, doc_data):
    """
    Provides path to a given doc.
    """
    return _get_path_doc(data_root, doc_data)


def get_one_doc_data(data_root, doc_data):
    """
    Provides doc data of a given doc.
    """
    doc_path = _get_path_doc(data_root, doc_data)
    try:
        with open(doc_path, encoding="utf8") as fh:
            return json.load(fh)
    except Exception as exc:
        log_error("\n".join([
            "cannot load a doc file",
            str(doc_data),
            str(exc),
        ]))
        return None
