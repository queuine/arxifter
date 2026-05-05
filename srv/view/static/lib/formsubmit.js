/*
 * Submitting the query.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
function FormSubmit({
  disabled
}) {
  return /*#__PURE__*/React.createElement("button", {
    id: "form-submit-button",
    title: "send the query to LLMs",
    disabled: disabled,
    className: disabled ? "form-submit-button-disabled" : "form-submit-button-enabled"
  }, "Submit");
}
export { FormSubmit as default };
