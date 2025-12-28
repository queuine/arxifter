/*
 * Display of answer data when the data do not follow the standard way.
 * It is usually either when LLM did not found any matching article,
 * providing an as-close-as-possible article instead of that,
 * or when a (network or server) error occurs.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import AnswerItem from "arxifter/biorxiv/answeritem.js";

function AnswerDirect(props) {
    const content = props.content;

    return (
        <>
        {
            (
                utilsIsDict(content) &&
                (content[utilsGetSuggestionKey()] === true)
            )
            ?
            <>
                <div className="search-answer-suggestion">
                    <span className="search-answer-empty">
                        Nothing matching was found,
                        but the following article might be of an interest.
                    </span>
                </div>
                <AnswerItem content={content} />
            </>
            :
            <pre><code>{JSON.stringify(content, null, 4)}</code></pre>
        }
        </>
    )
}

export { AnswerDirect as default };
