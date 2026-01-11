/*
 * The topmost part of the page, containing:
 * a configuration-provided link,
 * buttons to the setting and user popups.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function ArxifterTop(props) {
    const openPopupSetting = props.openPopupSetting;
    const openPopupUsers = props.openPopupUsers;
    const fabricLocal = getFabricLocal();

    return (
        <div id="arxifter-top">
            <a
                id="arxifter-top-backlink"
                href={fabricLocal["backLink"]}
                title={fabricLocal["backTitle"]}
                target="_blank"
            >
                {fabricLocal["backName"]}
            </a>
            <div id="arxifter-top-buttons-outer">
                <button
                    id="arxifter-top-button-setting"
                    className="arxifter-top-button"
                    onClick={(e) => {openPopupSetting();}}
                >
                    Setting
                </button>
                <button
                    id="arxifter-top-button-users"
                    className="arxifter-top-button"
                    onClick={(e) => {openPopupUsers();}}
                >
                    Users
                </button>
            </div>
        </div>
    );
}

export { ArxifterTop as default };
