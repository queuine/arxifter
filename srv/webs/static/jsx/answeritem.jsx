
function BiorxivAnswerItem(props) {
    const item = props.content;

    function isString(key) {
        return ((typeof key === "string") || (key instanceof String));
    }

    function isDict(item) {
        return (
            item !== undefined && item !== null && item.constructor == Object
        );
    }

    function getKey(item, key) {
        if (key in item) {
            return key;
        }
        if (!isString(key)) {
            return null;
        }
        if (key.length == 0) {
            return null;
        }

        const form_capit = key.charAt(0).toUpperCase() + key.slice(1);
        if (form_capit in item) {
            return form_capit;
        }
        const form_upper = key.toUpperCase();
        if (form_upper in item) {
            return form_upper;
        }
        return null;
    }

    function hasValue(item, key) {
        return (getKey(item, key) !== null);
    }

    function getValue(item, key) {
        if (getKey(item, key) !== null) {
            return item[getKey(item, key)];
        }
        return "unknown";
    }

    function getHeaderKeys() {
        return [
            "doi",
            "author",
            "authors"
        ]
    }

    function getReasonKeys() {
        return [
            "reason",
            "reasons",
            "selection_reason",
            "selection_reasons"
        ];
    }

    function getSpareKeys(item) {
        let spareKeys = [];
        const flankKeys = ["title"]
            .concat(getHeaderKeys(), getReasonKeys());

        Object.entries(item).map(([key, val]) => {
            if (!isString(key)) {
                spareKeys.push(JSON.stringify(key, null, 0));
            } else if (flankKeys.indexOf(key.toLowerCase()) < 0) {
                spareKeys.push(key);
            }
        });
        return spareKeys;
    }

    return (
        <div class="answer-item">
        {
            hasValue(item, "title")
            ?
            <div>
                <span class="answer-item-key">title:</span>
                <span class="answer-title">{getValue(item, "title")}</span>
            </div>
            :
            ""
        }
        {
            getHeaderKeys().map((x, i) => (
                hasValue(item, x)
                ?
                <div key={i}>
                    <span class="answer-item-key">{x}:</span>
                    <span>{getValue(item, x)}</span>
                </div>
                :
                ""
            ))
        }
        {
            getSpareKeys(item).map((x, i) => (
                <div key={i}>
                    <span class="answer-item-key">{x}:</span>
                    <span>{item[x]}</span>
                </div>
            ))
        }
        {
            getReasonKeys().map((x, i) => (
                hasValue(item, x)
                ?
                <div key={i}>
                    <span class="answer-item-key">{x}:</span>
                    <span>{getValue(item, x)}</span>
                </div>
                :
                ""
            ))
        }
        </div>
    )
}
