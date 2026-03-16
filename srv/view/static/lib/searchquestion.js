/*
 * Display of one user question (already sent to LLM).
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
import SearchQuestionLine from "arxifter/biorxiv/searchquestionline.js";
function SearchQuestion(props) {
  const getSiftLabel = (timestamp, rank) => {
    let ts = Number(timestamp);
    if (!isFinite(ts)) {
      ts = 0;
    } else {
      ts = Math.max(0, Math.round(ts));
    }
    let label = ` sifting #${rank}`;
    if (ts) {
      const dt = new Date(ts);
      const dt_day = dt.getFullYear() + "-" + String(dt.getMonth() + 1).padStart(2, 0) + "-" + String(dt.getDate()).padStart(2, 0);
      const dt_time = dt.toLocaleTimeString();
      label += `, queried ${dt_day} at ${dt_time}`;
    }
    return label + " ";
  };
  const getFeedDesc = (feedDesc, isActive) => {
    if (!utilsIsString(feedDesc)) {
      return null;
    }
    if (isActive) {
      return "sifted through " + feedDesc;
    }
    return "sifting through " + feedDesc;
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "search-question"
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-question-top"
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-question-label",
    title: getSiftLabel(props.timestamp, props.rank)
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-question-feed"
  }, utilsIsFeedMulti(props.content.subject) ? /*#__PURE__*/React.createElement("span", null, "feed\xA0subjects:") : /*#__PURE__*/React.createElement("span", null, "feed\xA0subject:")), /*#__PURE__*/React.createElement("div", {
    className: "search-question-subject"
  }, utilsToSubjectView(props.content.subject))), /*#__PURE__*/React.createElement("div", {
    className: "search-question-buttons-outer"
  }, /*#__PURE__*/React.createElement("button", {
    className: "search-question-button " + "search-question-save" + (props.actionActive ? " search-question-button-active" : " search-question-button-inactive"),
    title: "Download sifting " + `#${props.rank}`,
    disabled: !props.actionActive,
    onClick: props.doSave
  }, "\uD83E\uDC47"), /*#__PURE__*/React.createElement("button", {
    className: "search-question-button " + "search-question-delete" + (props.actionActive ? " search-question-button-active" : " search-question-button-inactive"),
    title: "Delete sifting " + `#${props.rank}`,
    disabled: !props.actionActive,
    onClick: props.doRemoval
  }, "\uD83D\uDDD9"))), /*#__PURE__*/React.createElement("div", {
    className: "search-question-query",
    title: getFeedDesc(props.content.feed, props.actionActive)
  }, props.content.query.split(/\r?\n|\r|\n/g).map((x, i) => /*#__PURE__*/React.createElement(SearchQuestionLine, {
    key: i,
    line: x
  }))));
}
export { SearchQuestion as default };
