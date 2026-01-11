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
        this.maxSaveSearches = getFabricUi()["recallSearches"];
        this.state = {
            searchSaving: props.getSaveLastSearches()
        };
        this.manageSearchSaving = (toSave) => {
            props.setSaveLastSearches(toSave);
            props.saveLastSearches(toSave);
        };
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
                            htmlFor="popup-saving-checkbox"
                        >
                            Save locally the last {this.maxSaveSearches}
                            {
                                (this.maxSaveSearches != 1)
                                ? " searches"
                                : " search"
                            }
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
