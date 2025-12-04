
function BiorxivQuery({queryContentName}) {
    const lastArticlesCount = getFeedArticleCount();

    const queryLabel = ""
        + `Query on the last ${lastArticlesCount} articles `
        + "(per subject) at bioRχiv";

    const queryPlaceholder = ""
        + "Enter a search query for LLM to sift through bioRχiv feeds."

    return (
        <label id="biorxiv-query-label">
            <span id="biorxiv-query-title">{queryLabel}</span>
            <textarea
                id="biorxiv-query-textarea"
                name={queryContentName}
                rows={8}
                cols={120}
                placeholder={queryPlaceholder}
            />
        </label>
    );
}
