/*
 * Input for the user query.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
class FormQuery extends React.Component {
  constructor(props) {
    super(props);
    this.children = props.children;
    this.queryContentName = props.dataName;
    this.lastArticlesCount = getFabricFeeds()["feedSize"];
    this.textareaRef = React.createRef();
    this.textareaIdName = "form-query-textarea";
    this.state = {
      underEmpty: false
    };
    this.setUnderEmpty = val => {
      this.setState({
        underEmpty: val
      });
      if (val) {
        this.textareaRef.current?.focus();
      }
    };
    this.queryLabel = "" + `Query on the last ${this.lastArticlesCount} articles ` + "(per feed) at bioRχiv";
    this.queryPlaceholder = ["", "Enter a search query for LLM to sift through bioRχiv feeds.", "It can be e.g. 'List all articles related to bacteria.'"].join("\n    ");
  }
  render() {
    return /*#__PURE__*/React.createElement("div", {
      id: "form-query-cover"
    }, /*#__PURE__*/React.createElement("div", {
      id: "form-query-roof"
    }, /*#__PURE__*/React.createElement("label", {
      id: "form-query-title",
      htmlFor: this.textareaIdName
    }, this.queryLabel), this.children), /*#__PURE__*/React.createElement("textarea", {
      ref: this.textareaRef,
      id: this.textareaIdName,
      name: this.queryContentName,
      rows: 4,
      cols: 80,
      maxlength: utilsGetMaxQueryLength(),
      placeholder: this.queryPlaceholder,
      autofocus: "true",
      onChange: e => {
        this.setUnderEmpty(false);
      },
      className: this.state.underEmpty ? "form-query-textarea-under-empty" : "form-query-textarea"
    }));
  }
}
export { FormQuery as default };
