#!/usr/bin/env python3

""" scheduling restaurant staff
"""


from flask import Flask


def create_app():
    """create the flask app"""
    app = Flask(__name__)

    # Mark: Root

    @app.route("/")
    def home():
        """default location for the server, home"""
        return "<html><body>Welcome</body></html>", 200

    # Mark: errors

    @app.errorhandler(404)
    def page_not_found(error):
        """Returns error page 404"""
        print(error)
        return "<html><body>404 not found</body></html>", 404

    return app
