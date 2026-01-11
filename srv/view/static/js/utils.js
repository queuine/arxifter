/*
 * Assorted auxiliary functions.
 */

// display form of subjects of biorxiv feeds
function utilsToSubjectView(subjectLabel) {
    if (subjectLabel.length == 0) {
        return "";
    }
    let subjectParts = [];
    subjectLabel.split("+").forEach(item => {
        if (item.length != 0) {
            subjectParts.push(
                (item.charAt(0).toUpperCase() + item.slice(1))
                .replaceAll("_", " ")
            );
        }
    });
    return subjectParts.join(" + ");
};

// determines whether the feed is based on several subjects
function utilsIsFeedMulti(subjectLabel) {
    if (subjectLabel == "all") {
        return true;
    }
    if (subjectLabel.indexOf("+") > -1) {
        return true;
    }
    return false;
};

// maximal length for a user query
function utilsGetMaxQueryLength() {
    return 1000;
};

// for display of authors of LLM-taken articles
function utilsGetMaxDefaultAuthorsLength() {
    return 150;
};

// for display of abstracts of LLM-taken articles
function utilsGetMaxDefaultAbstractLength() {
    return 400;
};

// used within display of user questions
function utilsGetMaxQuestionLineIndenting() {
    return 60;
};

// key stating that an LLM answer is not an exact match
function utilsGetSuggestionKey() {
    return "instead";
};

// key of system warnings (used as items in responses)
function utilsGetWarningKey() {
    return "warning";
};

// key for expired session (of a guest)
function utilsGetSessionGoneKey() {
    return "expired";
};

// item keys commonly used for explanations by LLM
function utilsGetReasoningKeys() {
    return [
        "reason",
        "reasons",
        "selection_reason",
        "selection_reasons"
    ];
};

// checking a string form of an item (e.g. in LLM answers)
function utilsIsString(val) {
    return ((typeof val === "string") || (val instanceof String));
};

// checking a dict form of an item (e.g. in LLM answers)
function utilsIsDict(item) {
    return (
        (typeof item !== "undefined")
        && (item !== null)
        && (item.constructor == Object)
    );
};

// checking an array form of an item (e.g. in LLM answers)
function utilsIsArray(item) {
    return Array.isArray(item);
};

// finding exact forms of items in LLM answers
function utilsGetKey(item, key) {
    if (key in item) {
        return key;
    }
    if (!utilsIsString(key)) {
        return null;
    }
    if (key.length == 0) {
        return null;
    }

    const form_capit = key.charAt(0).toUpperCase() + key.slice(1);
    if (form_capit in item) {
        return form_capit;
    }
    const form_upper = key.toUpperCase();
    if (form_upper in item) {
        return form_upper;
    }
    return null;
};

// checking presence of items in LLM answers
function utilsHasValue(item, key) {
    return (utilsGetKey(item, key) !== null);
};

// taking values from items of LLM answers
function utilsGetValue(item, key) {
    if (utilsGetKey(item, key) !== null) {
        let itemVal = item[utilsGetKey(item, key)];
        if (!utilsIsString(itemVal)) {
            itemVal = JSON.stringify(itemVal);
        }
        return itemVal;
    }
    return "unknown";
};

// path for making guest sessions
function utilsGetSessionParts() {
    return ["session", "guests"];
};

// path for making queries on feeds
function utilsGetQueryParts() {
    return ["query"];
};

// cookie reading
function utilsGetCookieValue(cookieName) {
    let cookieValue = "";
    document.cookie.split(";").forEach(item => {
        const splitIdx = item.indexOf("=");
        if (
            (splitIdx > 0)
            && (item.substring(0, splitIdx).trim() == cookieName)
        ) {
            cookieValue = item.substring(splitIdx + 1).trim();
            return;
        }
    });
    try {
        cookieValue = decodeURIComponent(cookieValue);
    } catch (e) {
        cookieValue = "";
    }
    return cookieValue;
};

// cookie deleting
function utilsDelCookieValue(cookieName) {
    const usePath = "/";
    document.cookie = (
        cookieName
        + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path="
        + usePath
        + ";"
    );
};

// cookie setting
function utilsSetCookieValue(cookieName, cookieValue, cookieExp) {
    if (cookieExp <= 0) {
        return;
    }
    const usePath = "/";
    const dt = new Date();
    dt.setTime(dt.getTime() + (cookieExp * 24 * 3600 * 1000));
    const expStr = dt.toUTCString();
    document.cookie = (
        cookieName + "=" + encodeURIComponent(cookieValue)
        + "; expires=" + expStr + "; path="
        + usePath
        + ";"
    );
};

// makes random hexadecimal string
function utilsRandomizeHex() {
    const innHex = "0123456789abcdef";
    let outHex = "";
    while (true) {
        let arrHex = innHex.split("");
        for (let i = arrHex.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arrHex[i], arrHex[j]] = [arrHex[j], arrHex[i]];
        }
        outHex = arrHex.join("");
        let revHex = arrHex.toReversed().join("");
        if ((innHex != outHex) && (innHex != revHex)) {
            break;
        }
    }
    return outHex;
};

// generates ID that is unique within a search list only
function utilsGenSearchID(rank) {
    const randPart = Math.round(Math.random() * 1e9);
    return `search-${rank}-${Date.now()}-${randPart}`;
};
