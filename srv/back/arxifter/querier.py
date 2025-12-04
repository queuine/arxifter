#!/usr/bin/env python

from .setting import get_llm_settings_obj
from .setting import get_llm_qa_template
from .setting import LLM_QUERY_TOP_COUNT


def make_query(index, question):
    Settings = get_llm_settings_obj()

    query_engine = index.as_query_engine(
        llm=Settings.llm,
        similarity_top_k=LLM_QUERY_TOP_COUNT,
    )
    query_engine.update_prompts({
        "response_synthesizer:text_qa_template": get_llm_qa_template()
    })

    return query_engine.query(question)
