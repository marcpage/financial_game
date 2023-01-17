#!/usr/bin/env python3


import argparse

import financial_game.email
import financial_game.settings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A web-based real-life financial game")
    parser.add_argument("--unused1", dest="port")
    parser.add_argument("--unused2", dest="database")
    parser.add_argument("--unused3", dest="debug")
    parser.add_argument("--unused4", dest="reset")
    parser.add_argument(
        "--settings",
        dest="settings",
        type=str,
        help="Path to the settings file to use "
        + f"({financial_game.settings.default_path()})",
    )
    parser.add_argument(
        "-p",
        "--port",
        dest="smtp_port",
        type=int,
        help=f"The smtp port (587)",
    )
    parser.add_argument(
        "-s",
        "--server",
        dest="smtp_server",
        type=str,
        help="SMTP server (smtp.gmail.com)",
    )
    parser.add_argument(
        "--user",
        dest="smtp_user",
        type=str,
        help="SMTP log in username",
    )
    parser.add_argument(
        "--password",
        dest="smtp_password",
        type=str,
        help="SMTP log in password",
    )
    parser.add_argument(
        "--secret",
        dest="secret",
        type=str,
        help="The secret phrase used to encrypt password",
    )
    parser.add_argument(
        "--tls",
        dest="smtp_tls",
        action="store_true",
        help="Should we use TLS",
    )
    parser.add_argument(
        "--from",
        dest="email_from",
        type=str,
        help="The sender of the email",
    )
    parser.add_argument(
        "--to",
        dest="to",
        type=str,
        required=True,
        help="The recipient of the email",
    )
    parser.add_argument(
        "--subject",
        dest="subject",
        type=str,
        required=True,
        help="The subject of the email",
    )
    parser.add_argument(
        "--text",
        dest="text",
        type=str,
        help="The path to the text file that contains the text body of the email",
    )
    parser.add_argument(
        "--html",
        dest="html",
        type=str,
        help="The path to the text file that contains the html body of the email",
    )
    parser.add_argument(
        "--attach",
        dest="attachments",
        type=str,
        action="append",
        help="The path of files to attach to the email",
    )
    parser.add_argument(
        "--inline",
        dest="inlined",
        type=str,
        action="append",
        help="Images inlined in the html, of the form <image_id>:<image_path>",
    )
    parser.add_argument(
        "--encoding",
        dest="encoding",
        type=str,
        default="utf-8",
        help="The encoding to use for subject, text body, and html body",
    )
    # TODO: Add support for printing encrypted password   # pylint: disable=fixme
    args = financial_game.settings.load(parser.parse_args())
    assert args.text is not None or args.html is not None
    assert args.email_from is not None

    if args.html:
       with open(args.html, 'r') as html_file:
        args.html = html_file.read()

    if args.text:
       with open(args.text, 'r') as text_file:
        args.text = text_file.read()

    if args.attachments:
        args.attachments = {f:{} for f in args.attachments}
    else:
        args.attachments = None

    if args.inlined:
        args.inlined = dict(p.split(':') for p in args.inlined)

    financial_game.email.send(args, args.to, args.subject, args.html, args.text, args.attachments, args.inlined, args.encoding)
