#!/usr/bin/env python
"""
Actions on the database that holds basic properties of individual docs.
It is used e.g. for connecting together doc ids with their basic info,
with that being used for doc locating within the depo directory.
"""

from pathlib import Path
import sqlite3

from .setting import (
    DOC_NAMING_DB,
)
from ..logging import (
    log_error,
)

CREATE_TABLE_COMMAND = """
    CREATE TABLE IF NOT EXISTS articles_names(
        id INTEGER PRIMARY KEY,
        doi TEXT UNIQUE NOT NULL,
        date TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        parts INTEGER NOT NULL DEFAULT 1
    ) WITHOUT ROWID, STRICT
"""

INSERT_COMMAND = """
    INSERT INTO articles_names(
        id,
        doi,
        date,
        version
    )
    VALUES (
        coalesce((SELECT max(id) FROM articles_names), 0) + 1,
        :doi,
        :date,
        :version
    )
    ON CONFLICT (doi) DO UPDATE SET
        date = excluded.date,
        version = excluded.version
    WHERE excluded.version > articles_names.version
    RETURNING id
"""

UPDATE_DOC_PARTS_COUNT_COMMAND = """
    UPDATE articles_names SET parts = :parts WHERE id = :id
"""

SELECT_COUNT_PARTS_COMMAND = """
    SELECT sum(parts) FROM articles_names
"""

SELECT_COUNT_DOCS_COMMAND = """
    SELECT count(id) FROM articles_names
"""

SELECT_DOCS_INFO_COMMAND = """
    SELECT id, doi, date, version, parts
    FROM articles_names ORDER BY id ASC
"""

SELECT_DOC_SET_INFO_COMMAND = """
    SELECT id, doi, date, version
    FROM articles_names
    WHERE id in (qm_list)
    ORDER BY id ASC
"""

SELECT_ONE_DOC_INFO_COMMAND = """
    SELECT id, doi, date, version
    FROM articles_names
    WHERE id = :id
"""


def _db_action(
    subj_dir, command, params, fetch_some, fetch_all, output_dict=False
):
    db_path = Path(
        subj_dir,
        DOC_NAMING_DB,
    )
    try:
        with sqlite3.connect(db_path, autocommit=True) as con:
            if output_dict:
                con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(command, params)
            if not fetch_some:
                return [True, None]
            if not fetch_all:
                return [True, cur.fetchone()]
            return [True, cur.fetchall()]
    except Exception as exc:
        log_error("\n".join([
            "could not do an action on the naming db",
            str(db_path),
            str(command),
            str(params),
            str(exc),
        ]))
        return [False, None]


def prepare_doc_naming(subj_dir):
    """
    Makes the database for basic doc info.
    """
    status, _ = _db_action(
        subj_dir,
        command=CREATE_TABLE_COMMAND,
        params={},
        fetch_some=False,
        fetch_all=False,
    )
    if not status:
        log_error("could not create sqlite db for doc naming")
    return status


def set_doc_rank(subj_dir, doc):
    """
    Sets doc id of a given doc.
    """
    status, output = _db_action(
        subj_dir,
        command=INSERT_COMMAND,
        params={
            "doi": doc["doi"],
            "date": doc["date"],
            "version": doc["version"],
        },
        fetch_some=True,
        fetch_all=False,
    )
    if not status:
        log_error("could not insert an article info into the naming db")
    return [
        status,
        output[0] if output is not None else output
    ]


def set_doc_parts_count(subj_dir, doc_id, count):
    """
    Stores the sentence count of a given doc.
    """
    status, _ = _db_action(
        subj_dir,
        command=UPDATE_DOC_PARTS_COUNT_COMMAND,
        params={
            "id": doc_id,
            "parts": count,
        },
        fetch_some=False,
        fetch_all=False,
    )
    if not status:
        log_error("could not set doc parts count for a doc")
    return status


def get_span_parts_count(subj_dir):
    """
    Gets overall count of doc sentences of docs within a given span.
    """
    status, output = _db_action(
        subj_dir,
        command=SELECT_COUNT_PARTS_COMMAND,
        params={},
        fetch_some=True,
        fetch_all=False,
    )
    if not status:
        log_error("could not read the parts count from the naming db")
    return [
        status,
        output[0] if (status and (output is not None)) else output
    ]


def get_span_docs_count(subj_dir):
    """
    Gets overall count of docs of docs within a given span.
    """
    status, output = _db_action(
        subj_dir,
        command=SELECT_COUNT_DOCS_COMMAND,
        params={},
        fetch_some=True,
        fetch_all=False,
    )
    if not status:
        log_error("could not read the docs count from the naming db")
    return [
        status,
        output[0] if (status and (output is not None)) else output
    ]


def get_span_docs_info(subj_dir):
    """
    Gets doc infos of all the docs within a given span.
    """
    status, output = _db_action(
        subj_dir,
        command=SELECT_DOCS_INFO_COMMAND,
        params={},
        fetch_some=True,
        fetch_all=True,
        output_dict=True,
    )
    if not status:
        log_error("could not read the docs info set from the naming db")
    return [status, output]


def get_one_doc_info(subj_dir, doc_id):
    """
    Gets doc info of the doc of a given doc id.
    """
    status, output = _db_action(
        subj_dir,
        command=SELECT_ONE_DOC_INFO_COMMAND,
        params={"id": doc_id},
        fetch_some=True,
        fetch_all=False,
        output_dict=True,
    )
    if not status:
        log_error("could not read the asked-for doc info from the naming db")
    return [status, dict(output)]


def get_set_doc_info(subj_dir, id_list):
    """
    Gets doc infos of the docs of a given doc id list.
    """
    status, output = _db_action(
        subj_dir,
        command=SELECT_DOC_SET_INFO_COMMAND.replace(
            "qm_list", ", ".join(["?"] * len(id_list))
        ),
        params=id_list,
        fetch_some=True,
        fetch_all=True,
        output_dict=True,
    )
    if not status:
        log_error("could not read the sought doc info set from the naming db")
    return [status, [dict(item) for item in output]]
