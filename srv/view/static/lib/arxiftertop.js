/*
 * The topmost part of the page, containing:
 * a configuration-provided link,
 * link to the user-setting popup.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function ArxifterTop(props) {
  const openPopup = props.openPopup;
  const fabricLocal = getFabricLocal();
  return /*#__PURE__*/React.createElement("div", {
    id: "arxifter-top"
  }, /*#__PURE__*/React.createElement("a", {
    id: "arxifter-top-backlink",
    href: fabricLocal["backLink"],
    target: "_blank"
  }, fabricLocal["backName"]), /*#__PURE__*/React.createElement("button", {
    id: "arxifter-top-about",
    onClick: e => {
      openPopup();
    }
  }, "About"));
}
export { ArxifterTop as default };
