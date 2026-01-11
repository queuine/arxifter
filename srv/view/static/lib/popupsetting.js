/*
 * Setting of UI properties.
 * It is done within a popup-like layer.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
class PopupSetting extends React.Component {
  constructor(props) {
    super(props);
    this.closePopup = props.closePopup;
    this.maxSaveSearches = getFabricUi()["recallSearches"];
    this.state = {
      searchSaving: props.getSaveLastSearches()
    };
    this.manageSearchSaving = toSave => {
      props.setSaveLastSearches(toSave);
      props.saveLastSearches(toSave);
    };
  }
  render() {
    return /*#__PURE__*/React.createElement("div", {
      open: true,
      className: "arxifter-popup"
    }, /*#__PURE__*/React.createElement("div", {
      id: "popup-saving-outer"
    }, /*#__PURE__*/React.createElement("div", null, "The last ", this.maxSaveSearches, this.maxSaveSearches != 1 ? " searches " : " search ", "can get saved locally within the browser, so that their results reappear after page reloading."), /*#__PURE__*/React.createElement("div", {
      id: "popup-saving"
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      id: "popup-saving-checkbox",
      checked: this.state.searchSaving,
      onChange: e => {
        const toSave = e.target.checked;
        this.setState({
          searchSaving: toSave
        });
        this.manageSearchSaving(toSave);
      }
    }), /*#__PURE__*/React.createElement("label", {
      htmlFor: "popup-saving-checkbox"
    }, "Save locally the last ", this.maxSaveSearches, this.maxSaveSearches != 1 ? " searches" : " search"))), /*#__PURE__*/React.createElement("div", {
      className: "arxifter-popup-bottom"
    }, /*#__PURE__*/React.createElement("button", {
      className: "arxifter-popup-close",
      onClick: e => {
        this.closePopup();
      }
    }, "Close")));
  }
}
export { PopupSetting as default };
