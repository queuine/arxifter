/*
 * Functions to access the browser local storage.
 */

// the effective prefix of item names
function storageGetPrefix(prefix) {
    const separator = ".";

    if ([null, ""].indexOf(prefix) > -1) {
        return "";
    }
    if (prefix.endsWith(separator)) {
        return prefix;
    }
    return prefix + separator;
};

// name for the item keeping the last searches
function storageGetLabelSearches(prefix) {
    return storageGetPrefix(prefix) + "searchesLast";
};

// save the last searches
function storageSaveSearches(prefix, searchList, maxCount) {
    let searchesToSave = [];
    searchList.slice(-maxCount).forEach((item) => {
        if (
            (item.question !== null)
            && (item.answers.length != 0)
            && (
                (
                    utilsIsDict(item.answers[0])
                    && (item.answers[0][utilsGetSuggestionKey()] === true)
                )
                || (
                    utilsIsArray(item.answers[0])
                    && (item.answers[0].length > 0)
                    && (!utilsIsString(item.answers[0][0]))
                )
            )
        ) {
            searchesToSave.push(item);
        }
    });
    localStorage.setItem(
        storageGetLabelSearches(prefix),
        JSON.stringify(searchesToSave)
    );
};

// take the last searches
function storageLoadSearches(prefix) {
    const storedSearches = localStorage.getItem(
        storageGetLabelSearches(prefix)
    );
    if (storedSearches === null) {
        return [];
    }
    let parsedSearches = [];
    try {
        parsedSearches = JSON.parse(storedSearches);
    } catch (e) {
        parsedSearches = [];
    }
    return parsedSearches;
};

// remove the last searches
function storageCleanSearches(prefix) {
    localStorage.removeItem(
        storageGetLabelSearches(prefix)
    );
};

// name for the item keeping the setup related to users
function storageGetItemNameUsers() {
    return "setupUsers";
};

// name for the item keeping the setup related to making queries
function storageGetItemNameAsking() {
    return "setupAsking";
};

// name for the item keeping the setup related to saving queries
function storageGetItemNameSaving() {
    return "setupSaving";
};

// the key for value of whether the user is guest
function storageGetKeyIsGuest() {
    return "asGuest";
};

// the key for value of whether results should be explained by LLM
function storageGetKeyExplaining() {
    return "toExplain";
};

// the key for value of the default feed for the queries
function storageGetKeySiftedFeed() {
    return "feedLabel";
};

// the key for value of whether results should be saved locally
function storageGetKeySaveSearches() {
    return "searchesLast";
};

// take default values of the user-related setup
function storageGetDefaultSetupUsers() {
    return {
        [storageGetKeyIsGuest()]: false,
    };
};

// take default values of the asking-related setup
function storageGetDefaultSetupAsking() {
    return {
        [storageGetKeyExplaining()]: true,
        [storageGetKeySiftedFeed()]: "",
    };
};

// take default values of the saving-related setup
function storageGetDefaultSetupSaving() {
    return {
        [storageGetKeySaveSearches()]: true
    };
};

// generally taking a setup
function storageLoadSetup(prefix, label, defaultSetup) {
    const storedSetup = localStorage.getItem(
        storageGetPrefix(prefix) + label
    );
    if (storedSetup === null) {
        return defaultSetup;
    }

    try {
        let parsedSetup = JSON.parse(storedSetup);
        if (!utilsIsDict(parsedSetup)) {
            return defaultSetup;
        }
        for (const [key, value] of Object.entries(defaultSetup)) {
            if (parsedSetup[key] === undefined) {
                parsedSetup[key] = value;
            }
        }
        return parsedSetup;
    } catch (e) {}

    return defaultSetup;
};

// taking the user-related setup
function storageLoadSetupUsers(prefix) {
    return storageLoadSetup(
        prefix,
        storageGetItemNameUsers(),
        storageGetDefaultSetupUsers()
    );
};

// taking the asking-related setup
function storageLoadSetupAsking(prefix) {
    return storageLoadSetup(
        prefix,
        storageGetItemNameAsking(),
        storageGetDefaultSetupAsking()
    );
};

// taking the saving-related setup
function storageLoadSetupSaving(prefix) {
    return storageLoadSetup(
        prefix,
        storageGetItemNameSaving(),
        storageGetDefaultSetupSaving()
    );
};

// generally saving a setup
function storageSaveSetup(prefix, label, setup) {
    localStorage.setItem(
        storageGetPrefix(prefix) + label,
        JSON.stringify(setup)
    );
};

// saving the user-related setup
function storageSaveSetupUsers(prefix, key, value) {
    let setup = storageLoadSetupUsers(prefix);
    setup[key] = value;
    storageSaveSetup(
        prefix,
        storageGetItemNameUsers(),
        setup
    );
};

// saving the asking-related setup
function storageSaveSetupAsking(prefix, key, value) {
    let setup = storageLoadSetupAsking(prefix);
    setup[key] = value;
    storageSaveSetup(
        prefix,
        storageGetItemNameAsking(),
        setup
    );
};

// saving the saving-related setup
function storageSaveSetupSaving(prefix, key, value) {
    let setup = storageLoadSetupSaving(prefix);
    setup[key] = value;
    storageSaveSetup(
        prefix,
        storageGetItemNameSaving(),
        setup
    );
};

// take whether the user is supposed to be a guest
function storageLoadSetupIsGuest(prefix) {
    return storageLoadSetupUsers(prefix)[storageGetKeyIsGuest()];
};

// take whether LLM should explain its choices
function storageLoadSetupExplaining(prefix) {
    return storageLoadSetupAsking(prefix)[storageGetKeyExplaining()];
};

// take the default feed for the sifting
function storageLoadSetupSiftedFeed(prefix) {
    return storageLoadSetupAsking(prefix)[storageGetKeySiftedFeed()];
};

// take whether the last searches should be saved locally
function storageLoadSetupSaveSearches(prefix) {
    return storageLoadSetupSaving(prefix)[storageGetKeySaveSearches()];
};

// save whether the user is supposed to be a guest
function storageSaveSetupIsGuest(prefix, value) {
    storageSaveSetupUsers(prefix, storageGetKeyIsGuest(), value)
};

// save whether LLM should explain its choices
function storageSaveSetupExplaining(prefix, value) {
    storageSaveSetupAsking(prefix, storageGetKeyExplaining(), value)
};

// save the default feed for the sifting
function storageSaveSetupSiftedFeed(prefix, value) {
    storageSaveSetupAsking(prefix, storageGetKeySiftedFeed(), value);
};

// save whether the last searches should be saved locally
function storageSaveSetupSaveSearches(prefix, value) {
    storageSaveSetupSaving(prefix, storageGetKeySaveSearches(), value);
};
