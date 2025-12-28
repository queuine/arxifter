/*
 * Display of one line from a user question.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function SearchQuestionLine(props) {
    const line = props.line;
    const lineTrimmed = line.trim();
    const maxSpaceCount = utilsGetMaxQuestionLineIndenting();
    const startingSpacesCount = Math.max(0, Math.min(
        maxSpaceCount,
        line.search(/\S|$/)
    ));

    if (lineTrimmed == "") {
        return (
            <div>&nbsp;</div>
        );
    }

    return (
        <div>
        {
            Array.from({length: startingSpacesCount}, (x, i) => (
                <span key={i}>&nbsp;</span>
            ))
        }
        {
            lineTrimmed
        }
        </div>
    );
}

export { SearchQuestionLine as default };
