/*
 * Setting whether LLM should explain its article selection.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function FormExplained(props) {
    const checkName = props.dataName;
    const [getExplained, setGetExplained] = (
        React.useState(props.explaining)
    );

    return (
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
    );
}

export { FormExplained as default };
