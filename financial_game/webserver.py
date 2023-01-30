#!/usr/bin/env python3

""" Root webserver
"""


import flask

import financial_game.template
import financial_game.model
import financial_game.sessionkey


COOKIE = "user-id"  # name of the cookie that contains the session key


def get_user(request, args):
    """Determines the user (or None) that is requesting the page"""
    if COOKIE in request.cookies:
        user_id, password_hash = financial_game.sessionkey.parse(
            request.cookies[COOKIE],
            request.headers,
            args.secret,
        )
        user = financial_game.model.User.fetch(user_id)

        if user is not None and user.password_hash == password_hash:
            return user

    return None


def create_app(args):
    """create the flask app"""
    app = flask.Flask(__name__)

    # Mark: Root

    @app.route("/")
    def home(message=None):
        """default location for the server, home"""
        user = get_user(flask.request, args)

        if user is None:
            contents = financial_game.template.render(
                "templates/home.html.mako", message=message, user=None
            )

        else:
            contents = (
                "<html><body>"
                + f"Welcome {user.name}"
                + "<p><a href='/logout'>Logout</a></p></body></html>"
            )

        return contents, 200

    @app.route("/login_failed")
    def invalid_login():
        return home(message="Invalid Login")

    # Mark: API

    @app.route("/logout")
    def logout():
        response = flask.make_response(flask.redirect(flask.url_for("home")))
        response.set_cookie(COOKIE, "", expires=0)
        return response

    @app.route("/login", methods=["POST"])
    def login():
        user = financial_game.model.User.lookup(flask.request.form["email"])

        if user and user.password_matches(flask.request.form["password"]):
            response = flask.make_response(flask.redirect(flask.url_for("home")))
            session_key = financial_game.sessionkey.create(
                user, flask.request.headers, args.secret
            )
            response.set_cookie(COOKIE, session_key)

        else:
            response = flask.make_response(
                flask.redirect(flask.url_for("invalid_login"))
            )

        return response

    # Mark: errors

    @app.errorhandler(404)
    def page_not_found(error=None):
        """Returns error page 404"""
        return f"<html><body>404 not found<p>{error}</p></body></html>", 404

    return app
