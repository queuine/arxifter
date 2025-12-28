/*
 * Display of one LLM answer.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
import AnswerItem from "arxifter/biorxiv/answeritem.js";
import AnswerDirect from "arxifter/biorxiv/answerdirect.js";
function SearchAnswer(props) {
  return /*#__PURE__*/React.createElement("div", {
    className: "search-answer"
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-answer-label"
  }, "llm answer:"), typeof props.content !== "undefined" && props.content.constructor == Array ? props.content.map((x, i) => utilsIsDict(x) ? /*#__PURE__*/React.createElement(AnswerItem, {
    key: JSON.stringify(i),
    content: x
  }) : /*#__PURE__*/React.createElement(AnswerDirect, {
    key: JSON.stringify(i),
    content: x
  })) : /*#__PURE__*/React.createElement(AnswerDirect, {
    content: props.content
  }), (typeof props.content === "undefined" || props.content.constructor == Array && props.content.length == 0) && /*#__PURE__*/React.createElement("span", {
    className: "search-answer-empty"
  }, "Nothing found."));
}
export { SearchAnswer as default };
