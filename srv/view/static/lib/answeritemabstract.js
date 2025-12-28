/*
 * Display of abstract of one article.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
class AnswerItemAbstract extends React.Component {
  constructor(props) {
    super(props);
    this.item = props.content;
    this.state = {
      abstractWhole: false,
      abstractChange: false
    };
  }

  // taking the current scrolling position before changing
  // whether a long abstract is shown whole or not;
  getSnapshotBeforeUpdate(prevProps, prevState) {
    return window.scrollY;
  }
  // here preserving the scrolling position on the change
  // of how a long abstract is shown,
  // so that its reading is not disrupted;
  componentDidUpdate(prevProps, prevState, snapshot) {
    if (!this.state.abstractChange) {
      return;
    }
    this.setState({
      abstractChange: false
    });
    if (snapshot !== null) {
      window.scroll(window.scrollX, snapshot);
    }
  }
  render() {
    const item = this.item;
    if (!utilsHasValue(item, "abstract")) {
      // if here, having no abstract;
      return null;
    }
    const abstractContent = utilsGetValue(item, "abstract");
    const maxVisibleItemLength = utilsGetMaxDefaultAbstractLength();
    if (abstractContent.length <= maxVisibleItemLength) {
      // if here, the abstract is short;
      return /*#__PURE__*/React.createElement("div", {
        className: "answer-item-abstract"
      }, /*#__PURE__*/React.createElement("span", {
        className: "answer-item-key"
      }, "abstract:"), /*#__PURE__*/React.createElement("span", null, abstractContent));
    }
    if (this.state.abstractWhole) {
      // while the abstract is too long, it is shown whole here;
      return /*#__PURE__*/React.createElement("div", {
        className: "answer-item-abstract"
      }, /*#__PURE__*/React.createElement("span", {
        className: "answer-item-key"
      }, "abstract:"), /*#__PURE__*/React.createElement("span", null, abstractContent.substring(0, maxVisibleItemLength - 1)), /*#__PURE__*/React.createElement("span", {
        className: "answer-item-abstract-middle"
      }, abstractContent.substring(maxVisibleItemLength - 1, maxVisibleItemLength + 1)), /*#__PURE__*/React.createElement("span", null, abstractContent.substring(maxVisibleItemLength + 1)), /*#__PURE__*/React.createElement("button", {
        className: "answer-item-more-less",
        title: " show less ",
        onClick: e => {
          this.setState({
            abstractWhole: !this.state.abstractWhole,
            abstractChange: true
          });
        }
      }, /*#__PURE__*/React.createElement("span", null, "<<<")));
    }

    // if here, the abstract is too long and not being shown whole;
    return /*#__PURE__*/React.createElement("div", {
      className: "answer-item-abstract"
    }, /*#__PURE__*/React.createElement("span", {
      className: "answer-item-key"
    }, "abstract:"), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("span", null, abstractContent.substring(0, maxVisibleItemLength), "..."), /*#__PURE__*/React.createElement("button", {
      className: "answer-item-more-less",
      title: " show more ",
      onClick: e => {
        this.setState({
          abstractWhole: !this.state.abstractWhole,
          abstractChange: true
        });
      }
    }, /*#__PURE__*/React.createElement("span", null, ">>>"))));
  }
}
export { AnswerItemAbstract as default };
