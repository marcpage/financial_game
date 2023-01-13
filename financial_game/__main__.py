#!/usr/bin/env python3

"""
    Main entrypoint to the game
"""

import financial_game.webserver


def main():
    """main entrypoint"""
    database = financial_game.model.Database("sqlite:///objects/test.sqlite3")
    app = financial_game.webserver.create_app(database)
    app.run(host="0.0.0.0", debug=True, port=8000)


if __name__ == "__main__":
    main()
