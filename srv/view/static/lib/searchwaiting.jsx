/*
 * A notice displayed when the UI waits for an LLM answer.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function SearchWaiting(props) {
    return (
        <div className="search-waiting">
            <div className="search-waiting-head">
                Waiting for LLM answer.
            </div>
            <div className="search-waiting-next">
                at most {getFabricSifting()["answerMaxCount"]} articles
                get presented
            </div>
            <div className="search-waiting-time">
                {Math.round((Date.now() - props.timestamp) / 1000)}s
            </div>
        </div>
    );
}

export { SearchWaiting as default };
