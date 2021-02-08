import React from 'react';
import PropTypes from 'prop-types';


/* eslint "jsx-a11y/href-no-hash": 0 */
// Reworking the data triggers to use buttons doesn't seem worth it to avoid an eslint warning.
export default class Footer extends React.Component {
    render() {
        const session = this.context.session;
        const disabled = !session;
        let userActionRender;

        if (!(session && session['auth.userid'])) {
            userActionRender = <a href="#" data-trigger="login" disabled={disabled}>User sign-in</a>;
        } else {
            userActionRender = <a href="#" data-trigger="logout">User sign out</a>;
        }
        return (
            <footer id="page-footer">
                <div className="page-footer">
                    <div className="container">
                        <div className="row">
                            <div className="col-sm-6 col-sm-push-6">
                                <ul className="footer-links">
                                    <li><a href="mailto:t2dream-l@mailman.ucsd.edu">Contact</a></li>
                                    <li><a href="https://ucsd.edu/about/terms-of-use.html">Terms of Use</a></li>
                                    <li id="user-actions-footer">{userActionRender}</li>
                                </ul>
                                <p className="copy-notice">&copy;{new Date().getFullYear()} Regents of the University of California.</p>
                            </div>

                            <div className="col-sm-6 col-sm-pull-6">
                                <ul className="footer-logos">
                                    <li><a href="/"><img src="/static/img/logo_final.png" alt="Diabetes Epigenome Atlas" id="t2dream-logo" height="55px" width="130px" /></a></li>
                                    <li><a href="http://www.ucsd.edu"><img src="/static/img/UCSanDiegoLogo-BlueGold.png" alt="UC San Diego" id="ucsd-logo" width="130px" height="40px" /></a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </footer>
        );
    }
}

Footer.contextTypes = {
    session: PropTypes.object,
};

Footer.propTypes = {
    version: PropTypes.string, // App version number
};

Footer.defaultProps = {
    version: '',
};
