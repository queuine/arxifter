/*
 * Display of one user question (already sent to LLM).
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
import SearchQuestionLine from "arxifter/biorxiv/searchquestionline.js";
function SearchQuestion(props) {
  return /*#__PURE__*/React.createElement("div", {
    className: "search-question"
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-question-top"
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-question-label"
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-question-feed"
  }, utilsIsFeedMulti(props.content.subject) ? /*#__PURE__*/React.createElement("span", null, "feed\xA0subjects:") : /*#__PURE__*/React.createElement("span", null, "feed\xA0subject:")), /*#__PURE__*/React.createElement("div", {
    className: "search-question-subject"
  }, utilsToSubjectView(props.content.subject))), /*#__PURE__*/React.createElement("div", {
    className: "search-question-delete-outer"
  }, /*#__PURE__*/React.createElement("button", {
    className: "search-question-delete" + (props.removalActive ? "" : " search-question-delete-inactive"),
    title: "Delete the search results",
    disabled: !props.removalActive,
    onClick: props.removal
  }, "X"))), /*#__PURE__*/React.createElement("div", {
    className: "search-question-query"
  }, props.content.query.split(/\r?\n|\r|\n/g).map((x, i) => /*#__PURE__*/React.createElement(SearchQuestionLine, {
    key: i,
    line: x
  }))));
}
export { SearchQuestion as default };
