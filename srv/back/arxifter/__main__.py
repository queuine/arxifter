#!/usr/bin/env python
#
# arxifter: sifting through open archives
# Copyright (c) 2025 Martin Saturka
# Released under the MIT license.
#
"""
Module for calling auxiliary tools:
* for feed parsing/indexing, call it as "python -m arxifter parse|index <dir>"
* for taking the list of subjects, cal it as "python -m arxifter list subjects"
"""

import sys

PARSE_COMMAND = "parse"
INDEX_COMMAND = "index"
LIST_COMMAND = "list"
LIST_ARG_SUBJECTS = "subjects"


if __name__ == "__main__":
    if len(sys.argv) == 3:
        if sys.argv[1] == PARSE_COMMAND:
            try:
                from .parser import parse_feed
                res = parse_feed(sys.argv[2])
            except Exception as exc:
                sys.stderr.write(str(exc) + "\n")
                res = False
            sys.exit(0 if res else 2)

        if sys.argv[1] == INDEX_COMMAND:
            try:
                from .indexer import index_docs
                res = index_docs(sys.argv[2])
            except Exception as exc:
                sys.stderr.write(str(exc) + "\n")
                res = False
            sys.exit(0 if res else 2)

        if sys.argv[1] == LIST_COMMAND:
            if sys.argv[2] != LIST_ARG_SUBJECTS:
                sys.exit(1)
            res = True
            try:
                from .subjects import get_subjects_sh
                print(get_subjects_sh(), file=sys.stdout)
            except Exception as exc:
                sys.stderr.write(str(exc) + "\n")
                res = False
            sys.exit(0 if res else 2)

        sys.stderr.write("unknown command\n")
        sys.exit(1)

    sys.stderr.write("wrong parameters\n")
    sys.exit(1)
