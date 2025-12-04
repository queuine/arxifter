#!/usr/bin/env python

import os, sys, json

import feedparser

from .setting import DOCUMENTS_SUBDIR


def parse_feed(source):

    feed = None
    try:
        feed = feedparser.parse(source)
    except Exception as exc:
        print(exc, file=sys.stderr)
        return False

    feed_ents = None
    try:
        feed_ents = feed['entries']
    except Exception as exc:
        print(exc, file=sys.stderr)
        return False

    work_dir = os.path.dirname(source)
    use_subdir = DOCUMENTS_SUBDIR
    use_dir = os.path.join(work_dir, use_subdir)

    try:
        os.makedirs(use_dir, exist_ok=True)
    except Exception as exc:
        print(exc, file=sys.stderr)
        return False

    ind = -1
    for entry in feed_ents:
        ind += 1

        doc_name = str(ind+1).rjust(3).replace(" ", "0") + ".json"
        with open(os.path.join(use_dir, doc_name), "w", encoding="utf8") as fh:
            fh.write(json.dumps({
                'doi': entry['dc_identifier'],
                'link': entry['link'],
                'updated': entry['updated'],
                'title': entry['title'],
                'authors': entry['authors'],
                'abstract': entry['description'],
            }))

    return True
