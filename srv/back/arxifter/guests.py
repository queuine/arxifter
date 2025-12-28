#!/usr/bin/env python
"""
Management of guest users.
Look at the [users] part of configuration for the setting of it.
"""

import os, re, random, binascii, math
from pathlib import Path
import datetime as dt
import asyncio

from .setting import (
    GUEST_ID_LENGTH,
    HEXDIGITS,
    GUEST_IDS_LIST_SIZE,
    GUEST_FILENAME_MAKING,
    GUEST_FILENAME_LISTING,
)


def _make_new_guest_id():
    return "".join([
        random.choice(HEXDIGITS) for ind in range(GUEST_ID_LENGTH)
    ])


def list_guest_id_files(conf, curr_dt):
    """
    Lists all current ids amenable for guest users.
    """
    for item in sorted(
        Path(conf["users"]["guest_ids"]["path"]).glob("*"),
        reverse=True
    ):
        if not item.is_file():
            continue
        matched = re.match(GUEST_FILENAME_LISTING, item.parts[-1])
        if matched is None:
            continue
        try:
            file_delta = (
                curr_dt
                - dt.datetime(
                    *[int(part) for part in matched.groups()],
                    tzinfo=dt.UTC,
                )
            )
        except Exception:
            continue
        yield (
            item,
            ((file_delta.days * 24) + (file_delta.seconds / 3600)),
        )


def _prune_past_guest_ids(conf, curr_dt):
    for file_path_obj, hour_diff in list_guest_id_files(conf, curr_dt):
        if hour_diff < (conf["users"]["guest_span"] + 1):
            continue
        try:
            file_path_obj.unlink(missing_ok=True)
        except Exception:
            continue


def get_guests_json(conf, curr_dt, xor_str):
    """
    Provides a list of ids (of at most setting:GUEST_IDS_LIST_SIZE length)
    that can be used by guests.
    """
    if not conf["users"]["with_guest"]:
        return []

    id_list = []
    id_count = 0
    for file_path_obj, hour_diff in list_guest_id_files(conf, curr_dt):
        if hour_diff >= 1:
            break
        try:
            id_list.append(
                Path(file_path_obj).read_text(encoding="utf8").strip()
            )
            id_count += 1
            if id_count == GUEST_IDS_LIST_SIZE:
                break
        except Exception:
            continue

    xor_rep = math.ceil(GUEST_ID_LENGTH / len(xor_str))
    xor_bytes = binascii.unhexlify(
        (xor_str * xor_rep)[:GUEST_ID_LENGTH]
    )
    return [
        binascii.hexlify(bytes(
            a ^ b for a, b in zip(binascii.unhexlify(item), xor_bytes)
        )).decode("utf8")
        for item in id_list
    ]


async def ensure_guest_id(conf, curr_dt):
    """
    Keeps some ids amenable for guest users;
    that if guest users are enabled in configuration.
    """
    if not conf["users"]["with_guest"]:
        return
    _prune_past_guest_ids(conf, curr_dt)

    file_name = curr_dt.strftime(GUEST_FILENAME_MAKING)
    file_path = os.path.join(conf["users"]["guest_ids"]["path"], file_name)
    try:
        guest_id = _make_new_guest_id()
        with open(file_path, "x", encoding="utf8") as fh:
            fh.write(guest_id)
    except FileExistsError:
        for _ in range(20):
            try:
                guest_id = Path(file_path).read_text(encoding="utf8").strip()
                if len(guest_id) == GUEST_ID_LENGTH:
                    break
            except Exception:
                pass
            await asyncio.sleep(0.1)

    return len(guest_id) == GUEST_ID_LENGTH
