/*
 * Selecting the subject of the feed to be asked on.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function FormSubject(props) {
  const subjectName = props.dataName;
  const fabricFeeds = getFabricFeeds();
  const biorxivSubjectLabels = fabricFeeds["subjects"];
  const biorxivSubjectLabelsDefaultSystem = biorxivSubjectLabels.indexOf(fabricFeeds["defaultSubject"]);
  const biorxivSubjectLabelDefault = biorxivSubjectLabels[props.usedSubject > -1 ? props.usedSubject : biorxivSubjectLabelsDefaultSystem > -1 ? biorxivSubjectLabelsDefaultSystem : 0];
  return /*#__PURE__*/React.createElement("div", {
    id: "form-subject-outer",
    title: "choose a feed for the sifting"
  }, /*#__PURE__*/React.createElement("label", {
    id: "form-subject-label",
    htmlFor: "form-subject-selection"
  }, /*#__PURE__*/React.createElement("span", {
    id: "form-subject-title"
  }, "biorxiv feed:")), /*#__PURE__*/React.createElement("select", {
    id: "form-subject-selection",
    name: subjectName,
    defaultValue: biorxivSubjectLabelDefault
  }, /*#__PURE__*/React.createElement("button", null, /*#__PURE__*/React.createElement("selectedcontent", null)), biorxivSubjectLabels.map(subjectLabel => /*#__PURE__*/React.createElement("option", {
    key: subjectLabel,
    value: subjectLabel
  }, utilsToSubjectView(subjectLabel)))));
}
export { FormSubject as default };
