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
  const fabricLocal = getFabricLocal();
  return /*#__PURE__*/React.createElement("div", {
    id: "arxifter-top"
  }, /*#__PURE__*/React.createElement("a", {
    id: "arxifter-top-backlink",
    href: fabricLocal["backLink"],
    title: fabricLocal["backTitle"],
    target: "_blank"
  }, fabricLocal["backName"]), /*#__PURE__*/React.createElement("div", {
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
