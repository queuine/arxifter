/*
 * Display of authors of one article.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function AnswerItemAuthors(props) {
  const item = props.content;
  if (!utilsHasValue(item, "authors") && !utilsHasValue(item, "author")) {
    return null;
  }
  const authorsContent = utilsHasValue(item, "authors") ? utilsGetValue(item, "authors") : utilsGetValue(item, "author");
  const maxVisibleItemLength = utilsGetMaxDefaultAuthorsLength();
  if (authorsContent.length <= maxVisibleItemLength) {
    return /*#__PURE__*/React.createElement("div", {
      className: "answer-item-authors"
    }, /*#__PURE__*/React.createElement("span", {
      className: "answer-item-key"
    }, "authors:"), /*#__PURE__*/React.createElement("span", null, authorsContent));
  }
  return /*#__PURE__*/React.createElement("div", {
    className: "answer-item-authors",
    "data-title": authorsContent
  }, /*#__PURE__*/React.createElement("span", {
    className: "answer-item-key"
  }, "authors:"), /*#__PURE__*/React.createElement("span", null, authorsContent.substring(0, maxVisibleItemLength), "..."));
}
export { AnswerItemAuthors as default };
