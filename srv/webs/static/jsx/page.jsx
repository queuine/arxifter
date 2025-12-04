
function BiorxivPage() {
    let searchesRef = React.createRef();

    function appendSearch(isAnswer, payload) {
        if (isAnswer) {
            let data_content = null;
            try {
                data_content = payload.data.answer;
            } catch (e) {
                data_content = payload;
            }
            searchesRef.current.addSearch(true, data_content);
        } else {
            searchesRef.current.addSearch(false, payload);
        }
    };

    return (
        <div id="biorxiv-page">
            <BiorxivForm appendSearch={appendSearch} />
            <BiorxivSearches ref={searchesRef} />
        </div>
    );
}
