'use strict';
var React = require('react');
import PropTypes from 'prop-types';
import createReactClass from 'create-react-class';

var Footer = createReactClass({
    contextTypes: {
        session: PropTypes.object
    },

    propTypes: {
        version: PropTypes.string // App version number
    },

    render: function() {
        var session = this.context.session;
        var disabled = !session;
        var userActionRender;

        if (!(session && session['auth.userid'])) {
            userActionRender = <a href="#" data-trigger="login" disabled={disabled}>Submitter sign-in</a>;
        } else {
            userActionRender = <a href="#" data-trigger="logout">Submitter sign out</a>;
        }
        return (
            <footer id="page-footer">
                <div className="container">
                    <div className="row">
                        <div className="app-version">{this.props.version}</div>
                    </div>
                </div>
                <div className="page-footer">
                    <div className="container">
                        <div className="row">
                            <div className="col-sm-6 col-sm-push-6">
                                <ul className="footer-links">
                                    <li><a href="mailto:kgaulton@ucsd.edu">Contact</a></li>
                                    <li><a href="">Terms of Use</a></li>
                                    <li id="user-actions-footer">{userActionRender}</li>
                                </ul>
                                <p className="copy-notice">&copy;{new Date().getFullYear()} Regents of the University of California.</p>
                            </div>

                            <div className="col-sm-6 col-sm-pull-6">
                                <ul className="footer-logos">
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </footer>
        );
    }
});

module.exports = Footer;
