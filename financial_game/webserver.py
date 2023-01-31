#!/usr/bin/env python3

""" Root webserver
"""


import flask

import financial_game.template
import financial_game.model
from financial_game.model_bank import Bank, AccountType, TypeOfAccount
from financial_game.model_user import Account, AccountPurpose
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


def none_if_empty(value: str) -> str:
    """Returns None if value is empty or None, the value otherwise"""
    return value if value else None


def create_app(args):
    """create the flask app"""
    app = flask.Flask(__name__)

    # Mark: Root

    @app.route("/")
    def home(message=None):
        """default location for the server, home"""
        user = get_user(flask.request, args)

        if user is None:
            banks, account_types = [], {}
        else:
            banks, account_types = AccountType.every()

        contents = financial_game.template.render(
            "templates/home.html.mako",
            message=message,
            user=user,
            banks=banks,
            account_types=account_types,
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

    @app.route("/add_account", methods=["POST"])
    def add_account():
        user = get_user(flask.request, args)

        if user is None:
            return flask.make_response(flask.redirect(flask.url_for("home")))

        bank_id = int(flask.request.form["bank"])
        label = flask.request.form["account_label"]
        hint = flask.request.form.get("account_hint", None)
        purpose = flask.request.form.get("account_purpose", None)
        purpose = None if purpose is None else AccountPurpose[purpose]

        if bank_id == -1:
            name = flask.request.form["bank_name"]
            url = none_if_empty(flask.request.form.get("bank_url", None))
            bank = Bank.create(name, url)
            account_type_id = -1
        else:
            bank = Bank.fetch(bank_id)
            account_type_id = int(flask.request.form[f"bank_{bank.id}_account_type"])

        if account_type_id == -1:
            name = flask.request.form["account_type_name"]
            category = flask.request.form["acount_type_category"]
            url = none_if_empty(flask.request.form.get("account_type_url", None))
            account_type = AccountType.create(bank, name, TypeOfAccount[category], url)
        else:
            account_type = AccountType.fetch(account_type_id)

        Account.create(user, account_type, label, hint, purpose)
        return flask.make_response(flask.redirect(flask.url_for("home")))

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
