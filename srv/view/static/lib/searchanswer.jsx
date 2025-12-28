/*
 * Display of one LLM answer.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import AnswerItem from "arxifter/biorxiv/answeritem.js";
import AnswerDirect from "arxifter/biorxiv/answerdirect.js";

function SearchAnswer(props) {
    return (
        <div className="search-answer">
            <div className="search-answer-label">llm answer:</div>
            {
                (
                    (typeof props.content !== "undefined")
                    &&
                    (props.content.constructor == Array)
                )
                ?
                props.content.map((x, i) => (
                    utilsIsDict(x)
                    ?
                    <AnswerItem key={JSON.stringify(i)} content={x} />
                    :
                    <AnswerDirect key={JSON.stringify(i)} content={x} />
                ))
                :
                <AnswerDirect content={props.content} />
            }
            {
                (
                    (typeof props.content === "undefined")
                    ||
                    (
                        (props.content.constructor == Array)
                        &&
                        (props.content.length == 0)
                    )
                )
                &&
                <span className="search-answer-empty">Nothing found.</span>
            }
        </div>
    );
}

export { SearchAnswer as default };
