#!/usr/bin/env python3

""" scheduling restaurant staff
"""


import flask

import financial_game.template
import financial_game.model


def create_app(database):
    """create the flask app"""
    app = flask.Flask(__name__)

    # Mark: Root

    @app.route("/")
    def home(message=None):
        """default location for the server, home"""

        if "user-id" not in flask.request.cookies:
            contents = financial_game.template.render(
                "templates/home.html.mako", message=message
            )

        else:
            contents = f"<html><body>Welcome {flask.request.cookies.get('user-id')}</body></html>"

        return contents, 200

    @app.route("/login_failed")
    def invalid_login():
        return home(message="Invalid Login")

    # Mark: API

    @app.route("/login", methods=["POST"])
    def login():
        user = database.find_user(flask.request.form["email"])
        print(f"user = {user}")

        if user and user.password_matches(flask.request.form["password"]):
            response = flask.make_response(flask.redirect(flask.url_for("home")))
            response.set_cookie("user-id", f"{user.id}")

        else:
            response = flask.make_response(
                flask.redirect(flask.url_for("invalid_login"))
            )

        return response

    # Mark: errors

    @app.errorhandler(404)
    def page_not_found(error=None):
        """Returns error page 404"""
        print(f"error = '{error}'")
        return f"<html><body>404 not found<p>{error}</p></body></html>", 404

    return app
