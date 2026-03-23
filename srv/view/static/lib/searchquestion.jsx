/*
 * Display of one user question (already sent to LLM).
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import SearchQuestionLine from "arxifter/biorxiv/searchquestionline.js";

function SearchQuestion(props) {
    const getSiftLabel = (timestamp, rank) => {
        let ts = Number(timestamp);
        if (!isFinite(ts)) {
            ts = 0;
        } else {
            ts = Math.max(0, Math.round(ts));
        }
        let label = ` sifting #${rank}`
        if (ts) {
            const dt = new Date(ts);
            const dtDay = (
                dt.getFullYear()
                + "-"
                + String(dt.getMonth() + 1).padStart(2, 0)
                + "-"
                + String(dt.getDate()).padStart(2, 0)
            );
            const dtTime = dt.toLocaleTimeString();
            label += `, queried ${dtDay} at ${dtTime}`;
        }
        return label + " ";
    };

    const getFeedDesc = (feedDesc, isActive) => {
        if (!utilsIsString(feedDesc)) {
            return null;
        }
        if (isActive) {
            return "sifted through " + feedDesc;
        }
        return "sifting through " + feedDesc;
    };

    return (
            <div className="search-question">
                <div className="search-question-top">
                    <div
                        className="search-question-label"
                        title={getSiftLabel(props.timestamp, props.rank)}
                    >
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
                    <div className="search-question-buttons-outer">
                        <button
                            className={
                                "search-question-button " + (
                                "search-question-save" ) + (
                                    props.actionActive
                                    ? " search-question-button-active"
                                    : " search-question-button-inactive"
                                )
                            }
                            title={
                                "Download sifting " + `#${props.rank}`
                            }
                            disabled={!props.actionActive}
                            onClick={props.doSave}
                        >
                            🡇
                        </button>
                        <button
                            className={
                                "search-question-button " + (
                                "search-question-delete" ) + (
                                    (props.actionActive)
                                    ? " search-question-button-active"
                                    : " search-question-button-inactive"
                                )
                            }
                            title={
                                "Delete sifting " + `#${props.rank}`
                            }
                            disabled={!props.actionActive}
                            onClick={props.doRemoval}
                        >
                            🗙
                        </button>
                    </div>
                </div>
                <div
                    className="search-question-query"
                    title={
                        getFeedDesc(props.content.feed, props.actionActive)
                    }
                >
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
