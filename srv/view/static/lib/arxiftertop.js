/*
 * The topmost part of the page, containing:
 * a configuration-provided link,
 * buttons to the setting and user popups.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function ArxifterTop(props) {
  const openPopupSetting = props.openPopupSetting;
  const openPopupUsers = props.openPopupUsers;
  const fabricBacklink = getFabricBacklink();
  return /*#__PURE__*/React.createElement("div", {
    id: "arxifter-top"
  }, /*#__PURE__*/React.createElement("div", {
    id: "arxifter-top-links"
  }, /*#__PURE__*/React.createElement("a", {
    id: "arxifter-top-backlink",
    href: fabricBacklink["link"],
    title: fabricBacklink["title"],
    target: "_blank"
  }, fabricBacklink["name"], ":"), /*#__PURE__*/React.createElement("div", {
    title: "via ar\u03C7ifter sifting through bioR\u03C7iv feeds"
  }, "check what's new on", ' ' /* to keep a white space in there */, /*#__PURE__*/React.createElement("a", {
    id: "arxifter-top-biorxiv-link",
    href: "https://www.biorxiv.org/",
    target: "_blank"
  }, "bioR\u03C7iv"))), /*#__PURE__*/React.createElement("div", {
    id: "arxifter-top-buttons-outer"
  }, /*#__PURE__*/React.createElement("button", {
    id: "arxifter-top-button-setting",
    className: "arxifter-top-button",
    title: "configuration of UI",
    onClick: e => {
      openPopupSetting();
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "arxifter-top-button-title"
  }, "Setting")), /*#__PURE__*/React.createElement("button", {
    id: "arxifter-top-button-users",
    className: "arxifter-top-button",
    title: "set up regular or guest user",
    onClick: e => {
      openPopupUsers();
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "arxifter-top-button-title"
  }, "Users"))));
}
export { ArxifterTop as default };
