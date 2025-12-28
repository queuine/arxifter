#!/usr/bin/env python
"""
Usage of the embedded feeds.
It is active when ingested feeds are used for answering user questions.
"""

import os, json

from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

from .setting import (
    EMBED_MODEL_NAME_KEY,
    INFO_FILE_NAME,
)


def _get_used_embed_model_name(data_dir):
    try:
        with open(
            os.path.join(data_dir, INFO_FILE_NAME),
            encoding="utf8",
        ) as fh:
            model_name = json.load(fh)[EMBED_MODEL_NAME_KEY]
    except Exception:
        model_name = None

    return model_name


def _get_loader_embed_model_obj(conf, data_dir, api_key):
    embed_model_name = _get_used_embed_model_name(data_dir)
    if embed_model_name is None:
        return None

    return OpenAIEmbedding(
        model=embed_model_name,
        api_key=api_key,
        embed_batch_size=conf["llms"]["embed_batch_size"],
    )


def load_index(conf, data_dir, embed_dir, api_key):
    """
    Provides the embedded feeds.
    """
    embed_model_obj = _get_loader_embed_model_obj(conf, data_dir, api_key)
    if embed_model_obj is None:
        return None

    storage_context = StorageContext.from_defaults(
        docstore=SimpleDocumentStore.from_persist_dir(
            persist_dir=embed_dir
        ),
        vector_store=SimpleVectorStore.from_persist_dir(
            persist_dir=embed_dir
        ),
        index_store=SimpleIndexStore.from_persist_dir(
            persist_dir=embed_dir
        ),
    )
    embed_index = load_index_from_storage(
        storage_context,
        embed_model=embed_model_obj
    )
    return embed_index
