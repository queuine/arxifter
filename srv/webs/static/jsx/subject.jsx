
function BiorxivSubject({subjectName}) {
    const biorxivSubjectLabels = getBiorxivSubjects()
    const biorxivSubjectLabelDefault = biorxivSubjectLabels[0];

    return (
        <label>
            <span id="biorxiv-subject-title">biorxiv subject:</span>
            <select
                id="biorxiv-subject-selection"
                name={subjectName}
                defaultValue={biorxivSubjectLabelDefault}
            >
                {biorxivSubjectLabels.map(subjectLabel =>
                    <option key={subjectLabel} value={subjectLabel}>
                        {toSubjectView(subjectLabel)}
                    </option>
                )}
            </select>
        </label>
    );
}
