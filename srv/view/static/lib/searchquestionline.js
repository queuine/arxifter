/*
 * Display of one line from a user question.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function SearchQuestionLine(props) {
  const line = props.line;
  const lineTrimmed = line.trim();
  const maxSpaceCount = utilsGetMaxQuestionLineIndenting();
  const startingSpacesCount = Math.max(0, Math.min(maxSpaceCount, line.search(/\S|$/)));
  if (lineTrimmed == "") {
    return /*#__PURE__*/React.createElement("div", null, "\xA0");
  }
  return /*#__PURE__*/React.createElement("div", null, Array.from({
    length: startingSpacesCount
  }, (x, i) => /*#__PURE__*/React.createElement("span", {
    key: i
  }, "\xA0")), lineTrimmed);
}
export { SearchQuestionLine as default };
