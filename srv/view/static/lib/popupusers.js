/*
 * Setting of user id and/or guest status.
 * It is done within a popup-like layer.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
class PopupUsers extends React.Component {
  constructor(props) {
    super(props);
    this.closePopup = props.closePopup;
    this.setupGuestSession = props.setupGuestSession;
    this.idRemembered = props.getIdRemembered();
    this.noteText = getFabricNotices()["noteUsers"];
    this.withGuest = getFabricUsers()["withGuest"];
    this.sessionStates = {
      NO: 0,
      OK: 1,
      KO: 2
    };
    this.inputRef = React.createRef();
    this.agreeRef = React.createRef();
    this.state = {
      userId: this.idRemembered,
      toRemember: this.idRemembered ? true : false,
      asGuest: props.getIsGuest() && this.withGuest,
      hasAgreed: false,
      isLaborer: false,
      guestId: "",
      sessionState: this.sessionStates.NO
    };
    this.getRememberId = () => {
      return {
        toRemember: this.state.toRemember,
        userId: this.state.userId
      };
    };
    this.hasUserSet = () => {
      if (this.state.asGuest) {
        return this.state.sessionState == this.sessionStates.OK;
      }
      return this.state.userId != "";
    };
    this.isUserGuest = () => {
      return this.state.asGuest;
    };
    this.getUser = () => {
      if (this.state.asGuest) {
        return this.state.guestId;
      }
      return this.state.userId;
    };
    this.setGuestId = val => {
      this.setState({
        guestId: val
      });
    };
    this.setSessionState = val => {
      this.setState({
        sessionState: val
      });
    };
    this.resetSession = () => {
      this.setSessionState(this.sessionStates.NO);
      if (this.agreeRef.current?.checked) {
        this.agreeRef.current?.click();
      }
    };
  }
  render() {
    const idRetentionLabel = "The id is kept in a cookie when it is remembered.";
    const agreeEvaluationLabel = "Agree to the evaluation-only use.";
    return /*#__PURE__*/React.createElement("div", {
      open: true,
      className: "arxifter-popup"
    }, /*#__PURE__*/React.createElement("div", {
      id: "popup-users-top"
    }, getFabricNotices()["noteUsersHtml"] ? /*#__PURE__*/React.createElement("span", {
      dangerouslySetInnerHTML: {
        __html: this.noteText
      }
    }) : this.noteText), /*#__PURE__*/React.createElement("div", {
      id: "popup-users-form"
    }, /*#__PURE__*/React.createElement("button", {
      id: "popup-users-form-user",
      title: this.state.asGuest ? "Click to switch to the regular-user mode." : "Fill in your user id.",
      htmlFor: "popup-users-input-user",
      className: this.state.asGuest ? "popup-users-form-label " + "popup-users-form-label-that" : "popup-users-form-label " + "popup-users-form-label-this",
      onClick: e => {
        const currentAsGuest = this.state.asGuest;
        this.setState({
          asGuest: false
        });
        if (!currentAsGuest) {
          this.inputRef.current?.focus();
        }
      }
    }, "User id"), /*#__PURE__*/React.createElement("input", {
      type: "password",
      size: "32",
      className: this.state.asGuest && "popup-users-form-label-invisible",
      id: "popup-users-input-user",
      title: "Fill in your user id if you already have one.",
      ref: this.inputRef,
      autofocus: this.state.asGuest ? false : 'true',
      disabled: this.state.asGuest ? true : false,
      value: this.state.userId,
      onChange: e => {
        this.setState({
          userId: e.target.value
        });
      }
    }), /*#__PURE__*/React.createElement("div", null), /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      id: "popup-users-checkbox-remember",
      title: idRetentionLabel,
      disabled: this.state.asGuest ? true : false,
      checked: this.state.toRemember,
      onChange: e => {
        this.setState({
          toRemember: e.target.checked
        });
      }
    }), /*#__PURE__*/React.createElement("label", {
      title: idRetentionLabel,
      htmlFor: "popup-users-checkbox-remember",
      className: this.state.asGuest ? "popup-users-form-label-inner " + "popup-users-form-label-disabled" : "popup-users-form-label-inner"
    }, "remember the id"), this.withGuest && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      id: "popup-users-separator"
    }, /*#__PURE__*/React.createElement("hr", null)), /*#__PURE__*/React.createElement("button", {
      id: "popup-users-form-guest",
      title: this.state.asGuest ? agreeEvaluationLabel : "Click to switch to the guest-user mode.",
      className: this.state.asGuest ? "popup-users-form-label " + "popup-users-form-label-this" : "popup-users-form-label " + "popup-users-form-label-that",
      onClick: e => {
        const currentAsGuest = this.state.asGuest;
        this.setState({
          asGuest: true
        });
        if (currentAsGuest) {
          this.agreeRef.current?.focus();
        }
      }
    }, "Guest"), /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      id: "popup-users-checkbox-guest-agrees",
      title: agreeEvaluationLabel,
      ref: this.agreeRef,
      autofocus: this.state.asGuest ? 'true' : false,
      disabled: this.state.asGuest ? false : true,
      onChange: e => {
        this.setState({
          hasAgreed: e.target.checked
        });
        this.setupGuestSession(e.target.checked);
      }
    }), /*#__PURE__*/React.createElement("label", {
      title: "Contact us in case of a regular use.",
      htmlFor: "popup-users-checkbox-guest-agrees",
      className: this.state.asGuest ? "popup-users-form-label-inner" : "popup-users-form-label-inner " + "popup-users-form-label-disabled"
    }, "I agree to evaluation use."), /*#__PURE__*/React.createElement("div", {
      id: "popup-users-empty-filler"
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      id: "popup-users-checkbox-is-laborer",
      disabled: this.state.asGuest ? false : true,
      onChange: e => {
        this.setState({
          isLaborer: e.target.checked
        });
      }
    })), /*#__PURE__*/React.createElement("div", {
      id: "popup-users-session-notice",
      className: this.state.asGuest ? "popup-users-form-label-inner" : "popup-users-form-label-inner " + "popup-users-form-label-invisible"
    }, this.state.sessionState == this.sessionStates.NO && "guest session is not set", this.state.sessionState == this.sessionStates.OK && "guest session is set up", this.state.sessionState == this.sessionStates.KO && "guest session set up failed"))), /*#__PURE__*/React.createElement("div", {
      className: "arxifter-popup-bottom"
    }, /*#__PURE__*/React.createElement("button", {
      className: "arxifter-popup-close",
      onClick: e => {
        this.closePopup();
      }
    }, "Close")));
  }
}
export { PopupUsers as default };
