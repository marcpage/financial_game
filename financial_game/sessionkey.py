#!/usr/bin/env python3

""" Handles creating and parsing session keys
"""


import base64
import hashlib
import datetime

from Crypto.Cipher import AES
from Crypto import Random


COOKIE = "user-id"  # name of the cookie that contains the session key


def create(user, headers, secret, hour_delta=0):
    """Creates a session key given the headers and a secret"""
    now = datetime.datetime.now()
    now += datetime.timedelta(hours=hour_delta)
    hour_string = now.strftime("%Y/%m/%d@%H")
    data = f"{user.id}:{user.password_hash}"
    data += " " * (AES.block_size - len(data) % AES.block_size)
    key_data = f"{secret}:{hour_string}:{headers['User-Agent']}"
    key = hashlib.sha256(key_data.encode()).digest()
    initialization_vector = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, initialization_vector)
    return base64.b64encode(
        initialization_vector + cipher.encrypt(data.encode())
    ).decode("utf-8")


# TODO: Return a refreshed session key if its old  # pylint: disable=fixme
def parse(session_key, headers, secret, hour_delta=0):
    """Parses a session key given the headers and a secret"""
    block_size = AES.block_size
    now = datetime.datetime.now()
    now += datetime.timedelta(hours=hour_delta)
    hour_string = now.strftime("%Y/%m/%d@%H")
    encrypted = base64.b64decode(session_key)
    initialization_vector = encrypted[:block_size]
    key_data = f"{secret}:{hour_string}:{headers['User-Agent']}"
    key = hashlib.sha256(key_data.encode()).digest()
    cipher = AES.new(key, AES.MODE_CBC, initialization_vector)
    encrypted_data = encrypted[block_size:]

    try:
        data = cipher.decrypt(encrypted_data).decode("utf-8").strip().split(":")

    except UnicodeDecodeError:

        if hour_delta < 0:
            return (None, None)

        return parse(session_key, headers, secret, hour_delta=-1)

    return (int(data[0]), data[1])
