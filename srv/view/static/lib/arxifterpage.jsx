/*
 * The top layer of the UI.
 * Besides references to lower UI levels and minor utilities,
 * it contains functions for setting guest sessions.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import ArxifterTop from "arxifter/biorxiv/arxiftertop.js";
import PopupSetting from "arxifter/biorxiv/popupsetting.js";
import PopupUsers from "arxifter/biorxiv/popupusers.js";
import SearchForm from "arxifter/biorxiv/searchform.js";
import SearchList from "arxifter/biorxiv/searchlist.js";

function ArxifterPage() {
    let searchFormRef = React.createRef();
    let searchesRef = React.createRef();
    let dialogSettingRef = React.createRef();
    let popupSettingRef = React.createRef();
    let dialogUsersRef = React.createRef();
    let popupUsersRef = React.createRef();

    // adds new queries and answers to the search list
    const appendSearch = (isAnswer, payload) => {
        if (isAnswer) {
            const fabricAnswer = getFabricAnswer();
            const answerKey = fabricAnswer["llmResponse"];
            let data_content = null;
            try {
                if ((typeof payload[answerKey]) !== "undefined") {
                    data_content = payload[answerKey];
                } else {
                    data_content = payload;
                }
            } catch (e) {
                data_content = payload;
            }
            try {
                if (payload[utilsGetSessionGoneKey()] === true) {
                    popupUsersRef.current?.resetSession();
                }
            } catch (e) {}
            searchesRef.current?.addSearch(true, data_content);
            searchesRef.current?.saveLastSearches();
        } else {
            searchesRef.current?.addSearch(false, payload);
        }
    };

    // prefix for item names stored in browser local storage
    const getStoragePrefix = () => {
        return getFabricUi()["storagePrefix"];
    };

    // local storage: setting for whether last searches should be saved
    const getSaveLastSearches = () => {
        return storageLoadSetupSaveSearches(getStoragePrefix());
    };
    const setSaveLastSearches = (toSave) => {
        storageSaveSetupSaveSearches(getStoragePrefix(), toSave);
        searchesRef.current?.setToSaveLastSearches(toSave);
    };
    const saveLastSearches = (toSave) => {
        searchesRef.current?.saveLastSearches(toSave);
    };

    // functions for taking the current user
    const hasUserSet = () => {
        return popupUsersRef.current?.hasUserSet();
    };
    const isUserGuest = () => {
        return popupUsersRef.current?.isUserGuest();
    };
    const getUser = () => {
        return popupUsersRef.current?.getUser();
    };

    // open/close the setting popup
    const openPopupSetting = () => {
        dialogSettingRef.current?.showModal();
    };
    const closePopupSetting = () => {
        dialogSettingRef.current?.close();
    };

    // open/close the users popup
    const openPopupUsers = (followSearch = false) => {
        dialogUsersRef.current?.showModal();
        searchFormRef.current?.setFollowup(followSearch);
    };
    const closePopupUsers = () => {
        dialogUsersRef.current?.close();
    };
    // actions to be done after the popup is closed;
    // it is used for starting a sifting if the users-popup
    // was opened b/c the user had neither a user id filled in,
    // nor a guest session set up;
    const followPopupUsers = () => {
        searchFormRef.current?.followSubmit();
    };

    // saving/loading the user id to/from cookies
    const getIdRemembered = () => {
        const cookieName = getFabricUi()["userId"];
        const cookieValue = utilsGetCookieValue(cookieName);
        if (cookieValue == "") {
            // no user id was stored;
            return "";
        }
        // if here, some user id was stored;
        // if the id should be remembered, it gets auto-prolonged;
        // otherwise it gets auto-deleted;
        const cookieExp = getFabricUi()["retain_user"];
        if (cookieExp <= 0) {
            // it gets deleted and forgotten;
            //utilsSetCookieValue(cookieName, "", cookieExp);
            utilsDelCookieValue(cookieName);
            return "";
        }
        // if here, some id was stored and it has to be retained;
        utilsSetCookieValue(cookieName, cookieValue, cookieExp);
        return cookieValue;
    };
    const setIdRemembering = () => {
        const cookieName = getFabricUi()["userId"];
        const cookieExp = getFabricUi()["retain_user"];
        if (cookieExp <= 0) {
            utilsDelCookieValue(cookieName);
            return;
        }
        const rememberId = popupUsersRef.current?.getRememberId();
        const cookieValue = rememberId ? rememberId["userId"] : "";
        const toRemember = rememberId ? rememberId["toRemember"] : false;
        if ((!toRemember) || (cookieValue == "")) {
            utilsDelCookieValue(cookieName);
            return;
        }
        utilsSetCookieValue(cookieName, cookieValue, cookieExp);
    };

    // local storage: setting for whether the user is supposed to be a guest
    const getIsGuest = () => {
        return storageLoadSetupIsGuest(
            getStoragePrefix()
        );
    };
    const setIsGuest = () => {
        return storageSaveSetupIsGuest(
            getStoragePrefix(),
            isUserGuest()
        );
    };

    // actions to be done when the users-popup gets closed
    const onPopupUsersClosed = () => {
        setIsGuest();
        setIdRemembering();
        followPopupUsers();
    };

    // local storage: setting for whether LLM should explain its choices
    const getExplaining = () => {
        return storageLoadSetupExplaining(
            getStoragePrefix()
        );
    };
    const setExplaining = (toExplain) => {
        storageSaveSetupExplaining(
            getStoragePrefix(),
            toExplain
        );
    };

    // local storage: setting for the default feed to be sifted through
    const getUsedSubject = () => {
        const usedSubject = storageLoadSetupSiftedFeed(
            getStoragePrefix()
        );
        if (usedSubject == "") {
            return -1;
        }
        return getFabricFeeds()["subjects"].indexOf(usedSubject);
    };
    const setUsedSubject = (subjectId) => {
        storageSaveSetupSiftedFeed(
            getStoragePrefix(),
            subjectId
        );
    };

    // additional actions to be done when a query is asked
    const setOnSearch = (subjectId, toExplain) => {
        setUsedSubject(subjectId);
        setExplaining(toExplain);
    };

    // auxiliary function for setting guest sessions
    const annealStrings = (toProcess, toAlign) => {
        const toAlignUse = toAlign.repeat(
            Math.ceil(toProcess.length / toAlign.length)
        );
        let result = [];
        for (let ind = 0; ind < toProcess.length; ind += 2) {
            let valIn1 = parseInt(toProcess.substring(ind, (ind + 2)), 16);
            let valIn2 = parseInt(toAlignUse.substring(ind, (ind + 2)), 16);
            result.push((valIn1 ^ valIn2).toString(16).padStart(2, "0"));
        }
        return result.join("");
    };

    // setting up the guest session
    const setupGuestSession = (hasAgreed) => {
        if (!popupUsersRef.current) {
            return;
        }
        const sessionNO = popupUsersRef.current?.sessionStates.NO;
        const sessionOK = popupUsersRef.current?.sessionStates.OK;
        const sessionKO = popupUsersRef.current?.sessionStates.KO;

        if (!(getFabricUsers()["withGuest"])) {
            popupUsersRef.current?.setSessionState(sessionNO);
            return;
        }

        const asGuest = popupUsersRef.current?.state.asGuest;
        const isLaborer = popupUsersRef.current?.state.isLaborer;
        if ((asGuest !== true) || (hasAgreed !== true)) {
            popupUsersRef.current?.setSessionState(sessionNO);
            return;
        }

        const randHex = utilsRandomizeHex();
        const clues = getFabricSession();
        const clueStr = randHex.repeat(
            Math.ceil(clues["clueLen"] / randHex.length)
        ).substring(0, clues["clueLen"]);
        let postDict = {};
        postDict[clues["clueVis"]] = hasAgreed;
        postDict[clues["clueHid"]] = isLaborer;
        postDict[clues["clueStr"]] = clueStr;
        const postData = JSON.stringify(postDict);

        const postUrl = [
            getFabricServer()["pathPrefix"],
            utilsGetSessionParts().join("/")
        ].join("/");
        fetch(postUrl, {
            method: 'post',
            body: postData,
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        }).then((response) => {
            if (response.status != 200) {
                return null;
            }
            return response.json();
        }).then((result) => {
            const resKey = clues["provided"];
            if (!result) {
                popupUsersRef.current?.setSessionState(sessionKO);
            } else if (result[resKey]?.length > 0) {
                popupUsersRef.current?.setGuestId(
                    annealStrings(result[resKey][0], clueStr)
                );
                popupUsersRef.current?.setSessionState(sessionOK);
            } else {
                popupUsersRef.current?.setSessionState(sessionKO);
            }
        }).catch((error) => {
            popupUsersRef.current?.setSessionState(sessionKO);
        })
    };

    return (
        <div id="arxifter-page">
            <ArxifterTop
                openPopupSetting={openPopupSetting}
                openPopupUsers={openPopupUsers}
            />
            <dialog
                ref={dialogSettingRef}
                onCancel={() => {
                }}
                className="arxifter-page-popup"
            >
                <PopupSetting
                    ref={popupSettingRef}
                    getSaveLastSearches={getSaveLastSearches}
                    setSaveLastSearches={setSaveLastSearches}
                    saveLastSearches={saveLastSearches}
                    closePopup={() => {
                        closePopupSetting();
                    }}
                />
            </dialog>
            <dialog
                ref={dialogUsersRef}
                onCancel={() => {
                    onPopupUsersClosed();
                }}
                className="arxifter-page-popup"
            >
                <PopupUsers
                    ref={popupUsersRef}
                    getIdRemembered={getIdRemembered}
                    getIsGuest={getIsGuest}
                    setupGuestSession={setupGuestSession}
                    closePopup={() => {
                        closePopupUsers();
                        onPopupUsersClosed();
                    }}
                />
            </dialog>
            <SearchForm
                ref={searchFormRef}
                getExplaining={getExplaining}
                getUsedSubject={getUsedSubject}
                setOnSearch={setOnSearch}
                appendSearch={appendSearch}
                hasUserSet={hasUserSet}
                isUserGuest={isUserGuest}
                getUser={getUser}
                openPopupUsers={openPopupUsers}
            />
            <SearchList
                ref={searchesRef}
                searchList={
                    storageLoadSearches(getStoragePrefix())
                }
                getSaveLastSearches={getSaveLastSearches}
                getStoragePrefix={getStoragePrefix}
            />
        </div>
    );
}

export { ArxifterPage as default };
