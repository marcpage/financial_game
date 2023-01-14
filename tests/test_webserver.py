#!/usr/bin/env python3

import financial_game.webserver
import financial_game.model

import tempfile


def test_root():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        app = financial_game.webserver.create_app(db)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.get("/")
        assert response.status_code == 200, response.status_code
        assert b'the real-life financial game' in response.data.lower(), response.data


def test_login_fail():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        app = financial_game.webserver.create_app(db)
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
        db.create_user("john.appleseed@apple.com", "Setec astronomy", "John", sponsor_id=None)
        app = financial_game.webserver.create_app(db)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.post("/login", data={
            'email': 'john.appleseed@apple.com',
            'password': 'Setec astronomy'
        }, follow_redirects=True)
        assert response.status_code == 200, response.status_code
        assert b'invalid login' not in response.data.lower(), response.data


def test_404():
    with tempfile.TemporaryDirectory() as workspace:
        db = financial_game.model.Database("sqlite:///" + workspace + "test.sqlite3")
        app = financial_game.webserver.create_app(db)
        app.config.update({"TESTING": True})
        client = app.test_client()
        response = client.get("/not_found")
        assert response.status_code == 404, response.status_code
        assert b'not found' in response.data.lower(), response.data

