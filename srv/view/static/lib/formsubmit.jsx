/*
 * Submitting the query.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function FormSubmit({disabled}) {
    return (
        <button
            id="form-submit-button"
            title="send the query to LLM"
            disabled={disabled}
        >
            Submit
        </button>
    );
}

export { FormSubmit as default };
