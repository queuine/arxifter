/*
 * Displays data of one article (of an answer).
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
import AnswerItemDOI from "arxifter/biorxiv/answeritemdoi.js";
import AnswerItemAuthors from "arxifter/biorxiv/answeritemauthors.js";
import AnswerItemAbstract from "arxifter/biorxiv/answeritemabstract.js";
function AnswerItem(props) {
  const item = props.content;
  const warningKey = utilsGetWarningKey();
  function getSpareKeys(item) {
    let spareKeys = [];
    const suggestionKey = utilsGetSuggestionKey();
    const flankKeys = [warningKey, "title", "doi", "link", "date", "author", "authors", "abstract"].concat(utilsGetReasoningKeys());
    Object.entries(item).map(([key, val]) => {
      if (!utilsIsString(key)) {
        spareKeys.push(JSON.stringify(key, null, 0));
      } else if (flankKeys.indexOf(key.toLowerCase()) < 0) {
        if (key != suggestionKey) {
          spareKeys.push(key);
        }
      }
    });
    return spareKeys;
  }
  ;
  return /*#__PURE__*/React.createElement("div", {
    className: "answer-item"
  }, utilsHasValue(item, warningKey) && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    className: "answer-item-key"
  }, "notice:"), /*#__PURE__*/React.createElement("span", {
    className: "answer-item-notice"
  }, utilsGetValue(item, warningKey))), utilsHasValue(item, "title") && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    className: "answer-item-key"
  }, "title:"), /*#__PURE__*/React.createElement("span", {
    className: "answer-item-title"
  }, utilsGetValue(item, "title"))), (utilsHasValue(item, "doi") || utilsHasValue(item, "date")) && /*#__PURE__*/React.createElement(AnswerItemDOI, {
    content: item
  }), (utilsHasValue(item, "authors") || utilsHasValue(item, "author")) && /*#__PURE__*/React.createElement(AnswerItemAuthors, {
    content: item
  }), utilsHasValue(item, "abstract") && /*#__PURE__*/React.createElement(AnswerItemAbstract, {
    content: item
  }), getSpareKeys(item).map((x, i) => /*#__PURE__*/React.createElement("div", {
    key: i
  }, /*#__PURE__*/React.createElement("span", {
    className: "answer-item-key"
  }, x, ":"), /*#__PURE__*/React.createElement("span", null, item[x]))), utilsGetReasoningKeys().map((x, i) => utilsHasValue(item, x) && /*#__PURE__*/React.createElement("div", {
    key: i
  }, /*#__PURE__*/React.createElement("span", {
    className: "answer-item-key"
  }, x, ":"), /*#__PURE__*/React.createElement("span", null, utilsGetValue(item, x)))));
}
export { AnswerItem as default };
