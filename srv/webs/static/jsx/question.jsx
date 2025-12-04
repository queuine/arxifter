
function BiorxivQuestion(props) {
    return (
        <>
            {(props.rank > 0) ? <hr class="searches-separator" /> : ""}
            <div class="biorxiv-question">
                <div class="question-label">
                    feed subject:
                    <span class="question-subject">
                        {toSubjectView(props.content.subject)}
                    </span>
                </div>
                <div class="question-query">{props.content.query}</div>
            </div>
        </>
    );
}
