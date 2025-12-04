
function BiorxivAnswer(props) {

    function isDict(item) {
        return (
            item !== undefined && item !== null && item.constructor == Object
        );
    }

    return (
        <div class="biorxiv-answer">
            <div class="answer-label">llm answer:</div>
            {
                (props.content.constructor == Array)
                ?
                props.content.map((x, i) => (
                    isDict(x)
                    ?
                    <BiorxivAnswerItem key={i} content={x} />
                    :
                    <BiorxivAnswerDirect key={i} content={x} />
                ))
                :
                <BiorxivAnswerDirect content={props.content} />
            }
            {
                (
                    (props.content.constructor == Array)
                    &&
                    (props.content.length == 0)
                )
                ?
                <span class="answer-empty">Nothing found.</span>
                :
                ""
            }
        </div>
    );
}
