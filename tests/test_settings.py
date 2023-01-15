#!/usr/bin/env python3


import types
import tempfile
import os

import financial_game.settings


def test_basics():
    with tempfile.TemporaryDirectory() as workspace:
        old_platform = financial_game.settings.PLATFORM
        test_platform = "test"
        financial_game.settings.PLATFORM = "test"
        financial_game.settings.DEFAULT_SETTINGS[test_platform] = os.path.join(workspace, "test.yaml")
        args = financial_game.settings.load(types.SimpleNamespace(
            port=80,
            database="objects/testing_more.sqlite3",
            secret='secret',
            debug=True,
            settings=financial_game.settings.default_path(),
            reset="reset_file.yaml"
        ))
        assert not os.path.isfile(financial_game.settings.default_path())
        assert args.port == 80, args.port
        assert args.database == "objects/testing_more.sqlite3", args.database
        assert args.secret == "secret", args.secret
        assert args.debug, args.debug
        assert args.reset == "reset_file.yaml", args.reset
        financial_game.settings.PLATFORM = old_platform


def test_no_secrets():
    with tempfile.TemporaryDirectory() as workspace:
        old_platform = financial_game.settings.PLATFORM
        test_platform = "test"
        financial_game.settings.PLATFORM = "test"
        financial_game.settings.DEFAULT_SETTINGS[test_platform] = os.path.join(workspace, "test.yaml")
        args = financial_game.settings.load(types.SimpleNamespace(
            port=80,
            database="objects/testing_more.sqlite3",
            secret=None,
            debug=True,
            settings=financial_game.settings.default_path(),
            reset="reset_file.yaml"
        ))
        assert os.path.isfile(financial_game.settings.default_path())
        assert args.port == 80, args.port
        assert args.database == "objects/testing_more.sqlite3", args.database
        assert args.secret is None, args.secret
        assert args.debug, args.debug
        assert args.reset == "reset_file.yaml", args.reset
        financial_game.settings.PLATFORM = old_platform


def test_override():
    with tempfile.TemporaryDirectory() as workspace:
        old_platform = financial_game.settings.PLATFORM
        test_platform = "test"
        financial_game.settings.PLATFORM = "test"
        financial_game.settings.DEFAULT_SETTINGS[test_platform] = os.path.join(workspace, "test.yaml")
        args = financial_game.settings.load(types.SimpleNamespace(
            port=80,
            database="objects/testing_more.sqlite3",
            secret=None,
            debug=False,
            settings=None,
            reset="reset_file.yaml"
        ))
        assert args.secret is None, args.secret
        assert os.path.isfile(financial_game.settings.default_path())
        assert not args.debug, args.debug
        args = financial_game.settings.load(types.SimpleNamespace(
            port=800,
            database="objects/testing_some_more.sqlite3",
            secret=None,
            debug=True,
            settings=None,
            reset="reset_file_release.yaml"
        ))
        assert args.port == 800, args.port
        assert args.database == "objects/testing_some_more.sqlite3", args.database
        assert args.secret is None, args.secret
        assert args.debug, args.debug
        assert args.reset == "reset_file_release.yaml", args.reset
        financial_game.settings.PLATFORM = old_platform


if __name__ == "__main__":
    test_basics()
    test_no_secrets()
    test_override()
