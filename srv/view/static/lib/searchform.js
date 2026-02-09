/*
 * The form to make a question on a feed to be sent to LLM.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
import FormExplained from "arxifter/biorxiv/formexplained.js";
import FormQuery from "arxifter/biorxiv/formquery.js";
import FormSubject from "arxifter/biorxiv/formsubject.js";
import FormSubmit from "arxifter/biorxiv/formsubmit.js";
class SearchForm extends React.Component {
  constructor(props) {
    super(props);
    this.formRef = React.createRef();
    this.formQueryRef = React.createRef();
    this.hasUserSet = props.hasUserSet;
    this.isUserGuest = props.isUserGuest;
    this.getUser = props.getUser;
    this.openPopupUsers = props.openPopupUsers;
    this.appendSearch = props.appendSearch;
    this.explaining = props.getExplaining();
    this.usedSubject = props.getUsedSubject();
    this.setOnSearch = props.setOnSearch;
    this.getAutoFocusTA = props.getAutoFocusTA;
    this.dataNameQuery = "queryContent";
    this.dataNameExplained = "toExplain";
    this.dataNameSubject = "selectedBiorxivSubject";
    this.state = {
      submitDisabled: false,
      followup: false
    };
    this.setSubmitDisabled = val => {
      this.setState({
        submitDisabled: val
      });
    };
    this.setFollowup = val => {
      this.setState({
        followup: val
      });
    };
    this.gotEmptyQuery = () => {
      this.formQueryRef.current?.setUnderEmpty(true);
    };
    this.setAutoFocus = toAutoFocus => {
      this.formQueryRef.current?.setAutoFocus(toAutoFocus);
    };
    this.handleSubmit = e => {
      e.preventDefault();
      this.submitQuery(e.target);
    };
    this.followSubmit = () => {
      if (!this.state.followup) {
        return;
      }
      this.setFollowup(false);
      if (!this.hasUserSet()) {
        return;
      }
      if (!this.formRef.current) {
        return;
      }
      this.submitQuery(this.formRef.current);
    };
    this.prepareParams = (queryText, toExplain, hsVal) => {
      const fabricQuery = getFabricQuery();
      let queryDict = {};
      queryDict[fabricQuery["queryText"]] = queryText;
      queryDict[fabricQuery["toExplain"]] = toExplain;
      queryDict[fabricQuery["userId"]] = this.getUser();
      queryDict[fabricQuery["isGuest"]] = this.isUserGuest();
      queryDict[hsVal] = true;
      return queryDict;
    };
    this.submitQuery = form => {
      const formData = new FormData(form);
      const formJson = Object.fromEntries(formData.entries());
      const subjectId = formJson[this.dataNameSubject];
      const queryText = formJson[this.dataNameQuery].trim();
      const toExplain = typeof formJson[this.dataNameExplained] !== "undefined";
      if (queryText.length == 0) {
        if (form[this.dataNameQuery].value != "") {
          form[this.dataNameQuery].value = "";
        }
        this.gotEmptyQuery();
        return;
      }
      if (!this.hasUserSet()) {
        this.openPopupUsers(true);
        return;
      }
      this.setSubmitDisabled(true);
      this.setOnSearch(subjectId, toExplain);
      this.appendSearch(false, {
        subject: subjectId,
        query: queryText
      });
      const urlPrefix = getFabricView()["pathPrefix"];
      const urlInfix = utilsGetQueryParts().join("/");
      const wsForm = window.location.protocol == "https:" ? "wss:" : "ws:";
      const wsUri = wsForm + window.location.host + [urlPrefix, urlInfix, subjectId].join("/");
      let infoProvided = false;
      let connectionOpened = false;
      let websocket = null;
      try {
        websocket = new WebSocket(wsUri);
      } catch (error) {
        this.setSubmitDisabled(false);
        this.appendSearch(true, error);
      }
      websocket.onerror = error => {
        infoProvided = true;
        this.setSubmitDisabled(false);
        if (!connectionOpened) {
          this.appendSearch(true, "could not connect to server");
        } else {
          this.appendSearch(true, error);
        }
        try {
          websocket.close();
        } catch (e) {}
      };
      websocket.onopen = () => {
        connectionOpened = true;
        websocket.onclose = () => {
          this.setSubmitDisabled(false);
          if (!infoProvided) {
            infoProvided = true;
            this.appendSearch(true, "connection to server lost");
          }
        };
        const fabricHandshake = getFabricHandshake();
        const repeatHandshake = fabricHandshake["firstBits"] - 1;
        let hsVal = 2;
        for (let i = repeatHandshake; i > 0; i--) {
          hsVal *= 4;
          hsVal += 2;
        }
        let iterCount = fabricHandshake["count"] - 1;
        websocket.onmessage = evt => {
          const message = JSON.parse(evt.data);
          if (iterCount > 0) {
            hsVal = Math.abs(hsVal - message);
            websocket.send(hsVal.toString(10));
          } else if (iterCount == 0) {
            hsVal = Math.abs(hsVal - message).toString(10);
            const queryDict = this.prepareParams(queryText, toExplain, hsVal);
            websocket.send(JSON.stringify(queryDict));
          } else if (iterCount == -1) {
            infoProvided = true;
            this.setSubmitDisabled(false);
            this.appendSearch(true, message);
            try {
              websocket.close();
            } catch (e) {}
          }
          iterCount -= 1;
        };
        websocket.send(hsVal.toString(10));
      };
    };
  }
  render() {
    return /*#__PURE__*/React.createElement("form", {
      ref: this.formRef,
      id: "search-form",
      method: "post",
      onSubmit: this.handleSubmit
    }, /*#__PURE__*/React.createElement(FormQuery, {
      ref: this.formQueryRef,
      dataName: this.dataNameQuery,
      autoFocus: this.getAutoFocusTA()
    }, /*#__PURE__*/React.createElement(FormExplained, {
      dataName: this.dataNameExplained,
      explaining: this.explaining
    })), /*#__PURE__*/React.createElement("div", {
      id: "search-form-bottom"
    }, /*#__PURE__*/React.createElement(FormSubject, {
      dataName: this.dataNameSubject,
      usedSubject: this.usedSubject
    }), /*#__PURE__*/React.createElement(FormSubmit, {
      disabled: this.state.submitDisabled
    })));
  }
}
export { SearchForm as default };
