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

// name for the item keeping the last sifts
function storageGetLabelSifts(prefix) {
    return storageGetPrefix(prefix) + "siftsLast";
};

// save the last sifts
function storageSaveSifts(prefix, siftingList, maxCount) {
    let siftsToSave = [];
    siftingList.slice(-maxCount).forEach((item) => {
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
            siftsToSave.push(item);
        }
    });
    localStorage.setItem(
        storageGetLabelSifts(prefix),
        JSON.stringify(siftsToSave)
    );
};

// take the last sifts
function storageLoadSifts(prefix, jsonrepair) {
    const storedSifts = localStorage.getItem(
        storageGetLabelSifts(prefix)
    );
    if (storedSifts === null) {
        return [];
    }
    let parsedSifts = [];
    let parsingError = false;
    try {
        parsedSifts = JSON.parse(storedSifts);
    } catch (e) {
        parsedSifts = [];
        parsingError = true;
    }
    if (parsingError) {
        // There should be no error during the parsing of the stored list;
        // but browsers may decide that the stored data are too big,
        // possibly truncating it (generally doing something to it).
        // And since such a truncating occurred once during testing,
        // it is better to consider it as a possibility.
        try {
            parsedSifts = JSON.parse(
                jsonrepair(storedSifts)
            );
        } catch (e) {
            parsedSifts = [];
        }
    }
    return utilsCheckSiftsList(parsedSifts);
};

// remove the last sifts
function storageCleanSifts(prefix) {
    localStorage.removeItem(
        storageGetLabelSifts(prefix)
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

// name for the item keeping the setup related to UI configuration
function storageGetItemNameUI() {
    return "setupUI";
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
function storageGetKeySaveSifts() {
    return "siftsLast";
};

// the key for value of whether text area should get auto-focused
function storageGetKeyAutoFocusTA() {
    return "autoFocusTA";
};

// take default values of the user-related setup
function storageGetDefaultSetupUsers() {
    return {
        [storageGetKeyIsGuest()]: true,
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
        [storageGetKeySaveSifts()]: true
    };
};

// take default values of the UI-related setup
function storageGetDefaultSetupUI() {
    return {
        [storageGetKeyAutoFocusTA()]: true
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

// taking the UI-related setup
function storageLoadSetupUI(prefix) {
    return storageLoadSetup(
        prefix,
        storageGetItemNameUI(),
        storageGetDefaultSetupUI()
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

// saving the UI-related setup
function storageSaveSetupUI(prefix, key, value) {
    let setup = storageLoadSetupUI(prefix);
    setup[key] = value;
    storageSaveSetup(
        prefix,
        storageGetItemNameUI(),
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

// take whether the last sifts should be saved locally
function storageLoadSetupSaveSifts(prefix) {
    return storageLoadSetupSaving(prefix)[storageGetKeySaveSifts()];
};

// take whether the query text area should be auto-focused
function storageLoadSetupAutoFocusTA(prefix) {
    return storageLoadSetupUI(prefix)[storageGetKeyAutoFocusTA()];
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

// save whether the last sifts should be saved locally
function storageSaveSetupSaveSifts(prefix, value) {
    storageSaveSetupSaving(prefix, storageGetKeySaveSifts(), value);
};

// save whether the query text area should be auto-focused
function storageSaveSetupAutoFocusTA(prefix, value) {
    storageSaveSetupUI(prefix, storageGetKeyAutoFocusTA(), value);
};
