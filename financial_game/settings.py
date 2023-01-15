#!/usr/bin/env python3

""" Handles settings file
"""


import os

import yaml


DEFAULT_DATABASE = "objects/test.sqlite3"
DEFAULT_WEB_PORT = 8000

# TODO: Get the correct path on each platform (dict)  # pylint: disable=fixme
DEFAULT_SETTINGS = os.path.join(
    os.environ["HOME"], "Library", "Preferences", "financial_game.yaml"
)


def default_path():
    """Get the default path for the settings file"""
    return DEFAULT_SETTINGS


def load(args):
    """Fill in unset args with either default or values from settings file"""
    if args.settings is None:
        args.settings = default_path()

    try:
        with open(args.settings, "r", encoding="utf-8") as settings_file:
            settings = yaml.safe_load(settings_file.read())

    except FileNotFoundError:
        settings = {}

    args.port = (
        settings.get("port", DEFAULT_WEB_PORT) if args.port is None else args.port
    )
    args.database = (
        settings.get("database", DEFAULT_DATABASE)
        if args.database is None
        else args.database
    )
    args.secret = (
        settings.get("secret", args.secret) if args.secret is None else args.secret
    )
    args.debug = settings.get("debug", args.debug) if not args.debug else args.debug
    args.reset = settings.get("reset", args.reset) if args.reset is None else args.reset

    if args.secret is None and not os.path.isfile(args.settings):
        write(
            args.settings,
            {
                "port": args.port,
                "database": args.database,
                "secret": args.secret,
                "debug": args.debug,
                "reset": args.reset,
            },
        )

    return args


def write(path, settings):
    """Creates the file and writes the settings"""
    os.makedirs(os.path.split(path)[0], exist_ok=True)

    with open(path, "w", encoding="utf-8") as settings_file:
        yaml.dump(settings, settings_file)
