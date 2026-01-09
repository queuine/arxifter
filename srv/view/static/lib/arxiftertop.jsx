/*
 * The topmost part of the page, containing:
 * a configuration-provided link,
 * link to the user-setting popup.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function ArxifterTop(props) {
    const openPopup = props.openPopup;
    const fabricLocal = getFabricLocal();

    return (
        <div id="arxifter-top">
            <a
                id="arxifter-top-backlink"
                href={fabricLocal["backLink"]}
                target="_blank"
            >
                {fabricLocal["backName"]}
            </a>
            <button
                id="arxifter-top-about"
                onClick={(e) => {openPopup();}}
            >
                About
            </button>
        </div>
    );
}

export { ArxifterTop as default };
