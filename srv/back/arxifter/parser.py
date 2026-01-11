#!/usr/bin/env python
"""
Making JSON docs out of RSS feeds.
"""

import os, json

import feedparser

from .setting import (
    NEW_DIRS_MODE,
    DOCUMENTS_SUBDIR,
    DOCUMENTS_FOR_VECTORS_SUBDIR,
    BIORXIV_FEED_MINIMAL_SIZE,
    BIORXIV_DOI_START,
    BIORXIV_DOI_ENDS,
    ARTICLE_KEY_RANK,
)
from .logging import log_error
from .utils import (
    get_doc_name,
    replace_marks,
)


def _get_link(entry):
    link_val = None
    for key in ["link", "id"]:
        try:
            link_val = str(entry[key]).strip()
            if not link_val.startswith("http"):
                link_val = ""
            if link_val != "":
                break
        except Exception:
            link_val = None

    if link_val == "":
        link_val = None

    return link_val


def _get_doi(entry, link):
    doi_val = None
    try:
        doi_val = str(entry["dc_identifier"]).strip()
        if doi_val == "":
            doi_val = None
    except Exception:
        doi_val = None

    if (doi_val is None) and (link is not None):
        doi_start = link.find(BIORXIV_DOI_START)
        if doi_start > -1:
            doi_val = link[doi_start:].strip()
            for suffix in BIORXIV_DOI_ENDS:
                doi_end = doi_val.find(suffix)
                if doi_end > -1:
                    doi_val = doi_val[:doi_end]
            doi_val = doi_val.strip()
        if doi_val == "":
            doi_val = None
        else:
            doi_val = "doi:" + doi_val

    return doi_val


def _get_date(entry):
    date_val = None
    for key in ["updated", "prism_publicationdate"]:
        try:
            date_val = str(entry[key]).strip()
            if date_val != "":
                break
        except Exception:
            date_val = None

    if date_val == "":
        date_val = None

    return date_val


def _get_title(entry):
    title_val = None
    try:
        title_val = replace_marks(str(entry["title"]).strip())
    except Exception:
        title_val = None

    if title_val == "":
        title_val = None

    return title_val


def _get_authors(entry):
    authors_val = None
    try:
        authors_val = " ".join([
            str(item.name) for item in entry["authors"]
        ]).strip()
        if authors_val == "":
            authors_val = None
    except Exception:
        authors_val = None

    if authors_val is None:
        try:
            authors_val = str(entry["author"]).strip()
            if authors_val == "":
                authors_val = None
        except Exception:
            authors_val = None

    return authors_val


def _get_abstract(entry):
    abstract_val = None
    for key in ["description", "summary"]:
        try:
            abstract_val = replace_marks(str(entry[key]).strip())
            if abstract_val != "":
                break
        except Exception:
            abstract_val = None

    if abstract_val == "":
        abstract_val = None

    return abstract_val


def parse_feed_save_docs(source):
    """
    Parses and saves an already downloaded feed.
    It saves them in two versions:
    * for presenting to users,
    * for indexing by LLMs.
    """
    feed = None
    try:
        feed = feedparser.parse(source)
    except Exception as exc:
        log_error("\n".join([
            "could not parse a feed:",
            str(source),
            str(exc),
        ]))
        return False

    feed_ents = None
    try:
        feed_ents = feed["entries"]
    except Exception as exc:
        log_error("\n".join([
            "could not take entries from a parsed feed:",
            str(source),
            str(exc),
        ]))
        return False

    work_dir = os.path.dirname(source)
    docs_dir_orig = os.path.join(work_dir, DOCUMENTS_SUBDIR)
    docs_dir_prep = os.path.join(work_dir, DOCUMENTS_FOR_VECTORS_SUBDIR)

    try:
        os.makedirs(docs_dir_orig, mode=NEW_DIRS_MODE, exist_ok=True)
        os.makedirs(docs_dir_prep, mode=NEW_DIRS_MODE, exist_ok=True)
    except Exception as exc:
        log_error("\n".join([
            "could not prepare dirs to save docs made out of a feed:",
            str(docs_dir_orig),
            str(docs_dir_prep),
            str(exc),
        ]))
        return False

    ind = 0
    parsed_count = 0
    for entry in feed_ents:
        ind += 1

        doc_name = get_doc_name(ind)
        doc_path_orig = os.path.join(docs_dir_orig, doc_name)
        doc_path_prep = os.path.join(docs_dir_prep, doc_name)

        # "title" and "abstract" are required here,
        # the other items are optional;
        art_link = _get_link(entry)
        art_doi = _get_doi(entry, art_link)
        art_date = _get_date(entry)
        art_title = _get_title(entry)
        art_authors = _get_authors(entry)
        art_abstract = _get_abstract(entry)

        if (art_title is None) or (art_abstract is None):
            log_error("\n".join([
                "article metadata lack required parts",
                f"article: {ind} (indexing is from 1)",
                str(source),
            ]))
            continue

        art_reg = {}
        for key, val in [
            ["link", art_link],
            ["doi", art_doi],
            ["date", art_date],
            ["title", art_title],
            ["authors", art_authors],
            ["abstract", art_abstract],
        ]:
            if val is not None:
                art_reg[key] = val

        try:
            with open(doc_path_orig, "w", encoding="utf8") as fh:
                fh.write(json.dumps(art_reg))
        except Exception as exc:
            log_error("\n".join([
                "could not save a doc made out of a feed:",
                str(doc_path_orig),
                str(exc),
            ]))
            continue

        try:
            with open(doc_path_prep, "w", encoding="utf8") as fh:
                fh.write(json.dumps({
                    ARTICLE_KEY_RANK: ind,
                    "title": art_title,
                    "abstract": art_abstract,
                }))
        except Exception as exc:
            log_error("\n".join([
                "could not save a doc made out of a feed:",
                str(doc_path_prep),
                str(exc),
            ]))
            continue

        parsed_count += 1

    if parsed_count < BIORXIV_FEED_MINIMAL_SIZE:
        log_error("\n".join([
            f"too low count ({parsed_count}) of docs taken out of feed",
            str(source),
        ]))
        return False

    return True
