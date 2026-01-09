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
    className: "search-question-label"
  }, utilsIsFeedMulti(props.content.subject) ? "feed subjects:" : "feed subject:", /*#__PURE__*/React.createElement("span", {
    className: "search-question-subject"
  }, utilsToSubjectView(props.content.subject))), /*#__PURE__*/React.createElement("div", {
    className: "search-question-query"
  }, props.content.query.split(/\r?\n|\r|\n/g).map((x, i) => /*#__PURE__*/React.createElement(SearchQuestionLine, {
    key: i,
    line: x
  }))));
}
export { SearchQuestion as default };
