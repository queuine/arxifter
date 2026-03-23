/*
 * Displays data of one article (of an answer).
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import AnswerItemDOI from "arxifter/biorxiv/answeritemdoi.js";
import AnswerItemAuthors from "arxifter/biorxiv/answeritemauthors.js";
import AnswerItemAbstract from "arxifter/biorxiv/answeritemabstract.js";

function AnswerItem(props) {
    const item = props.content;
    const warningKey = utilsGetWarningKey();
    const subjectKey = utilsGetSubjectKey();

    const hiddenKeys = [
        "author_corresponding",
        "author_corresponding_institution",
        "license",
        subjectKey,
        "jatsxml",
        "funder",
        "published",
        "server"
    ];

    const getSpareKeys = (item) => {
        let spareKeys = [];
        const suggestionKey = utilsGetSuggestionKey();
        const flankKeys = [
            warningKey,
            "title",
            "doi",
            "link",
            "date",
            "author",
            "authors",
            "abstract",
            "other",
            "version",
            "type"
        ].concat(utilsGetReasoningKeys());

        Object.entries(item).map(([key, val]) => {
            if (!utilsIsString(key)) {
                spareKeys.push(JSON.stringify(key, null, 0));
            } else if (flankKeys.indexOf(key.toLowerCase()) < 0) {
                if (hiddenKeys.indexOf(key.toLowerCase()) < 0) {
                    if (key != suggestionKey) {
                        spareKeys.push(key);
                    }
                }
            }
        });
        return spareKeys;
    };

    const getStringForm = (item) => {
        if (utilsIsString(item)) {
            return item;
        }
        return JSON.stringify(item);
    };

    const getTitleTitle = (docData) => {
        let ttShown = [];
        if (utilsIsString(docData[subjectKey])) {
            ttShown.push(
                "subject: " + docData[subjectKey].replaceAll("_", " ")
            );
        }
        ["version", "type"].forEach((key, idx) => {
            if (utilsIsString(docData[key])) {
                ttShown.push(`${key}: ` + docData[key]);
            }
        })
        if (utilsIsString(docData["other"])) {
            ttShown.push(docData["other"]);
        }
        if (ttShown.length == 0) {
            return null;
        }
        return ttShown.join(", ");
    }

    return (
        <div className="answer-item">
        {
            utilsHasValue(item, warningKey)
            &&
            <div>
                <span className="answer-item-key">notice:</span>
                <span className="answer-item-notice">
                    {utilsGetValue(item, warningKey)}
                </span>
            </div>
        }
            <div className="answer-item-title-outer">
                <div className="answer-item-key">title:</div>
                <div
                    className="answer-item-title"
                    title={getTitleTitle(item)}
                >
                    {utilsGetValue(item, "title")}
                </div>
            </div>
        {
            (utilsHasValue(item, "doi") || utilsHasValue(item, "date"))
            &&
            <AnswerItemDOI content={item} />
        }
        {
            (utilsHasValue(item, "authors") || utilsHasValue(item, "author"))
            &&
            <AnswerItemAuthors content={item} />
        }
        {
            utilsHasValue(item, "abstract")
            &&
            <AnswerItemAbstract content={item} />
        }
        {
            getSpareKeys(item).map((x, i) => (
                <div key={i}>
                    <span className="answer-item-key">{getStringForm(x)}:</span>
                    <span>{getStringForm(item[x])}</span>
                </div>
            ))
        }
        {
            utilsGetReasoningKeys().map((x, i) => (
                utilsHasValue(item, x)
                &&
                <div key={i}>
                    <span className="answer-item-key">{x}:</span>
                    <span>{utilsGetValue(item, x)}</span>
                </div>
            ))
        }
        </div>
    )
}

export { AnswerItem as default };
