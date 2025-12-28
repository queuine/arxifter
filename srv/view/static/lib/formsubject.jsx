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
        <label>
            <span id="form-subject-title">biorxiv subject:</span>
            <select
                id="form-subject-selection"
                name={subjectName}
                defaultValue={biorxivSubjectLabelDefault}
            >
                {biorxivSubjectLabels.map(subjectLabel =>
                    <option key={subjectLabel} value={subjectLabel}>
                        {utilsToSubjectView(subjectLabel)}
                    </option>
                )}
            </select>
        </label>
    );
}

export { FormSubject as default };
