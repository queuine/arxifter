
function BiorxivForm(props) {
    const [submitDisabled, setSubmitDisabled] = React.useState(false);

    function submitQuery(
        subject_id,
        query_text,
        appendSearch,
        setSubmitDisabled
    ) {
        if (query_text.length == 0) {
            return;
        }
        setSubmitDisabled(true);

        appendSearch(false, {subject: subject_id, query: query_text})
        axios.post("/query/" + subject_id, {
                "query": query_text,
            })
            .then(function (response) {
                setSubmitDisabled(false);
                appendSearch(true, response);
            })
            .catch(function (error) {
                setSubmitDisabled(false);
                appendSearch(true, error);
            })
    }

    function handleSubmit(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const formJson = Object.fromEntries(formData.entries());
        submitQuery(
            formJson.selectedBiorxivSubject,
            formJson.queryContent,
            props.appendSearch,
            setSubmitDisabled
        );
    }

    return (
        <form id="biorxiv-form" method="post" onSubmit={handleSubmit}>
            <BiorxivQuery queryContentName="queryContent" />
            <div id="biorxiv-form-bottom">
                <BiorxivSubject subjectName="selectedBiorxivSubject" />
                <BiorxivSubmit disabled={submitDisabled} />
            </div>
        </form>
    );
}
