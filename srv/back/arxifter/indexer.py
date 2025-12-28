#!/usr/bin/env python
"""
Preparation of embedded feeds as vectors; that via an LLM action.
It is active during the stage when RSS feeds are downloaded and ingested.
"""

import os, time

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.openai import OpenAIEmbedding

from .setting import (
    DOCUMENTS_FOR_VECTORS_SUBDIR,
    VECTORS_SUBDIR,
    ATTEMPT_COUNT_INDEX,
    VEC_FEED_INDEX_SLEEP,
)
from .logging import log_error
from .keys import get_llm_key_indexer


def _get_indexer_embed_model_obj(conf):
    return OpenAIEmbedding(
        model=conf["llms"]["embed_model_name"],
        embed_batch_size=conf["llms"]["embed_batch_size"],
        api_key=get_llm_key_indexer(conf),
    )


def index_docs(conf, base_path):
    """
    Does the RSS embedding via:
    * reading the saved docs previously made from RSS feeds,
    * putting the docs to LLM,
    * saving the embedded data along the original docs.
    """
    got_indexed = False
    for attempt in range(ATTEMPT_COUNT_INDEX):
        time.sleep(attempt * VEC_FEED_INDEX_SLEEP)
        try:
            documents = SimpleDirectoryReader(
                os.path.join(base_path, DOCUMENTS_FOR_VECTORS_SUBDIR)
            ).load_data()
            index = VectorStoreIndex.from_documents(
                documents,
                embed_model=_get_indexer_embed_model_obj(conf)
            )
            index.storage_context.persist(
                os.path.join(base_path, VECTORS_SUBDIR),
            )
            got_indexed = True
            break
        except Exception as exc:
            got_indexed = False
            log_error("error during feed indexing:\n" + str(exc))

    return got_indexed
