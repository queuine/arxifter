/*
 * Display of one user question (already sent to LLM).
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import SearchQuestionLine from "arxifter/biorxiv/searchquestionline.js";

function SearchQuestion(props) {
    return (
            <div className="search-question">
                <div className="search-question-top">
                    <div className="search-question-label">
                        <div className="search-question-feed">
                        {
                            utilsIsFeedMulti(props.content.subject)
                            ?
                            <span>feed&nbsp;subjects:</span>
                            :
                            <span>feed&nbsp;subject:</span>
                        }
                        </div>
                        <div className="search-question-subject">
                            {utilsToSubjectView(props.content.subject)}
                        </div>
                    </div>
                    <div className="search-question-delete-outer">
                        <button
                            className={
                                "search-question-delete" + (
                                    (props.removalActive)
                                    ? ""
                                    : " search-question-delete-inactive"
                                )
                            }
                            title="Delete the search results"
                            disabled={!props.removalActive}
                            onClick={props.removal}
                        >
                            X
                        </button>
                    </div>
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
