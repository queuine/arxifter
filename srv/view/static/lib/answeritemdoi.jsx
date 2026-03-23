/*
 * Display of DOI (and date) of one article.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function AnswerItemDOI(props) {
    const item = props.content;
    const doiShown = (doiVal) => {
        if (!utilsIsString(doiVal)) {
            return JSON.stringify(doiVal);
        }
        const doiPrefix = "doi:";
        if (doiVal.startsWith(doiPrefix)) {
            return doiVal;
        }
        return doiPrefix + doiVal;
    }

    return (
        <div className="answer-item-doi">
        {
            (utilsHasValue(item, "doi") && utilsHasValue(item, "link"))
            &&
            <a
                target="_blank"
                className="answer-item-doi-link"
                href={utilsGetValue(item, "link")}
            >
                {doiShown(utilsGetValue(item, "doi"))}
            </a>
        }
        {
            (utilsHasValue(item, "doi") && !utilsHasValue(item, "link"))
            &&
            <span>{doiShown(utilsGetValue(item, "doi"))}</span>
        }
        {
            (utilsHasValue(item, "doi") && utilsHasValue(item, "date"))
            &&
            <span> / </span>
        }
        {
            (utilsHasValue(item, "date"))
            &&
            <span>{utilsGetValue(item, "date")}</span>
        }
        </div>
    )
}

export { AnswerItemDOI as default };
