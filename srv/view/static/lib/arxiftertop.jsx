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
                    title="configuration of UI"
                    onClick={(e) => {openPopupSetting();}}
                >
                    <span
                        className="arxifter-top-button-title"
                    >
                        Setting
                    </span>
                </button>
                <button
                    id="arxifter-top-button-users"
                    className="arxifter-top-button"
                    title="set up regular or guest user"
                    onClick={(e) => {openPopupUsers();}}
                >
                    <span
                        className="arxifter-top-button-title"
                    >
                        Users
                    </span>
                </button>
            </div>
        </div>
    );
}

export { ArxifterTop as default };
