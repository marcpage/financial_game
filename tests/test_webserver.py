#!/usr/bin/env python3

import financial_game.webserver


def test_root():
    app = financial_game.webserver.create_app()
    app.config.update({"TESTING": True})
    client = app.test_client()
    response = client.get("/")
    assert b'welcome' in response.data.lower(), response.data


def no_test_404():
    app = financial_game.webserver.create_app()
    app.config.update({"TESTING": True})
    client = app.test_client()
    response = client.get("/not_found")
    assert b'not found' in response.data.lower(), response.data

