/*
 * Display of one user question (already sent to LLM).
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import SearchQuestionLine from "arxifter/biorxiv/searchquestionline.js";

function SearchQuestion(props) {
    return (
            <div className="search-question">
                <div className="search-question-label">
                    feed subject:
                    <span className="search-question-subject">
                        {utilsToSubjectView(props.content.subject)}
                    </span>
                </div>
                <div className="search-question-query">
                    {
                        props.content.query.split(/\r?\n|\r|\n/g)
                        .map((x, i) => (
                            <SearchQuestionLine
                                key={i}
                                line={x}
                            />
                        ))
                    }
                </div>
            </div>
    );
}

export { SearchQuestion as default };
