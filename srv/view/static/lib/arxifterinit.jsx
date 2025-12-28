/*
 * Loading of the React-based UI.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import ArxifterPage from "arxifter/biorxiv/arxifterpage.js";

function pageInit() {
    const container = document.getElementById('root');
    const root = ReactDOM.createRoot(container);
    root.render(
        <ArxifterPage />
    );
}

if (
    (document.readyState == "loading")
    || (document.readyState == "uninitialized")
) {
    if (document.addEventListener) {
        document.addEventListener( "DOMContentLoaded", pageInit );
    } else {
        window.onload = pageInit;
    }
} else {
    pageInit();
}
