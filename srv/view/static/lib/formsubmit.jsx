/*
 * Submitting the query.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function FormSubmit({disabled}) {
    return (
        <button
            id="form-submit-button"
            title="send the query to LLMs"
            disabled={disabled}
            className={
                disabled
                ?
                "form-submit-button-disabled"
                :
                "form-submit-button-enabled"
            }
        >
            Submit
        </button>
    );
}

export { FormSubmit as default };
