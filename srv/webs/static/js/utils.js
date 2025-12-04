
function toSubjectView(subjectLabel) {
    if (subjectLabel.length == 0) {
        return "";
    }
    return (
        subjectLabel.charAt(0).toUpperCase() + subjectLabel.slice(1)
    ).replaceAll("_", " ");
};

function getFeedArticleCount() {
    return 30;
}
