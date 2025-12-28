/*
 * A notice displayed when the UI waits for a LLM answer.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function SearchWaiting() {
  return /*#__PURE__*/React.createElement("div", {
    className: "search-waiting"
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-waiting-head"
  }, "Waiting for LLM answer."), /*#__PURE__*/React.createElement("div", {
    className: "search-waiting-next"
  }, "at most ", getFabricLlms()["queryTopCount"], " articles get presented"));
}
export { SearchWaiting as default };
