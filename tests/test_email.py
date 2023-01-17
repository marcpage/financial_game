#!/usr/bin/env python3

import asyncio
import types
import queue
import threading
import ssl

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult

import financial_game.email


class EchoHandler:
    def __init__(self, out_queue):
        self.__queue= out_queue

    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        self.__queue.put((envelope.mail_from, envelope.rcpt_tos, envelope.content.decode('utf8', errors='replace')))
        return '250 Message accepted for delivery'


def authenticator(server, session, envelope, mechanism, auth_data):
    return AuthResult(success=True)


def start_server(email_queue, context, port=8025, address="localhost"):
    controller = Controller(EchoHandler(email_queue), address, port, auth_require_tls=False, authenticator=authenticator, tls_context=context)
    controller.start()
    return controller


def test_form_email_text_simple():
    args = types.SimpleNamespace(email_from="Marc Page <Marc@ResolveToExcel.com>")
    recipient = "Marc Page <MarcAllenPage@gmail.com>"
    message = financial_game.email.form(args, recipient, "Testing Text", text_body="Here it is\ntext body", encoding="us-ascii")
    assert "Subject: Testing Text" in message, message
    assert "text body"  in message, message


def test_form_email_html_simple():
    args = types.SimpleNamespace(email_from="Marc Page <Marc@ResolveToExcel.com>")
    recipient = "Marc Page <MarcAllenPage@gmail.com>"
    message = financial_game.email.form(args, recipient, "Testing HTML", html_body="Here it is\n<b>html</b> body", encoding="us-ascii")
    assert "Subject: Testing HTML" in message, message
    assert "<b>html</b>"  in message, message


def test_send_email():
    email_queue = queue.Queue()
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('tests/localhost_cert.pem', 'tests/localhost_key.pem')
    smtp_server = start_server(email_queue, context)
    args = types.SimpleNamespace(
        email_from="Marc Page <Marc@ResolveToExcel.com>",
        smtp_server="localhost",
        smtp_port=smtp_server.port,
        smtp_user="user",
        smtp_password="password",
        smtp_tls=True,
    )
    recipient = "Marc Page <MarcAllenPage@gmail.com>"
    financial_game.email.send(
            args,
            recipient,
            "Testing sending emails",
            html_body="Here it is\n<b>html</b> body",
            text_body="Here it is\ntext body",
            attachments={'requirements.txt':{'mime': 'text/plain'}},
            inlined={'image1': 'tests/sign-check-icon.png'},
            encoding="us-ascii")

    try:
        message = email_queue.get(timeout=0.100)

    except queue.Empty:
        message = None

    finally:
        smtp_server.stop()

    assert message is not None


if __name__ == "__main__":
    test_form_email_text_simple()
    test_form_email_html_simple()
    test_send_email()
