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
        <div
            id="form-explained-outer"
            title="whether LLM should explain its choices"
        >
            <input
                id="form-explained-checkbox"
                type="checkbox"
                name={checkName}
                value="yes"
                checked={getExplained}
                onChange={(e) => {
                    setGetExplained(!getExplained);
                }}
            />
            <label
                id="form-explained-label"
                htmlFor="form-explained-checkbox"
            >
                explained
            </label>
        </div>
    );
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
