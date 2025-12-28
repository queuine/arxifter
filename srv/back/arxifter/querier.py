#!/usr/bin/env python
"""
The querying of LLMs.
"""

from llama_index.core import PromptTemplate
from llama_index.llms.openai import OpenAI


def _get_querier_llm_obj(conf, api_key):
    return OpenAI(
        model=conf["llms"]["model_name"],
        api_key=api_key,
    )


def _get_llm_qa_template(conf, argued=True):
    return PromptTemplate(
        conf["prompts"]["explained" if argued else "plain"]["content"]
    )


async def exec_query(conf, index, question, argued, api_key):
    """
    Queries an LLM and returns its answer.
    It requires to have all the query components already prepared;
    those components are:
    * loaded embedded feeds (as a parameter),
    * user question on the feeds (as a parameter),
    * prompt to the LLM:
      * prompts are within the loaded configuration,
      * and the used prompt is taken according to the "argued" parameter,
    * API key.
    """
    query_engine = index.as_query_engine(
        llm=_get_querier_llm_obj(conf, api_key),
        similarity_top_k=conf["llms"]["query_top_count"],
    )
    prompt_template = _get_llm_qa_template(conf, argued)
    query_engine.update_prompts({
        "response_synthesizer:text_qa_template": prompt_template
    })

    res = await query_engine.aquery(question)
    return res
