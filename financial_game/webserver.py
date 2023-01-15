#!/usr/bin/env python3

""" Root webserver
"""


import flask

import financial_game.template
import financial_game.model
import financial_game.sessionkey


# TODO: Get session key secret from settings file  # pylint: disable=fixme
SECRET = "secret"


def create_app(database):
    """create the flask app"""
    app = flask.Flask(__name__)

    # Mark: Root

    @app.route("/")
    def home(message=None):
        """default location for the server, home"""

        if financial_game.sessionkey.COOKIE in flask.request.cookies:
            user_id, password_hash = financial_game.sessionkey.parse(
                flask.request.cookies[financial_game.sessionkey.COOKIE],
                flask.request.headers,
                SECRET,
            )
            user = database.get_user(user_id)

            if user is not None and user.password_hash != password_hash:
                user = None

        else:
            user = None

        if user is None:
            contents = financial_game.template.render(
                "templates/home.html.mako", message=message
            )

        else:
            contents = f"<html><body>Welcome {user.name}</body></html>"

        return contents, 200

    @app.route("/login_failed")
    def invalid_login():
        return home(message="Invalid Login")

    # Mark: API

    @app.route("/login", methods=["POST"])
    def login():
        user = database.find_user(flask.request.form["email"])

        if user and user.password_matches(flask.request.form["password"]):
            response = flask.make_response(flask.redirect(flask.url_for("home")))
            session_key = financial_game.sessionkey.create(
                user, flask.request.headers, SECRET
            )
            response.set_cookie(financial_game.sessionkey.COOKIE, session_key)

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
