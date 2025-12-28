/*
 * Setting of user id and/or guest status.
 * It is done within a popup-like layer.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

class ArxifterPopup extends React.Component {
    constructor(props) {
        super(props);
        this.closePopup = props.closePopup;
        this.setupGuestSession = props.setupGuestSession;
        this.idRemembered = props.getIdRemembered();
        this.noteText = getFabricPopup()["noteText"];
        this.withGuest = getFabricUsers()["withGuest"];
        this.sessionStates = {
            NO: 0,
            OK: 1,
            KO: 2
        }
        this.inputRef = React.createRef();
        this.agreeRef = React.createRef();
        this.state = {
            userId: this.idRemembered,
            toRemember: this.idRemembered ? true : false,
            asGuest: false,
            hasAgreed: false,
            isLaborer: false,
            guestId: "",
            sessionState: this.sessionStates.NO,
        };
        this.getRememberId = () => {
            return {
                toRemember: this.state.toRemember,
                userId: this.state.userId
            };
        };
        this.hasUserSet = () => {
            if (this.state.asGuest) {
                return (
                    this.state.sessionState == this.sessionStates.OK
                );
            }
            return (this.state.userId != "");
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
        this.setGuestId = (val) => {
            this.setState({
                guestId: val
            });
        };
        this.setSessionState = (val) => {
            this.setState({
                sessionState: val
            });
        };
    }

    render() {
        return (
            <div open id="arxifter-popup">
                <div id="arxifter-popup-top">
                    {this.noteText}
                </div>
                <div id="arxifter-popup-form">
                    <button
                        id="arxifter-popup-form-user"
                        title={
                            this.state.asGuest
                            ?
                            "Click to switch to the regular-user mode."
                            :
                            "Fill in the user id."
                        }
                        htmlFor="arxifter-popup-input-user"
                        className={
                            this.state.asGuest
                            ?
                            (
                                "arxifter-popup-form-label "
                                + "arxifter-popup-form-label-that"
                            )
                            :
                            (
                                "arxifter-popup-form-label "
                                + "arxifter-popup-form-label-this"
                            )
                        }
                        onClick={(e) => {
                            const currentAsGuest = this.state.asGuest;
                            this.setState({
                                asGuest: false
                            });
                            if (!currentAsGuest) {
                                this.inputRef.current?.focus();
                            }
                        }}
                    >
                        User id
                    </button>
                    <input
                        type="password"
                        size="32"
                        id="arxifter-popup-input-user"
                        ref={this.inputRef}
                        autofocus={this.state.asGuest ? 'false' : 'true'}
                        disabled={this.state.asGuest ? true : false}
                        value={this.state.userId}
                        onChange={(e) => {
                            this.setState({
                                userId: e.target.value
                            })
                        }}
                    />
                    <div></div>
                    <input
                        type="checkbox"
                        id="arxifter-popup-checkbox-remember"
                        disabled={this.state.asGuest ? true : false}
                        checked={this.state.toRemember}
                        onChange={(e) => {
                            this.setState({
                                toRemember: e.target.checked
                            })
                        }}
                    />
                    <label
                        htmlFor="arxifter-popup-checkbox-remember"
                        className={
                            this.state.asGuest
                            ?
                            (
                                "arxifter-popup-form-label-inner "
                                + "arxifter-popup-form-label-disabled"
                            )
                            :
                            "arxifter-popup-form-label-inner"
                        }
                        >
                        remember id
                    </label>
                    {this.withGuest &&
                    <>
                        <div id="arxifter-popup-separator"><hr /></div>
                        <button
                            id="arxifter-popup-form-guest"
                            title={
                                this.state.asGuest
                                ?
                                "Agree to the evaluation-only use."
                                :
                                "Click to switch to the guest-user mode."
                            }
                            className={
                                this.state.asGuest
                                ?
                                (
                                    "arxifter-popup-form-label "
                                    + "arxifter-popup-form-label-this"
                                )
                                :
                                (
                                    "arxifter-popup-form-label "
                                    + "arxifter-popup-form-label-that"
                                )
                            }
                            onClick={(e) => {
                                const currentAsGuest = this.state.asGuest;
                                this.setState({
                                    asGuest: true
                                })
                                if (currentAsGuest) {
                                    this.agreeRef.current?.focus();
                                }
                            }}
                        >
                            Guest
                        </button>
                        <input
                            type="checkbox"
                            id="arxifter-popup-checkbox-guest-agrees"
                            ref={this.agreeRef}
                            autofocus={this.state.asGuest ? 'true' : 'false'}
                            disabled={this.state.asGuest ? false : true}
                            onChange={(e) => {
                                this.setState({
                                    hasAgreed: e.target.checked
                                });
                                this.setupGuestSession(e.target.checked);
                            }}
                        />
                        <label
                            htmlFor="arxifter-popup-checkbox-guest-agrees"
                            className={
                                this.state.asGuest
                                ?
                                "arxifter-popup-form-label-inner"
                                :
                                (
                                    "arxifter-popup-form-label-inner "
                                    + "arxifter-popup-form-label-disabled"
                                )
                            }
                        >
                            I agree to evaluation use.
                        </label>
                        <div id="arxifter-popup-empty-filler">
                            <input
                                type="checkbox"
                                id="arxifter-popup-checkbox-is-laborer"
                                disabled={this.state.asGuest ? false : true}
                                onChange={(e) => {
                                    this.setState({
                                        isLaborer: e.target.checked
                                    });
                                }}
                            />
                        </div>
                        <div
                            id="arxifter-popup-session-notice"
                            className={
                                this.state.asGuest
                                ?
                                "arxifter-popup-form-label-inner"
                                :
                                (
                                    "arxifter-popup-form-label-inner "
                                    + "arxifter-popup-form-label-disabled"
                                )
                            }
                        >
                        {(this.state.sessionState == this.sessionStates.NO)
                            && "session is not set"
                        }
                        {(this.state.sessionState == this.sessionStates.OK)
                            && "session is set up"
                        }
                        {(this.state.sessionState == this.sessionStates.KO)
                            && "session set up failed"
                        }
                        </div>
                    </>
                    }
                </div>
                <div id="arxifter-popup-bottom">
                    <button
                        id="arxifter-popup-close"
                        onClick={(e) => {
                            this.closePopup();
                        }}
                    >
                        Close
                    </button>
                </div>
            </div>
        );
    }
}

export { ArxifterPopup as default };
