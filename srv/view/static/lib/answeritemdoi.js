/*
 * Display of DOI (and date) of one article.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function AnswerItemDOI(props) {
  const item = props.content;
  const doiShown = doiVal => {
    if (!utilsIsString(doiVal)) {
      return JSON.stringify(doiVal);
    }
    const doiPrefix = "doi:";
    if (doiVal.startsWith(doiPrefix)) {
      return doiVal;
    }
    return doiPrefix + doiVal;
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "answer-item-doi"
  }, utilsHasValue(item, "doi") && utilsHasValue(item, "link") && /*#__PURE__*/React.createElement("a", {
    target: "_blank",
    className: "answer-item-doi-link",
    href: utilsGetValue(item, "link")
  }, doiShown(utilsGetValue(item, "doi"))), utilsHasValue(item, "doi") && !utilsHasValue(item, "link") && /*#__PURE__*/React.createElement("span", null, doiShown(utilsGetValue(item, "doi"))), utilsHasValue(item, "doi") && utilsHasValue(item, "date") && /*#__PURE__*/React.createElement("span", null, " / "), utilsHasValue(item, "date") && /*#__PURE__*/React.createElement("span", null, utilsGetValue(item, "date")));
}
export { AnswerItemDOI as default };
