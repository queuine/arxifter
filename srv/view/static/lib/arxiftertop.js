/*
 * The topmost part of the page, containing:
 * a configuration-provided link,
 * link to the user-setting popup.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function ArxifterTop(props) {
  const openPopup = props.openPopup;
  const fabricPopup = getFabricPopup();
  return /*#__PURE__*/React.createElement("div", {
    id: "arxifter-top"
  }, /*#__PURE__*/React.createElement("a", {
    id: "arxifter-top-backlink",
    href: fabricPopup["backLink"],
    target: "_blank"
  }, fabricPopup["backName"]), /*#__PURE__*/React.createElement("button", {
    id: "arxifter-top-about",
    onClick: e => {
      openPopup();
    }
  }, "About"));
}
export { ArxifterTop as default };
