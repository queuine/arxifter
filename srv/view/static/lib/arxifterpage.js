/*
 * The top layer of the UI.
 * Besides references to lower UI levels and minor utilities,
 * it contains functions for setting guest sessions.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
import ArxifterTop from "arxifter/biorxiv/arxiftertop.js";
import ArxifterPopup from "arxifter/biorxiv/arxifterpopup.js";
import SearchForm from "arxifter/biorxiv/searchform.js";
import SearchList from "arxifter/biorxiv/searchlist.js";
function ArxifterPage() {
  let searchFormRef = React.createRef();
  let searchesRef = React.createRef();
  let dialogRef = React.createRef();
  let popupRef = React.createRef();
  const appendSearch = (isAnswer, payload) => {
    if (isAnswer) {
      const fabricAnswer = getFabricAnswer();
      const answerKey = fabricAnswer["llmResponse"];
      let data_content = null;
      try {
        if (typeof payload[answerKey] !== "undefined") {
          data_content = payload[answerKey];
        } else {
          data_content = payload;
        }
      } catch (e) {
        data_content = payload;
      }
      searchesRef.current.addSearch(true, data_content);
    } else {
      searchesRef.current.addSearch(false, payload);
    }
  };
  const hasUserSet = () => {
    return popupRef.current?.hasUserSet();
  };
  const isUserGuest = () => {
    return popupRef.current?.isUserGuest();
  };
  const getUser = () => {
    return popupRef.current?.getUser();
  };
  const openPopup = (followSearch = false) => {
    dialogRef.current?.showModal();
    searchFormRef.current?.setFollowup(followSearch);
  };
  const closePopup = () => {
    dialogRef.current?.close();
  };
  const followPopup = () => {
    searchFormRef.current?.followSubmit();
  };
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
    const cookieExp = getFabricUi()["retain"];
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
    const cookieExp = getFabricUi()["retain"];
    if (cookieExp <= 0) {
      utilsDelCookieValue(cookieName);
      return;
    }
    const rememberId = popupRef.current?.getRememberId();
    const cookieValue = rememberId ? rememberId["userId"] : "";
    const toRemember = rememberId ? rememberId["toRemember"] : false;
    if (!toRemember || cookieValue == "") {
      utilsDelCookieValue(cookieName);
      return;
    }
    utilsSetCookieValue(cookieName, cookieValue, cookieExp);
  };
  const getExplaining = () => {
    const cookieName = getFabricUi()["toExplain"];
    return utilsGetCookieValue(cookieName) == "no" ? false : true;
  };
  const setExplaining = toExplain => {
    const cookieName = getFabricUi()["toExplain"];
    const cookieExp = getFabricUi()["retain"];
    if (cookieExp <= 0) {
      utilsDelCookieValue(cookieName);
      return;
    }
    const cookieValue = toExplain ? "yes" : "no";
    utilsSetCookieValue(cookieName, cookieValue, cookieExp);
  };
  const getUsedSubject = () => {
    const cookieName = getFabricUi()["subjectName"];
    const usedSubject = utilsGetCookieValue(cookieName);
    if (usedSubject == "") {
      return -1;
    }
    return getFabricFeeds()["subjects"].indexOf(usedSubject);
  };
  const setUsedSubject = subjectId => {
    const cookieName = getFabricUi()["subjectName"];
    const cookieExp = getFabricUi()["retain"];
    if (cookieExp <= 0) {
      utilsDelCookieValue(cookieName);
      return;
    }
    utilsSetCookieValue(cookieName, subjectId, cookieExp);
  };
  const setOnSearch = (subjectId, toExplain) => {
    setUsedSubject(subjectId);
    setExplaining(toExplain);
  };
  const annealStrings = (toProcess, toAlign) => {
    const toAlignUse = toAlign.repeat(Math.ceil(toProcess.length / toAlign.length));
    let result = [];
    for (let ind = 0; ind < toProcess.length; ind += 2) {
      let valIn1 = parseInt(toProcess.substring(ind, ind + 2), 16);
      let valIn2 = parseInt(toAlignUse.substring(ind, ind + 2), 16);
      result.push((valIn1 ^ valIn2).toString(16).padStart(2, "0"));
    }
    return result.join("");
  };

  // setting up the guest session
  const setupGuestSession = hasAgreed => {
    if (!popupRef.current) {
      return;
    }
    const sessionNO = popupRef.current?.sessionStates.NO;
    const sessionOK = popupRef.current?.sessionStates.OK;
    const sessionKO = popupRef.current?.sessionStates.KO;
    if (!getFabricUsers()["withGuest"]) {
      popupRef.current?.setSessionState(sessionNO);
      return;
    }
    const asGuest = popupRef?.current.state.asGuest;
    const isLaborer = popupRef?.current.state.isLaborer;
    if (asGuest !== true || hasAgreed !== true) {
      popupRef.current?.setSessionState(sessionNO);
      return;
    }
    const randHex = utilsRandomizeHex();
    const clues = getFabricSession();
    const clueStr = randHex.repeat(Math.ceil(clues["clueLen"] / randHex.length)).substring(0, clues["clueLen"]);
    let postDict = {};
    postDict[clues["clueVis"]] = hasAgreed;
    postDict[clues["clueHid"]] = isLaborer;
    postDict[clues["clueStr"]] = clueStr;
    const postData = JSON.stringify(postDict);
    const postUrl = [getFabricUrls()["pathPrefix"], utilsGetSessionParts().join("/")].join("/");
    fetch(postUrl, {
      method: 'post',
      body: postData,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    }).then(response => {
      if (response.status != 200) {
        return null;
      }
      return response.json();
    }).then(result => {
      const resKey = clues["provided"];
      if (!result) {
        popupRef.current?.setSessionState(sessionKO);
      } else if (result[resKey]?.length > 0) {
        popupRef.current?.setGuestId(annealStrings(result[resKey][0], clueStr));
        popupRef.current?.setSessionState(sessionOK);
      } else {
        popupRef.current?.setSessionState(sessionKO);
      }
    }).catch(error => {
      popupRef.current?.setSessionState(sessionKO);
    });
  };
  return /*#__PURE__*/React.createElement("div", {
    id: "arxifter-page"
  }, /*#__PURE__*/React.createElement(ArxifterTop, {
    openPopup: openPopup
  }), /*#__PURE__*/React.createElement("dialog", {
    ref: dialogRef,
    onCancel: () => {
      setIdRemembering();
      followPopup();
    },
    id: "arxifter-page-popup"
  }, /*#__PURE__*/React.createElement(ArxifterPopup, {
    ref: popupRef,
    getIdRemembered: getIdRemembered,
    setupGuestSession: setupGuestSession,
    closePopup: () => {
      closePopup();
      setIdRemembering();
      followPopup();
    }
  })), /*#__PURE__*/React.createElement(SearchForm, {
    ref: searchFormRef,
    getExplaining: getExplaining,
    getUsedSubject: getUsedSubject,
    setOnSearch: setOnSearch,
    appendSearch: appendSearch,
    hasUserSet: hasUserSet,
    isUserGuest: isUserGuest,
    getUser: getUser,
    openPopup: openPopup
  }), /*#__PURE__*/React.createElement(SearchList, {
    ref: searchesRef
  }));
}
export { ArxifterPage as default };
