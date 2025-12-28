/*
 * A notice displayed when the UI waits for a LLM answer.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function SearchWaiting() {
    return (
        <div className="search-waiting">
            <div className="search-waiting-head">
                Waiting for LLM answer.
            </div>
            <div className="search-waiting-next">
                at most {getFabricLlms()["queryTopCount"]} articles
                get presented
            </div>
        </div>
    );
}

export { SearchWaiting as default };
