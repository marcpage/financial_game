#!/usr/bin/env python3


import tempfile
import time
import types
import hashlib

import financial_game.webserver
import financial_game.model
import financial_game.sessionkey


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
        app = financial_game.webserver.create_app(ARGS)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200, response.status_code
        assert b'the real-life financial game' in response.data.lower(), response.data


if __name__ == "__main__":
    test_root()
    test_login_fail()
    test_login_success()
    test_bad_session_password()
    test_404()
    test_logout()
