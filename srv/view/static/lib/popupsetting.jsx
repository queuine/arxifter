/*
 * Setting of UI properties.
 * It is done within a popup-like layer.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

class PopupSetting extends React.Component {
    constructor(props) {
        super(props);
        this.closePopup = props.closePopup;
        this.maxSaveSearches = getFabricUi()["recallSifts"];
        this.state = {
            searchSaving: props.getSaveLastSearches(),
            autoFocusTA: props.getAutoFocusTA(),
            atDarkMode: props.getInDarkMode()
        };
        this.manageSearchSaving = (toSave) => {
            props.setSaveLastSearches(toSave);
            props.saveLastSearches(toSave);
        };
        this.manageAutoFocusTA = (toAutoFocus) => {
            props.setAutoFocusTA(toAutoFocus);
        };
        this.setLightDarkView = (atDarkMode) => {
            const newTheme = atDarkMode ? "dark" : "light";
            document.documentElement.setAttribute('data-theme', newTheme);
        };
        this.manageDarkMode = (toDarkMode) => {
            props.setInDarkMode(toDarkMode);
            this.setLightDarkView(toDarkMode);
        };
        this.setLightDarkView(this.state.atDarkMode);
    }

    render() {
        return (
            <div open className="arxifter-popup">
                <div id="popup-saving-outer">
                    <div>
                        The last {this.maxSaveSearches}
                        {
                            (this.maxSaveSearches != 1)
                            ? " searches "
                            : " search "
                        }
                        can get saved locally within the browser,
                        so that their results reappear after
                        page reloading.
                    </div>
                    <div id="popup-saving">
                        <input
                            type="checkbox"
                            id="popup-saving-checkbox"
                            checked={this.state.searchSaving}
                            onChange={(e) => {
                                const toSave = e.target.checked;
                                this.setState({
                                    searchSaving: toSave
                                });
                                this.manageSearchSaving(toSave);
                            }}
                        />
                        <label
                            id="popup-saving-label"
                            htmlFor="popup-saving-checkbox"
                        >
                            save locally the last {this.maxSaveSearches}
                            {
                                (this.maxSaveSearches != 1)
                                ? " searches"
                                : " search"
                            }
                        </label>
                    </div>
                    <div id="popup-setting-ui">
                        General UI configuration:
                    </div>
                    <div id="popup-setting-autofocus">
                        <input
                            type="checkbox"
                            id="popup-setting-autofocus-checkbox"
                            checked={this.state.autoFocusTA}
                            onChange={(e) => {
                                const toAutoFocus = e.target.checked;
                                this.setState({
                                    autoFocusTA: toAutoFocus
                                });
                                this.manageAutoFocusTA(toAutoFocus);
                            }}
                        />
                        <label
                            id="popup-setting-autofocus-label"
                            htmlFor="popup-setting-autofocus-checkbox"
                        >
                            autofocus the query text area
                        </label>
                    </div>
                    <div id="popup-setting-darkmode">
                        <input
                            type="checkbox"
                            id="popup-setting-darkmode-checkbox"
                            checked={this.state.atDarkMode}
                            onChange={(e) => {
                                const toDarkMode = e.target.checked;
                                this.setState({
                                    atDarkMode: toDarkMode
                                });
                                this.manageDarkMode(toDarkMode);
                            }}
                        />
                        <label
                            id="popup-setting-darkmode-label"
                            htmlFor="popup-setting-darkmode-checkbox"
                        >
                            display the page in dark mode
                        </label>
                    </div>
                </div>
                <div className="arxifter-popup-bottom">
                    <button
                        className="arxifter-popup-close"
                        onClick={(e) => {
                            this.closePopup();
                        }}
                    >
                        Close
                    </button>
                </div>
            </div>
        );
    }
}

export { PopupSetting as default };
