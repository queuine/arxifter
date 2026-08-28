#!/usr/bin/env python
"""
Attempts to parse LLM answers on user queries.
"""

import re, json

from json_repair import repair_json

from .setting import (
    JSON_START_REMOVALS,
    JSON_END_REMOVALS,
    JSON_FLANKS,
    ARTICLE_VALUE_REASON_ENDING,
)

ANSWER_ARTICLE_MAX_TRASH_LINES = 3
ANSWER_ARTICLE_KEY_ARTNUM = "artnum"
ANSWER_ARTICLE_KEY_TITLE_PREFIX = "title_prefix"
ANSWER_ARTICLE_KEY_REASON = "reason"
ANSWER_ARTICLE_KEY_MATCHES = "matches"
ANSWER_ARTICLE_KEYS = [
    ANSWER_ARTICLE_KEY_ARTNUM,
    ANSWER_ARTICLE_KEY_TITLE_PREFIX,
    ANSWER_ARTICLE_KEY_REASON,
    ANSWER_ARTICLE_KEY_MATCHES,
]
ANSWER_ARTICLE_KEY_ARTNUM_PAT = r"(?:art|article)(?:[_\s-]*)(?:num|number|)"
ANSWER_ARTICLE_KEY_ARTNUM_RE = (
    re.compile(
        ANSWER_ARTICLE_KEY_ARTNUM_PAT,
        re.I | re.U,
    )
)
ANSWER_ARTICLE_KEY_TITLE_PREFIX_PAT = r"title(?:[_\s-]*)(?:prefix|)"
ANSWER_ARTICLE_KEY_TITLE_PREFIX_RE = (
    re.compile(
        ANSWER_ARTICLE_KEY_TITLE_PREFIX_PAT,
        re.I | re.U,
    )
)
ANSWER_ARTICLE_KEYS_PAT = [
    ANSWER_ARTICLE_KEY_ARTNUM_PAT,
    ANSWER_ARTICLE_KEY_TITLE_PREFIX_PAT,
    ANSWER_ARTICLE_KEY_REASON,
    ANSWER_ARTICLE_KEY_MATCHES,
]
ANSWER_ARTICLE_KEYS_REPL = {
    ANSWER_ARTICLE_KEY_ARTNUM: ANSWER_ARTICLE_KEY_ARTNUM_RE,
    ANSWER_ARTICLE_KEY_TITLE_PREFIX: ANSWER_ARTICLE_KEY_TITLE_PREFIX_RE,
}
ANSWER_LINE_EMPTY = re.compile("".join([
    r"^",
    r"([^\w\d]*)",
    r"$",
]), re.I | re.U)
# when a line contains one key-value info of an article
ANSWER_LINE_FIELD = re.compile("".join([
    r"^",
    r"(?:[_\W]*)",
    r"(",
    r"|".join([
        r"(?:" + line_key + r"(?:[\w]*))"
        for line_key in ANSWER_ARTICLE_KEYS_PAT
    ]),
    r")",
    r"(?:[\W]*)",
    r":",
    r"(?:[^\w\d]*)",
    r"((?:[\w\d])(?:.*))",
    r"$",
]), re.I | re.U)
ANSWER_LINE_KEY = re.compile("".join([
    r"^",
    r"|".join([
        line_key
        for line_key in ANSWER_ARTICLE_KEYS_PAT
    ]),
]), re.I | re.U)
ANSWER_LINE_VALUE_NUMBER = re.compile("".join([
    r"^([\d]+)(?:[^\d]*)$",
]), re.I | re.U)
ANSWER_LINE_VALUE_TRUE = "true"
ANSWER_LINE_VALUE_FALSE = "false"
ANSWER_LINE_VALUE_BOOLEAN = re.compile("".join([
    r"^(",
    ANSWER_LINE_VALUE_TRUE,
    r"|",
    ANSWER_LINE_VALUE_FALSE,
    r")(?:.*)$",
]), re.I | re.U)
ANSWER_LINE_VALUE_TEXT = re.compile("".join([
    r"^(.+)(?:[^\d\w]*)$",
]), re.I | re.U)
ANSWER_LINE_VALUE_ENDING = re.compile("".join([
    r"(?:[^\d\w]*)$",
]), re.I | re.U)
# when a line contains all key-value infos of an article
ANSWER_LINE_WHOLE_ARTICLE_PART = "".join([
    r"(?:",                 # start of one key-value pair
    r"(?:[^\d\w]*)",
    r"(",                   # possible key: start
    r"|".join([
        r"(?:(?:[_-]*)" + line_key + r"(?:[_-]*))"
        for line_key in ANSWER_ARTICLE_KEYS_PAT
    ]),
    r")",                   # possible key: end
    r"(?:[^\d\w]*)",
    r":",                   # required splitting between key and value
    r"(?:[^\w\d]*)",
    r"((?:[\w\d])(?:.*))",  # any value
    r")",                   # end of one key-value pair
])
ANSWER_LINE_WHOLE_ARTICLE = re.compile("".join([
    r"^",
    r"(?:.*)",              # anything at line start
    3 * ANSWER_LINE_WHOLE_ARTICLE_PART,
    2 * (ANSWER_LINE_WHOLE_ARTICLE_PART + "?"),
    r"(?:[_\W]*)",          # non-words at line end
    r"$",
]), re.I | re.U)


def _simple_repairing(answer):
    answer = answer.strip()

    # some LLMs flank their answers as: ```json...```
    for part in JSON_START_REMOVALS:
        if answer.startswith(part):
            answer = answer[len(part):]
    for part in JSON_END_REMOVALS:
        if answer.endswith(part):
            answer = answer[:-len(part)]
    answer = answer.strip()

    # some met broken answers had single-instead-of-double quotes
    return answer.replace("'\n", '"\n').replace("',\n", '",\n')


def _last_json_in_text(answer):
    # some provider/LLMs services return the answer along with reasoning;
    # it is not clear whether the inference providers fail in separating
    # the reasoning from the actual output, or whether those LLMs fail it,
    # but the actual output lacks any separating tokens then;
    # when the eventual json is at least flanked by ```json and ```,
    # it is possible to take it as the last occurrence of it;
    for json_flank_start, json_flank_end in JSON_FLANKS:
        last_start = answer.rfind(json_flank_start)
        if last_start < 0:
            continue
        answer_use = answer[last_start+len(json_flank_start):]
        last_end = answer_use.rfind(json_flank_end)
        if last_end < 0:
            continue
        answer_use = answer_use[:last_end]
        if not answer_use.strip():
            continue
        return _simple_repairing(answer_use)

    # if here, no common JSON-list flanking was found;
    # trying to look for simple "[{}]" structuring in there;
    use_lines = []
    met_start = False
    met_end = False
    for line in reversed(answer.splitlines()):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if not met_end:
            if line_stripped == "]":
                met_end = True
            else:
                continue
        use_lines.append(line)
        if line_stripped == "[":
            met_start = True
            break

    if (not met_start) or (not met_end):
        return None
    if len(use_lines) < 3:
        return None
    if not use_lines[1].strip().endswith("}"):
        return None
    if not use_lines[-2].strip().startswith("{"):
        return None

    return _simple_repairing("\n".join(reversed(use_lines)))


def _basic_article_data_check(article):
    has_artnum = False
    has_title_prefix = False
    artnum_val = None

    for key, value in article.items():
        if ANSWER_ARTICLE_KEY_ARTNUM_RE.search(key):
            if (
                (type(value) is int)
                or (
                    (type(value) is str)
                    and value.isascii()
                    and value.isdigit()
                )
            ):
                has_artnum = True
                artnum_val = int(value)
        if ANSWER_ARTICLE_KEY_TITLE_PREFIX_RE.search(key):
            if (
                (type(value) is str)
                and len(value)
            ):
                has_title_prefix = True

    return [
        has_artnum and has_title_prefix,
        artnum_val,
    ]


def _thorough_repairing(answer):
    answer = _simple_repairing(answer)

    # thorough repairing with the use of the json_repair package
    repaired_json = repair_json(answer, skip_json_loads=True)
    if repaired_json == "":
        raise OSError("too broken JSON even for json_repair")

    repaired_data = json.loads(repaired_json)

    if type(repaired_data) in [list, tuple]:
        used_artnums = {}
        use_data = []
        for item in reversed(repaired_data):
            if type(item) is not dict:
                continue
            is_correct, artnum = _basic_article_data_check(item)
            if is_correct and (artnum not in used_artnums):
                use_data.append(item)
                if artnum is not None:
                    used_artnums[artnum] = True
        if len(use_data) == 0:
            return None
        return list(reversed(use_data))

    if type(repaired_data) is not dict:
        return None

    is_correct, _ = _basic_article_data_check(repaired_data)
    if not is_correct:
        return None
    return repaired_data


def _last_data_in_text_one_key_value(
    article, key_part, value_part, force_fill
):
    line_key_obj = ANSWER_LINE_KEY.search(key_part)
    if line_key_obj is None:
        # this should not occur
        return False
    line_key = line_key_obj.group(0).lower()

    for repl_val, repl_re in ANSWER_ARTICLE_KEYS_REPL.items():
        if repl_re.match(line_key) is not None:
            line_key = repl_val
            break

    if (not force_fill) and (article[line_key] is not None):
        # surplus data silently ignored
        return True

    if line_key == ANSWER_ARTICLE_KEY_ARTNUM:
        line_value = ANSWER_LINE_VALUE_NUMBER.match(value_part)
        if line_value is None:
            return False
        if len(line_value.groups()) != 1:
            # this should not occur
            return False
        try:
            article[line_key] = int(line_value.group(1))
        except Exception:
            # this should not occur
            return False
        return True

    if line_key == ANSWER_ARTICLE_KEY_MATCHES:
        line_value = ANSWER_LINE_VALUE_BOOLEAN.match(value_part)
        if line_value is None:
            return False
        if len(line_value.groups()) != 1:
            # this should not occur
            return False
        item_value = line_value.group(1).lower()
        if item_value == ANSWER_LINE_VALUE_TRUE:
            article[line_key] = True
        elif item_value == ANSWER_LINE_VALUE_FALSE:
            article[line_key] = False
        else:
            # this should not occur
            return False
        return True

    line_value = ANSWER_LINE_VALUE_TEXT.match(value_part)
    if line_value is None:
        return False
    if len(line_value.groups()) != 1:
        # this should not occur
        return False
    item_value = line_value.group(1)
    item_end = ""
    if line_key in [
        ANSWER_ARTICLE_KEY_REASON, ANSWER_ARTICLE_KEY_TITLE_PREFIX
    ]:
        line_ending = ANSWER_LINE_VALUE_ENDING.search(item_value)
        if line_ending is not None:
            item_value = item_value[:line_ending.start()]
        if not item_value:
            return False
        if (
            (line_key == ANSWER_ARTICLE_KEY_REASON)
            and (not item_value.endswith(ARTICLE_VALUE_REASON_ENDING))
        ):
            item_end = ARTICLE_VALUE_REASON_ENDING
    article[line_key] = item_value + item_end
    return True


def _last_data_in_text_article_for_use(article):
    if (
        (article[ANSWER_ARTICLE_KEY_ARTNUM] is None)
        and (article[ANSWER_ARTICLE_KEY_TITLE_PREFIX] is None)
    ):
        return False
    for art_key in ANSWER_ARTICLE_KEYS:
        if article[art_key] is None:
            del article[art_key]
    return True


def _last_data_in_text_one_article(article_list, line_obj):
    article = {
        art_key: None
        for art_key in ANSWER_ARTICLE_KEYS
    }

    if (len(line_obj.groups()) & 1) == 1:
        # this should not occur
        return False
    pairs_count = len(line_obj.groups()) >> 1

    key_idx = -1
    val_idx = 0
    for _ in range(pairs_count):
        key_idx += 2
        val_idx += 2
        key_part = line_obj.group(key_idx)
        val_part = line_obj.group(val_idx)
        if (key_part is None) or (val_part is None):
            continue
        _last_data_in_text_one_key_value(
            article,
            key_part,
            val_part,
            True,
        )

    if _last_data_in_text_article_for_use(article):
        article_list.append(article)
        return True
    return False


def _last_data_in_text(answer):
    # some provider/LLMs services return article data
    # without that put into JSON list/structure;
    trash_non_empty_line_count = 0
    got_one_article = False
    got_one_key_value = False

    article_list = []
    article = {
        art_key: None
        for art_key in ANSWER_ARTICLE_KEYS
    }

    for line in reversed(answer.splitlines()):
        if ANSWER_LINE_EMPTY.match(line):
            continue

        if got_one_article:
            line_obj = ANSWER_LINE_WHOLE_ARTICLE.match(line)
        elif got_one_key_value:
            line_obj = ANSWER_LINE_FIELD.match(line)
        else:
            line_obj = ANSWER_LINE_WHOLE_ARTICLE.match(line)
            if line_obj:
                got_one_article = True
            else:
                line_obj = ANSWER_LINE_FIELD.match(line)
                if line_obj:
                    got_one_key_value = True

        if (not got_one_article) and (not got_one_key_value):
            trash_non_empty_line_count += 1
            if (
                trash_non_empty_line_count > ANSWER_ARTICLE_MAX_TRASH_LINES
            ):
                break
            continue

        if got_one_article:
            # if here: received one-or-more whole articles
            if not line_obj:
                break
            if not _last_data_in_text_one_article(article_list, line_obj):
                break
            continue

        # if here: received one-or-more key/value pairs
        if line_obj is None:
            break
        if len(line_obj.groups()) != 2:
            # this should not occur
            break
        if not _last_data_in_text_one_key_value(
            article,
            line_obj.group(1),
            line_obj.group(2),
            False,
        ):
            break
        for _, art_val in article.items():
            if art_val is None:
                break
        else:
            # not continuing to try to get more article data
            # if article data are already all got and filled
            break

    # when here: all relevant data (if present) got already read

    if got_one_article:
        # if here, it seems that a list of one-or-more articles got received
        if len(article_list) == 0:
            return None
        return article_list

    if not got_one_key_value:
        return None

    # if here, it seems that a single-article data got received
    if _last_data_in_text_article_for_use(article):
        return [article]
    return None


def parse_llm_answer(conf, get_logger, answer):
    """
    Tries to parse the LLM answer:
    * as it is,
    * with minor tweaks,
    * with large repairing
    """
    logger = get_logger(__name__)
    parsed_answer = None
    err_msgs = []

    repair_methods = [
        [
            lambda answer: answer,
            None,
            True,
            False,
        ],
        [
            _simple_repairing,
            "LLM answer had minor issues (fixed automatically)",
            True,
            False,
        ],
        [
            _last_json_in_text,
            "LLM answer was apparently returned mixed with reasoning",
            True,
            False,
        ],
        [
            _thorough_repairing,
            "LLM answer was a more broken JSON (repaired by json_repair)",
            False,
            True,
        ],
        [
            _last_data_in_text,
            "some data salvaged from the answer lacking JSON format",
            False,
            True,
        ],
    ]

    for method, message, to_load, spout in repair_methods:
        if parsed_answer is not None:
            break
        try:
            parsed_answer = json.loads(
                method(str(answer))
            ) if to_load else method(str(answer))
            if (
                (message is not None)
                and (
                    spout or conf["debugging"]["query_sifting"]
                )
            ):
                logger.warning(message)
        except Exception as exc:
            parsed_answer = None
            err_msgs.append(str(exc))

    if parsed_answer is None:
        logger.error(
            "LLM answer was a generally invalid and too broken JSON"
        )
        raise OSError("\n".join(err_msgs))

    return parsed_answer
