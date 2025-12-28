/*
 * Display of DOI (and date) of one article.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function AnswerItemDOI(props) {
  const item = props.content;
  return /*#__PURE__*/React.createElement("div", {
    className: "answer-item-doi"
  }, utilsHasValue(item, "doi") && utilsHasValue(item, "link") && /*#__PURE__*/React.createElement("a", {
    target: "_blank",
    className: "answer-item-doi-link",
    href: utilsGetValue(item, "link")
  }, utilsGetValue(item, "doi")), utilsHasValue(item, "doi") && !utilsHasValue(item, "link") && /*#__PURE__*/React.createElement("span", null, utilsGetValue(item, "doi")), utilsHasValue(item, "doi") && utilsHasValue(item, "date") && /*#__PURE__*/React.createElement("span", null, " / "), utilsHasValue(item, "date") && /*#__PURE__*/React.createElement("span", null, utilsGetValue(item, "date")));
}
export { AnswerItemDOI as default };
