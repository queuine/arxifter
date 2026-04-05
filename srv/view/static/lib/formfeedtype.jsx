/*
 * Setting for the feed type: per last days or per last count of articles.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function FormFeedType(props) {
    const feedTypeDays = getFabricQuery()["feedTypeDays"];
    const feedTypeCounts = getFabricQuery()["feedTypeCounts"];
    const checkName = props.dataName;
    const [getFeedType, setGetFeedType] = (
        React.useState(props.feedType)
    );
    const lastArticlesDays = getFabricFeeds()["depoDepth"];
    const lastArticlesCount = getFabricFeeds()["feedSize"];
    const labelLastDays = ""
        + "to sift through subject articles within "
        + `the last ${lastArticlesDays} days`;
    const labelLastCount = ""
        + `to sift through the last ${lastArticlesCount} `
        + "articles per subject";
    const handleFeedTypeSelection = (event) => {
        setGetFeedType(event.target.value);
    }

    return (
        <>
            <div
                className="form-set-type-outer"
            >
                <input
                    id="form-set-type-radio-1"
                    className="form-set-type-radio"
                    title={labelLastDays}
                    type="radio"
                    name={checkName}
                    value={feedTypeDays}
                    checked={getFeedType === feedTypeDays}
                    onChange={handleFeedTypeSelection}
                />
                <label
                    id="form-set-type-label-1"
                    className="form-set-type-label"
                    htmlFor="form-set-type-radio-1"
                    title={labelLastDays}
                >
                    articles within the last {lastArticlesDays} days
                </label>
            </div>
            <div
                className="form-set-type-outer"
            >
                <input
                    id="form-set-type-radio-2"
                    className="form-set-type-radio"
                    title={labelLastCount}
                    type="radio"
                    name={checkName}
                    value={feedTypeCounts}
                    checked={getFeedType === feedTypeCounts}
                    onChange={handleFeedTypeSelection}
                />
                <label
                    id="form-set-type-label-2"
                    className="form-set-type-label"
                    htmlFor="form-set-type-radio-2"
                    title={labelLastCount}
                >
                    the last {lastArticlesCount} articles per subject
                </label>
            </div>
        </>
    );
}

export { FormFeedType as default };
