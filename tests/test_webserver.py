#!/usr/bin/env python3


import tempfile
import time
import types
import hashlib

import financial_game.webserver
import financial_game.model
import financial_game.sessionkey
from financial_game.model_bank import TypeOfAccount
from financial_game.model_user import AccountPurpose


ARGS = types.SimpleNamespace(secret='gobble de gook')


def test_root():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        app = financial_game.webserver.create_app(ARGS)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.get("/")
        assert response.status_code == 200, response.status_code
        assert b'the real-life financial game' in response.data.lower(), response.data


def test_login_fail():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        app = financial_game.webserver.create_app(ARGS)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.post("/login", data={
            'email': 'john.appleseed@apple.com',
            'password': 'Setec astronomy'
        }, follow_redirects=True)
        assert response.status_code == 200, response.status_code
        assert b'invalid login' in response.data.lower(), response.data


def test_login_success():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        financial_game.model.User.create("john.appleseed@apple.com", "Setec astronomy", "John")
        app = financial_game.webserver.create_app(ARGS)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.post("/login", data={
            'email': 'john.appleseed@apple.com',
            'password': 'Setec astronomy'
        }, follow_redirects=True)
        assert response.status_code == 200, response.status_code
        assert b'invalid login' not in response.data.lower(), response.data


def test_bad_session_password():
    while time.localtime().tm_min == 59:
        time.sleep(0.100)  # To prevent test flakiness around hour changes

    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        financial_game.model.User.create("john.appleseed@apple.com", "Setec astronomy", "John")
        app = financial_game.webserver.create_app(ARGS)
        app.config.update({"TESTING": True})
        client = app.test_client()
        user = types.SimpleNamespace(id=1, password_hash=hashlib.sha256("password".encode()).hexdigest())
        headers = {'User-Agent': 'Chrome'}
        bad_session = financial_game.sessionkey.create(user, headers, ARGS.secret)
        client.set_cookie('localhost', financial_game.webserver.COOKIE, bad_session)
        response = client.get("/", headers=headers)
        assert response.status_code == 200, response.status_code
        assert b'email' in response.data.lower(), response.data
        assert b'password' in response.data.lower(), response.data


def test_404():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        app = financial_game.webserver.create_app(ARGS)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.get("/not_found")
        assert response.status_code == 404, response.status_code
        assert b'not found' in response.data.lower(), response.data


def test_logout():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        financial_game.model.User.create("john.appleseed@apple.com", "Setec astronomy", "John")
        app = financial_game.webserver.create_app(ARGS)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.post("/login", data={
            'email': 'john.appleseed@apple.com',
            'password': 'Setec astronomy'
        }, follow_redirects=True)
        assert response.status_code == 200, response.status_code
        assert b'invalid login' not in response.data.lower(), response.data
        assert len(client.cookie_jar) == 1
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200, response.status_code
        assert b'the real-life financial game' in response.data.lower(), response.data
        assert len(client.cookie_jar) == 0


def test_add_account_no_login():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        financial_game.model.User.create("john.appleseed@apple.com", "Setec astronomy", "John")
        app = financial_game.webserver.create_app(ARGS)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.post("/add_account", data={
            'bank': -1,
            'account_label': 'budget',
            'bank_name': 'Bank of America',
            'bank_url': 'https://BankOfAmerica.com/',
            'account_type_name': 'Customized Cash Rewards',
            'acount_type_category': 'CRED',
            'account_type_url': '',
        }, follow_redirects=True)
        assert len(financial_game.model.Bank.every()) == 0
        assert b'the real-life financial game' in response.data.lower(), response.data


def test_add_account():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        user = financial_game.model.User.create("john.appleseed@apple.com", "Setec astronomy", "John")
        app = financial_game.webserver.create_app(ARGS)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.post("/login", data={
            'email': 'john.appleseed@apple.com',
            'password': 'Setec astronomy'
        }, follow_redirects=True)
        assert response.status_code == 200, response.status_code
        assert b'invalid login' not in response.data.lower(), response.data
        assert financial_game.model.Bank.total() == 0

        response = client.post("/add_account", data={
            'bank': -1,
            'account_label': 'online purchases',
            'bank_name': 'Bank of America',
            'bank_url': 'https://BankOfAmerica.com/',
            'account_type_name': 'Customized Cash Rewards',
            'account_hint': 'usual',
            'account_purpose': 'MRGC',
            'acount_type_category': 'CRED',
            'account_type_url': '',
        }, follow_redirects=True)
        banks = financial_game.model.Bank.every()
        assert len(banks) == 1
        assert banks[0].name == 'Bank of America'
        assert banks[0].url == 'https://BankOfAmerica.com/'
        account_types = banks[0].account_types()
        assert len(account_types) == 1
        assert account_types[0].name == 'Customized Cash Rewards'
        assert account_types[0].url is None
        assert account_types[0].type == TypeOfAccount.CRED
        accounts = user.accounts()
        assert len(accounts) == 1
        assert accounts[0].label == 'online purchases'
        assert accounts[0].hint == 'usual'
        assert accounts[0].purpose == AccountPurpose.MRGC

        response = client.post("/add_account", data={
            'bank': banks[0].id,
            f'bank_{banks[0].id}_account_type': account_types[0].id,
            'account_label': 'budget',
        }, follow_redirects=True)
        banks = financial_game.model.Bank.every()
        assert len(banks) == 1
        assert banks[0].name == 'Bank of America'
        assert banks[0].url == 'https://BankOfAmerica.com/'
        account_types = banks[0].account_types()
        assert len(account_types) == 1
        assert account_types[0].name == 'Customized Cash Rewards'
        assert account_types[0].url is None
        assert account_types[0].type == TypeOfAccount.CRED
        accounts = user.accounts()
        assert len(accounts) == 2
        assert None in [a.purpose for a in accounts]
        assert None in [a.hint for a in accounts]

        response = client.post("/add_account", data={
            'bank': banks[0].id,
            f'bank_{banks[0].id}_account_type': -1,
            'account_label': 'budget',
            'account_type_name': 'Advantage Banking',
            'acount_type_category': 'CHCK',
            'account_type_url': '',
        }, follow_redirects=True)
        banks = financial_game.model.Bank.every()
        assert len(banks) == 1
        assert banks[0].name == 'Bank of America'
        assert banks[0].url == 'https://BankOfAmerica.com/'
        account_types = banks[0].account_types()
        assert len(account_types) == 2
        assert 'Customized Cash Rewards' in [t.name for t in account_types]
        accounts = user.accounts()
        assert len(accounts) == 3


if __name__ == "__main__":
    test_add_account_no_login()
    test_add_account()
    test_root()
    test_login_fail()
    test_login_success()
    test_bad_session_password()
    test_404()
    test_logout()
