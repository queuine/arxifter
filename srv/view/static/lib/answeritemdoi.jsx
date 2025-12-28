/*
 * Display of DOI (and date) of one article.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function AnswerItemDOI(props) {
    const item = props.content;

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
                {utilsGetValue(item, "doi")}
            </a>
        }
        {
            (utilsHasValue(item, "doi") && !utilsHasValue(item, "link"))
            &&
            <span>{utilsGetValue(item, "doi")}</span>
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
