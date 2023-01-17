#!/usr/bin/env python3

""" Handles settings file
"""


import os
import platform

import yaml


DEFAULT_DATABASE = "objects/test.sqlite3"
DEFAULT_WEB_PORT = 8000
DEFAULT_SMTP_PORT = 857
DEFAULT_SMTP_SERVER = "smtp.gmail.com"

# TODO: Get the correct path on each platform (dict)  # pylint: disable=fixme
PLATFORM = platform.system()
DEFAULT_SETTINGS = {
    "Darwin": os.path.join(
        os.environ.get("HOME", ""), "Library", "Preferences", "financial_game.yaml"
    ),
    "Linux": os.path.join(os.environ.get("HOME", ""), ".financial_game.yaml"),
    "Windows": os.path.join(os.environ.get("LOCALAPPDATA", ""), "financial_game.yaml"),
}


def default_path():
    """Get the default path for the settings file"""
    return DEFAULT_SETTINGS[PLATFORM]


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
    args.smtp_port = (
        settings.get("smtp-port", DEFAULT_SMTP_PORT)
        if args.smtp_port is None
        else args.smtp_port
    )
    args.smtp_server = (
        settings.get("smtp-server", DEFAULT_SMTP_SERVER)
        if args.smtp_server is None
        else args.smtp_server
    )
    args.smtp_tls = (
        settings.get("smtp-tls", args.smtp_tls) if not args.smtp_tls else args.smtp_tls
    )
    args.smtp_user = (
        settings.get("smtp-user", args.smtp_user)
        if not args.smtp_user
        else args.smtp_user
    )
    args.smtp_password = (
        settings.get("smtp-password", args.smtp_password)
        if not args.smtp_password
        else args.smtp_password
    )
    args.email_from = (
        settings.get("email-from", args.email_from)
        if not args.email_from
        else args.email_from
    )

    if args.secret is None and not os.path.isfile(args.settings):
        write(
            args.settings,
            {
                "port": args.port,
                "database": args.database,
                "secret": args.secret,
                "debug": args.debug,
                "reset": args.reset,
                "smtp-port": args.smtp_port,
                "smtp-server": args.smtp_server,
                "smtp-tls": args.smtp_tls,
                "smtp-user": args.smtp_user,
                "smtp-password": args.smtp_password,
                "email-from": args.email_from,
            },
        )

    return args


def write(path, settings):
    """Creates the file and writes the settings"""
    os.makedirs(os.path.split(path)[0], exist_ok=True)

    with open(path, "w", encoding="utf-8") as settings_file:
        yaml.dump(settings, settings_file)
