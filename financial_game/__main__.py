#!/usr/bin/env python3

"""
    Main entrypoint to the game
"""

##############################################################
#                                                              #
#  This file is not tested. Code should be minimal and simple  #
#                                                              #
##############################################################

import argparse
import os
import sys

import financial_game.webserver
import financial_game.settings


def parse_command_line():
    """Parses command line options"""
    parser = argparse.ArgumentParser(description="A web-based real-life financial game")
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        help=f"The port the web server listens on ({financial_game.settings.DEFAULT_WEB_PORT})",
    )
    parser.add_argument(
        "-d",
        "--db",
        dest="database",
        type=str,
        help="SqlAlchemy URL for the database or path to Sqlite3 database "
        + f"({financial_game.settings.DEFAULT_DATABASE})",
    )
    parser.add_argument(
        "--settings",
        dest="settings",
        type=str,
        help="Path to the settings file to use "
        + f"({financial_game.settings.default_path()})",
    )
    parser.add_argument(
        "--secret",
        dest="secret",
        type=str,
        help="The secret phrase used to encrypt session tokens",
    )
    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Should we be debugging"
    )
    parser.add_argument(
        "--reset",
        dest="reset",
        type=str,
        help="Path to a yaml script to (re)initialize the database "
        + "(only valid if db is a file path or db is empty)",
    )
    parser.add_argument(
        "--smtp-port",
        dest="smtp_port",
        default=587,
        type=int,
        help=f"The smtp port ({financial_game.settings.DEFAULT_SMTP_PORT})",
    )
    parser.add_argument(
        "--smtp-server",
        dest="smtp_server",
        type=str,
        default="smtp.gmail.com",
        help=f"SMTP server ({financial_game.settings.DEFAULT_SMTP_SERVER})",
    )
    parser.add_argument(
        "--smtp-user",
        dest="smtp_user",
        type=str,
        help="SMTP log in username",
    )
    parser.add_argument(
        "--smtp-password",
        dest="smtp_password",
        type=str,
        help="SMTP log in password",
    )
    parser.add_argument(
        "--email-from",
        dest="email_from",
        type=str,
        help="The sender for any emails sent",
    )
    parser.add_argument(
        "--tls",
        dest="smtp_tls",
        action="store_true",
        help="Should we use TLS",
    )
    args = financial_game.settings.load(parser.parse_args())

    if args.secret is None:
        parser.print_help()
        print(f"You must either specify --secret or set secret in {args.settings}")
        sys.exit(1)

    if "://" not in args.database:

        if args.reset:
            if not os.path.isfile(args.reset):
                parser.print_help()
                print(f"Reset file not found: {args.reset}")
                sys.exit(1)

            if os.path.isfile(args.database):
                os.unlink(args.database)

        args.database = f"sqlite:///{args.database}"

    return args


def main():
    """main entrypoint"""
    args = parse_command_line()
    database = financial_game.model.Database(args.database, serialized=args.reset)
    app = financial_game.webserver.create_app(database, args)
    app.run(host="0.0.0.0", debug=args.debug, port=args.port)


if __name__ == "__main__":
    main()
