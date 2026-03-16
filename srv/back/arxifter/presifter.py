#!/usr/bin/env python
"""
High-level management of presifiting processes.
"""

import asyncio, functools

from .setting import (
    PRESIFT_LAST_COUNT,
    PRESIFT_LAST_DAYS,
)
from .utils import (
    get_current_data_dir,
)
from .loader import (
    presift_docs,
)
from .spans.utils import (
    get_last_data_dir,
)
from .spans.loader import (
    presift_docs_last,
)


async def _get_similar_last_count(
    conf, executor, get_logger, logger, encoders, base_subjects, query_text
):
    similar_articles = None
    data_dir = None
    try:
        data_dir = get_current_data_dir(conf)
        if data_dir is None:
            raise OSError("no embedded feeds are availabble")
    except Exception as exc:
        logger.error(f"could not take the data-dir: {str(exc)}")
        data_dir = None
    if data_dir is None:
        return {
            "data_dir": None,
            "similar_articles": None,
        }

    try:
        loop = asyncio.get_event_loop()
        similar_articles = await loop.run_in_executor(
            executor,
            functools.partial(
                presift_docs,
                conf=conf,
                encoders=encoders,
                data_dir=data_dir,
                base_subjects=base_subjects,
                query=query_text,
                get_logger=get_logger,
            )
        )
        if similar_articles is None:
            raise OSError("could not load the similar articles")
    except Exception as exc:
        logger.error(
            f"taking similar articles (last counts) failed: {str(exc)}"
        )
        similar_articles = None

    return {
        "data_dir": data_dir,
        "similar_articles": similar_articles,
    }


async def _get_similar_last_days(
    conf, executor, get_logger, logger, encoders, base_subjects, query_text
):
    similar_articles = None
    data_dir = None
    try:
        data_dir = get_last_data_dir(conf)
        if data_dir is None:
            raise OSError("no embedded feeds are availabble")
    except Exception as exc:
        logger.error(f"could not take the data-dir: {str(exc)}")
        data_dir = None
    if data_dir is None:
        return {
            "data_dir": None,
            "similar_articles": None,
        }

    try:
        loop = asyncio.get_event_loop()
        similar_articles = await loop.run_in_executor(
            executor,
            functools.partial(
                presift_docs_last,
                conf=conf,
                encoders=encoders,
                data_dir=data_dir,
                base_subjects=base_subjects,
                query=query_text,
                get_logger=get_logger,
            )
        )
        if similar_articles is None:
            raise OSError("could not load the similar articles")
    except Exception as exc:
        logger.error(
            f"taking similar articles (last days) failed: {str(exc)}"
        )
        similar_articles = None

    return {
        "data_dir": data_dir,
        "similar_articles": similar_articles,
    }


async def conduct_presift(
    conf,
    executor,
    get_logger,
    presift_type,
    encoders,
    base_subjects,
    query_text
):
    """
    Provides presifting of the currently implemented feed types.
    """
    logger = get_logger(__name__)

    try:
        if presift_type == PRESIFT_LAST_COUNT:
            return await _get_similar_last_count(
                conf,
                executor,
                get_logger,
                logger,
                encoders,
                base_subjects,
                query_text
            )
    except Exception as exc:
        logger.error("\n".join([
            f"presifting of the '{PRESIFT_LAST_COUNT}' type failed",
            str(exc),
        ]))
        return None

    try:
        if presift_type == PRESIFT_LAST_DAYS:
            return await _get_similar_last_days(
                conf,
                executor,
                get_logger,
                logger,
                encoders,
                base_subjects,
                query_text,
            )
    except Exception as exc:
        logger.error("\n".join([
            f"presifting of the '{PRESIFT_LAST_DAYS}' type failed",
            str(exc),
        ]))
        return None

    logger.error(f"unknown presift type: '{presift_type}'")
    return None
