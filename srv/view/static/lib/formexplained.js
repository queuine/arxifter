/*
 * Setting whether LLM should explain its article selection.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function FormExplained(props) {
  const checkName = props.dataName;
  const [getExplained, setGetExplained] = React.useState(props.explaining);
  return /*#__PURE__*/React.createElement("div", {
    id: "form-explained-outer",
    title: "whether LLM should explain its choices"
  }, /*#__PURE__*/React.createElement("input", {
    id: "form-explained-checkbox",
    type: "checkbox",
    name: checkName,
    value: "yes",
    checked: getExplained,
    onChange: e => {
      setGetExplained(!getExplained);
    }
  }), /*#__PURE__*/React.createElement("label", {
    id: "form-explained-label",
    htmlFor: "form-explained-checkbox"
  }, "explained"));
}
export { FormExplained as default };

/*
        <label
            title="whether LLM should explain its choices"
        >
            <input
                type="checkbox"
                name={checkName}
                value="yes"
                checked={getExplained}
                onChange={(e) => {
                    setGetExplained(!getExplained);
                }}
            />
            explained
        </label>
*/
