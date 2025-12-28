/*
 * Display of authors of one article.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function AnswerItemAuthors(props) {
    const item = props.content;

    if (
        (!utilsHasValue(item, "authors"))
        &&
        (!utilsHasValue(item, "author"))
    ) {
        return null;
    }

    const authorsContent = (
        utilsHasValue(item, "authors")
        ?
        utilsGetValue(item, "authors")
        :
        utilsGetValue(item, "author")
    );

    const maxVisibleItemLength = utilsGetMaxDefaultAuthorsLength();

    if (authorsContent.length <= maxVisibleItemLength) {
        return (
            <div className="answer-item-authors">
                <span className="answer-item-key">authors:</span>
                <span>{authorsContent}</span>
            </div>
        )
    }

    return (
        <div
            className="answer-item-authors"
            data-title={authorsContent}
        >
            <span className="answer-item-key">authors:</span>
            <span>
                {authorsContent.substring(0, maxVisibleItemLength)}...
            </span>
        </div>
    )
}

export { AnswerItemAuthors as default };
