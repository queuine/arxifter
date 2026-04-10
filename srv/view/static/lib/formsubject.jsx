/*
 * Selecting the subject of the feed to be asked on.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

function FormSubject(props) {
    const subjectName = props.dataName;
    const fabricFeeds = getFabricFeeds();
    const biorxivSubjectLabels = fabricFeeds["subjects"];
    const biorxivSubjectLabelsDefaultSystem = (
        biorxivSubjectLabels.indexOf(fabricFeeds["defaultSubject"])
    );
    const biorxivSubjectLabelDefault = biorxivSubjectLabels[
        (props.usedSubject > -1) ? props.usedSubject : (
            (biorxivSubjectLabelsDefaultSystem > -1)
            ? biorxivSubjectLabelsDefaultSystem
            : 0
        )
    ];

    return (
        <div
            id="form-subject-outer"
            title="choose a feed for the sifting"
        >
            <label
                id="form-subject-label"
                htmlFor="form-subject-selection"
            >
                <span
                    id="form-subject-title"
                >
                    biorxiv feed:
                </span>
            </label>
            <select
                id="form-subject-selection"
                name={subjectName}
                defaultValue={biorxivSubjectLabelDefault}
            >
                <button><selectedcontent></selectedcontent></button>
                {biorxivSubjectLabels.map(subjectLabel =>
                    <option key={subjectLabel} value={subjectLabel}>
                        {utilsToSubjectView(subjectLabel)}
                    </option>
                )}
            </select>
        </div>
    );
}

export { FormSubject as default };
