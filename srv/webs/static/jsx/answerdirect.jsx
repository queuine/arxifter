
function BiorxivAnswerDirect(props) {
    return (
        <pre><code>{JSON.stringify(props.content, null, 4)}</code></pre>
    )
}
