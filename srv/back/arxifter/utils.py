#!/usr/bin/env python
"""
Assorted auxiliary functions.
"""

import os, re
from pathlib import Path
from urllib.parse import urlparse

from .setting import (
    RSS_FEED_URL_BASE,
    ACTIVE_DATA_DIR_LISTING,
    DATA_DIR_PERM,
    DATA_DIR_CURR,
    ATTEMPT_COUNT_DATA_DIR,
    FEED_REPLS_ENT_SHORT,
    FEED_MATCH_ENT_SHORT,
    FEED_MATCH_ENT,
    FEED_REPLS_ENT,
    FEED_MATCH_ONOFF,
    FEED_IMPUT_ONOFF,
    FEED_IMPUT_SYMS_SUP,
    FEED_MATCH_SYMS_SUP,
    FEED_MATCH_SYMS,
    FEED_REPLS_SYMS,
)


def _replace_marks_ent_short(match_obj):
    return "".join([
        FEED_REPLS_ENT_SHORT[match_obj.group(1)],
    ])


def _replace_marks_ent(match_obj):
    return "".join([
        match_obj.group(1),
        FEED_REPLS_ENT[match_obj.group(2)],
        match_obj.group(3),
    ])


def _replace_marks_onoff(match_obj):
    return "".join([
        match_obj.group(1),
        FEED_IMPUT_ONOFF,
        match_obj.group(2),
    ])


def _replace_marks_syms_sup(match_obj):
    return "".join([
        FEED_IMPUT_SYMS_SUP,
        match_obj.group(1),
    ])


def _replace_marks_syms(match_obj):
    return "".join([
        FEED_REPLS_SYMS[match_obj.group(1)],
    ])


def replace_marks(text):
    """
    Text parts of feeds contain some marks in strange forms.
    This function tries to turn them to more reasonable forms.
    """
    for pattern, replacer in [
        [FEED_MATCH_ENT_SHORT, _replace_marks_ent_short],
        [FEED_MATCH_ENT, _replace_marks_ent],
        [FEED_MATCH_ONOFF, _replace_marks_onoff],
        [FEED_MATCH_SYMS_SUP, _replace_marks_syms_sup],
        [FEED_MATCH_SYMS, _replace_marks_syms],
    ]:
        text = re.sub(pattern, replacer, text)

    return text


def list_stored_data_dirs(conf, years_only=False):
    """
    The directories where the batches of ingested feeds are stored.
    """
    data_dir_stored = os.path.join(
        conf["data"]["storage_dir"]["path"],
        DATA_DIR_PERM,
    )
    for item_year in sorted(Path(data_dir_stored).glob("*"), reverse=True):
        if not item_year.is_dir():
            continue
        if years_only:
            yield item_year
            continue
        for item_day in sorted(item_year.glob("*"), reverse=True):
            if not item_day.is_dir():
                continue
            yield item_day


def list_active_data_dir(conf):
    """
    The directories that are prepared to be used for loading ingested feeds.
    Each such directory corresponds to one batch of the feeds.
    """
    data_dir_curr = os.path.join(
        conf["data"]["storage_dir"]["path"],
        DATA_DIR_CURR,
    )
    for item in sorted(Path(data_dir_curr).glob("*"), reverse=True):
        if not item.is_dir():
            continue
        if re.match(ACTIVE_DATA_DIR_LISTING, item.parts[-1]) is None:
            continue
        yield item


def get_current_data_dir(conf):
    """
    Directory to be used as the current batch of ingested feeds.
    """
    dir_path = None
    for _ in range(ATTEMPT_COUNT_DATA_DIR):
        try:
            dir_test = None
            for item in list_active_data_dir(conf):
                dir_test = str(item)
                break
            if dir_test is not None:
                dir_test = str(Path(dir_test).resolve())
                if Path(dir_test).exists():
                    dir_path = dir_test
        except Exception:
            dir_path = None
        if dir_path is not None:
            break
    return dir_path


def origin_spec_to_parts(origin_spec):
    """
    Preparation for checking web clients.
    """
    if origin_spec == "":
        return None
    origin_spec_parts = urlparse(origin_spec)
    origin_parts = {
        "scheme": origin_spec_parts.scheme,
        "hostname": origin_spec_parts.hostname,
        "port": origin_spec_parts.port,
    }
    if origin_parts["port"] is None:
        origin_parts["port"] = (
            80 if origin_parts["scheme"] == "http" else 443
        )
    return origin_parts


def subject_spec_to_fs_name(subject_spec):
    """
    Making filesystem-friendly names from subject specifiers.
    The main point is that subjects can be combined,
    and then the respective specifiers contain the + (plus) sign.
    It is not within the "Portable Filename Character Set" though.
    """
    return subject_spec.replace("+", "-")


def subject_spec_to_feed_url(subject_spec):
    """
    Subject specs that are combinations of individual subjects,
    e.g. "genomics+bioinformatics", contain + (the plus sign).
    It is not clear whether biorxiv servers expect that the plus sign
    gets URL encoded or not; by now both ways work.
    Taking it directly with the plus sign for now.
    The encoded way would be with: urllib.parse.quote(subject_spec)
    """
    return RSS_FEED_URL_BASE + subject_spec


def get_doc_name(rank):
    """
    Name of a JSON doc with data from an entry of a RSS feed.
    """
    return str(rank).zfill(3) + ".json"
