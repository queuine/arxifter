#!/usr/bin/env python

from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore

from .setting import get_llm_settings_obj


def load_index(storage_dir):
    global Settings
    Settings = get_llm_settings_obj()

    storage_context = StorageContext.from_defaults(
        docstore=SimpleDocumentStore.from_persist_dir(
            persist_dir=storage_dir
        ),
        vector_store=SimpleVectorStore.from_persist_dir(
            persist_dir=storage_dir
        ),
        index_store=SimpleIndexStore.from_persist_dir(
            persist_dir=storage_dir
        ),
    )

    return load_index_from_storage(storage_context)
