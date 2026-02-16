#!/usr/bin/env python
"""
Assorted auxiliary functions.
"""

import os, json, re
import ipaddress as ip
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
    FEED_MATCH_LISTS,
    FEED_FLANK_LISTS,
    INFO_FILE_NAME,
    STATIC_EMBED_MODEL_NAME_KEY,
    DENSE_EMBED_MODEL_NAME_KEY,
    ENV_HF_MUTE,
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


def _replace_marks_lists(match_obj):
    flanks = FEED_FLANK_LISTS.get(match_obj.group(1), ["", ""])
    return "".join([
        flanks[0],
        match_obj.group(2),
        flanks[1],
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
        [FEED_MATCH_LISTS, _replace_marks_lists],
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


def subject_spec_to_base_subjects(subject_spec):
    """
    Splitting subject specifiers into base subjects.
    Article storage is currently by base subjects only,
    and that even for feeds that are based on combinations of subjects.
    The combination-defining character is the "+" sign.
    """
    return subject_spec.split("+")


def subject_spec_to_feed_url(subject_spec):
    """
    Subject specs that are combinations of individual subjects,
    e.g. "genomics+bioinformatics", contain + (the plus sign).
    It is not clear whether biorxiv servers expect that the plus sign
    gets URL encoded or not; by now both ways work.
    Taking it directly with the plus sign for now.
    The encoded way would be with: urllib.parse.quote(subject_spec)
    Since the current way does the ingest and storing via base subjects only,
    it does not matter whether the plus sign should (not) get encoded.
    """
    return RSS_FEED_URL_BASE + subject_spec


def get_doc_name(rank):
    """
    Name of a JSON doc with data from an entry of a RSS feed.
    """
    return str(rank).zfill(3) + ".json"


def check_encoders_info(encoders_info, encoders):
    """
    Checks whether encoder names are the same for a given info
    (that was read from a previously saved info file)
    and currently loaded encoders.
    """
    for info_key, enc_key in [
        [STATIC_EMBED_MODEL_NAME_KEY, "static"],
        [DENSE_EMBED_MODEL_NAME_KEY, "dense"],
    ]:
        if encoders_info[info_key] != encoders[enc_key]["name"]:
            return False

    return True


def load_encoders_info(data_dir):
    """
    Loads the names of the encoders used at a feed ingest.
    """
    encoders_info = {}
    file_path = os.path.join(
        data_dir,
        INFO_FILE_NAME,
    )
    try:
        with open(file_path, encoding="utf8") as fh:
            encoders_info = json.load(fh)
            if type(encoders_info) is not dict:
                encoders_info = {}
    except Exception:
        encoders_info = {}

    for key in [
        STATIC_EMBED_MODEL_NAME_KEY,
        DENSE_EMBED_MODEL_NAME_KEY
    ]:
        if key not in encoders_info:
            encoders_info[key] = None

    return encoders_info


def save_encoders_info(data_dir, encoders):
    """
    Saves the names of the encoders used during a feed ingest.
    """
    file_path = os.path.join(
        data_dir,
        INFO_FILE_NAME,
    )
    encoders_info = {
        STATIC_EMBED_MODEL_NAME_KEY: encoders["static"]["name"],
        DENSE_EMBED_MODEL_NAME_KEY: encoders["dense"]["name"],
    }
    try:
        with open(file_path, "w", encoding="utf8") as fh:
            json.dump(encoders_info, fh)
        info_written = True
    except Exception:
        info_written = False

    return info_written


def mute_hf():
    """
    Makes the use of HF purely local.
    """
    for env_key in ENV_HF_MUTE:
        os.environ[env_key] = "1"


def take_access_list(conf_access_part, require_all_lines, logging_action):
    """
    Reads IP ranges from the provided access file and sets it to it.
    Time of last modification time of the file is read/saved too.
    """
    without_errors = True
    read_list = []
    last_read_time = 0
    try:
        last_read_time = os.path.getmtime(conf_access_part["path"])
        with open(conf_access_part["path"], encoding="utf8") as fh:
            for line in fh:
                line = line.strip()
                if (
                    (line == "")
                    or line.startswith("#")
                ):
                    continue
                try:
                    access_range = ip.ip_network(line, strict=False)
                    read_list.append(access_range)
                except Exception as exc:
                    logging_action("\n".join([
                        "cannot read an access specification line:",
                        conf_access_part["path"],
                        line,
                        str(exc),
                    ]))
                    if require_all_lines:
                        without_errors = False
                        break
    except Exception as exc:
        without_errors = False
        logging_action("\n".join([
            "cannot read an access specification file:",
            conf_access_part["path"],
            str(exc),
        ]))

    if without_errors:
        conf_access_part["list"] = read_list
        conf_access_part["read"] = last_read_time

    return without_errors


def is_access_ok(conf, client_ip, is_guest, logging_action):
    """
    Checks whether a client is allowed for arxifter actions.
    The checking is based on the IP address of the client.
    The used checking lists get reread if the respective files
    have changed since the last time of their reading.
    """
    client_ip_address = ip.ip_address(client_ip)
    prefix = "guest" if is_guest else "user"

    # first, checking the respective allow-list;
    # if the client IP address is contained there, it is taken as OK;
    to_reread_allow_list = False
    try:
        if (
            (conf["access"][prefix + "_allow_list"]["path"] != "")
            and (
                os.path.getmtime(
                    conf["access"][prefix + "_allow_list"]["path"]
                ) > conf["access"][prefix + "_allow_list"]["read"]
            )
        ):
            to_reread_allow_list = True
    except Exception as exc:
        to_reread_allow_list = False
        logging_action("\n".join([
            f"cannot check modification time of {prefix}_allow_list file:",
            conf["access"][prefix + "_allow_list"]["path"],
            str(exc),
        ]))
    if to_reread_allow_list:
        # rereading the allow-list, as it has changed since its last checking
        take_access_list(
            conf["access"][prefix + "_allow_list"], False, logging_action
        )
    # doing the actual allow-list checking
    for ip_range in conf["access"][prefix + "_allow_list"]["list"]:
        if client_ip_address in ip_range:
            return True

    # second, if the client IP address is not explicitly allowed,
    # and if the default way is not allowing, it is taken as KO
    if not conf["access"][prefix + "_default_allow"]:
        return False

    # third, if the client IP address is not explicitly allowed,
    # and if the default way is allowing,
    # it is necessary to check the respective block-list;
    # if the client IP address is listed here, it is taken as KO;
    to_reread_block_list = False
    try:
        if (
            (conf["access"][prefix + "_block_list"]["path"] != "")
            and (
                os.path.getmtime(
                    conf["access"][prefix + "_block_list"]["path"]
                ) > conf["access"][prefix + "_block_list"]["read"]
            )
        ):
            to_reread_block_list = True
    except Exception as exc:
        to_reread_block_list = False
        logging_action("\n".join([
            f"cannot check modification time of {prefix}_block_list file:",
            conf["access"][prefix + "_block_list"]["path"],
            str(exc),
        ]))
    if to_reread_block_list:
        # rereading the block-list, as it has changed since its last checking
        take_access_list(
            conf["access"][prefix + "_block_list"], False, logging_action
        )
    # doing the actual block-list checking
    for ip_range in conf["access"][prefix + "_block_list"]["list"]:
        if client_ip_address in ip_range:
            return False

    # fourth, if here, the client IP address was not in the access lists,
    # and the default way is to allow, thus it is taken as OK;
    return True
