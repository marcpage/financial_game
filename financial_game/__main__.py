#!/usr/bin/env python3

"""
    Main entrypoint to the game
"""


import argparse
import os
import sys

import financial_game.webserver


DEFAULT_DATABASE = "objects/test.sqlite3"
DEFAULT_WEB_PORT = 8000


def parse_command_line():
    """Parses command line options"""
    parser = argparse.ArgumentParser(description="A web-based real-life financial game")
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        default=DEFAULT_WEB_PORT,
        help="The port the web server listens on",
    )
    parser.add_argument(
        "-d",
        "--db",
        dest="database",
        type=str,
        default=DEFAULT_DATABASE,
        help="SqlAlchemy URL for the database or path to Sqlite3 database",
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
    args = parser.parse_args()

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
    app = financial_game.webserver.create_app(database)
    app.run(host="0.0.0.0", debug=args.debug, port=args.port)


if __name__ == "__main__":
    main()
