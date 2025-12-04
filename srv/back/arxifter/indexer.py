#!/usr/bin/env python

import os

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

from .setting import DOCUMENTS_SUBDIR, VECTORS_SUBDIR
from .setting import get_llm_settings_obj


def index_docs(base_path):
    Settings = get_llm_settings_obj()

    documents = SimpleDirectoryReader(
        os.path.join(base_path, DOCUMENTS_SUBDIR)).load_data()
    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=Settings.embed_model,
    )
    index.storage_context.persist(
        os.path.join(base_path, VECTORS_SUBDIR),
    )

    return True
