#!/usr/bin/env python
"""
Makes the embeddings from docs data.
"""

import json

import spacy

from ..logging import (
    log_error,
)


def make_embed_split(encoders, doc_path):
    """
    Makes static embeddings of doc sentences.
    """
    try:
        with open(doc_path, encoding="utf8") as fh:
            doc = json.load(fh)
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
        sentences = [doc["title"]] + [
            str(item) for item in nlp(doc["abstract"]).sents
        ]
        return encoders["static"]["method"](sentences)
    except Exception as exc:
        log_error("\n".join([
            "could not split-embed a doc",
            str(doc_path),
            str(exc),
        ]))
        return None


def make_embed_whole(encoders, doc_path):
    """
    Makes dense embeddings of whole docs.
    """
    try:
        with open(doc_path, encoding="utf8") as fh:
            doc = json.load(fh)
        return encoders["dense"]["method"](
            "\n".join([
                "title: " + doc["title"],
                "abstract: " + doc["abstract"],
            ]),
            is_query=False,
        )
    except Exception as exc:
        log_error("\n".join([
            "could not whole-embed a doc",
            str(doc_path),
            str(exc),
        ]))
        return None
