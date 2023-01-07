#!/usr/bin/env python3

"""
    Main entrypoint to the game
"""

import financial_game.webserver


def main():
    """main entrypoint"""
    app = financial_game.webserver.create_app()
    app.run(host="0.0.0.0", debug=True, port=8000)


if __name__ == "__main__":
    main()
