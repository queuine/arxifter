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
      underEmpty: false,
      autoFocus: props.autoFocus
    };
    this.setUnderEmpty = val => {
      this.setState({
        underEmpty: val
      });
      if (val) {
        this.textareaRef.current?.focus();
      }
    };
    this.setAutoFocus = val => {
      this.setState({
        autoFocus: val
      });
    };
    this.queryLabel = "" + "Query";
    this.queryPlaceholder = ["", "Enter a query that will get sifted through bioRχiv feeds.", "It can be e.g. 'On structuring and dynamics of membranes.'"].join("\n    ");
  }
  render() {
    return /*#__PURE__*/React.createElement("div", {
      id: "form-query-cover"
    }, /*#__PURE__*/React.createElement("div", {
      id: "form-query-upper"
    }, /*#__PURE__*/React.createElement("label", {
      id: "form-query-title",
      title: "Query to sift through chosen bioRχiv subjects",
      htmlFor: this.textareaIdName
    }, this.queryLabel), /*#__PURE__*/React.createElement("div", {
      id: "form-query-choices"
    }, this.children)), /*#__PURE__*/React.createElement("textarea", {
      ref: this.textareaRef,
      id: this.textareaIdName,
      name: this.queryContentName,
      rows: 4,
      cols: 80,
      maxlength: utilsGetMaxQueryLength(),
      placeholder: this.queryPlaceholder,
      autofocus: this.state.autoFocus ? 'true' : false,
      onChange: e => {
        this.setUnderEmpty(false);
      },
      className: this.state.underEmpty ? "form-query-textarea-under-empty" : "form-query-textarea"
    }));
  }
}
export { FormQuery as default };
