#!/usr/bin/env python

import os
from pathlib import Path

LLM_DEBUGGING = True
DOCUMENTS_SUBDIR = "docs"
VECTORS_SUBDIR = "vecs"
LLM_MODEL_NAME = "gpt-5-nano"
LLM_EMBED_BATCH_SIZE = 100
LLM_QUERY_TOP_COUNT = 5
LLM_KEY_FILE_NAME = "llm_key.txt"


def set_llm_key(keys_dir):
    key_string = Path(
        os.path.join(keys_dir, LLM_KEY_FILE_NAME)
    ).read_text(encoding="utf8").strip()

    os.environ["OPENAI_API_KEY"] = key_string


def get_llm_settings_obj():
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI
    from llama_index.core import Settings

    Settings.embed_model = OpenAIEmbedding(
        embed_batch_size=LLM_EMBED_BATCH_SIZE)
    Settings.llm = OpenAI(model=LLM_MODEL_NAME)

    return Settings


def get_llm_qa_template():
    from llama_index.core import PromptTemplate

    new_qa_template_str = (
        'You are a top-tier expert biological system that helps scientists '
        'to keep their knowledge up-to-date '
        'by analyzing a set of provided articles.\n'
        'The articles are below.\n'
        '---------------------\n'
        '{context_str}\n'
        '---------------------\n'
        'Given the articles and not prior knowledge, '
        'answer the query with always returning '
        'the doi and title parts of the relevant articles '
        'along with the reasons for selecting those individual articles.\n'
        'You can add other information if the query aks for it explicitly.\n'
        'Provide the answer as a JSON list, '
        'so that it is easy to put it on web.\n'
        'Query: {query_str}\n'
        'Answer: '
    )

    return PromptTemplate(new_qa_template_str)
