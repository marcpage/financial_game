#!/usr/bin/env python3

""" Handle encrypting data
"""


import hashlib

from Crypto.Cipher import AES
from Crypto import Random


def encrypt(key_data: str, data: bytes):
    """Encrypt data from the key_data"""
    key = hashlib.sha256(key_data.encode("utf-8")).digest()
    initialization_vector = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, initialization_vector)
    padded = pad(data, AES.block_size)
    encrypted = cipher.encrypt(padded)
    return initialization_vector + encrypted


def decrypt(key_data: str, encrypted: bytes):
    """Decrypt data using the key_data"""
    block_size = AES.block_size
    initialization_vector = encrypted[:block_size]
    key = hashlib.sha256(key_data.encode("utf-8")).digest()
    cipher = AES.new(key, AES.MODE_CBC, initialization_vector)
    encrypted_data = encrypted[block_size:]
    decrypted = cipher.decrypt(encrypted_data)
    unpadded = strip_padding(decrypted)
    return unpadded


def pad(data: bytes, pad_to: int) -> bytes:
    """padd data to multiple of pad_to bytes"""
    padding_needed = pad_to - len(data) % pad_to
    padded = data + bytes((padding_needed,)) * padding_needed
    return padded


def strip_padding(data: bytes) -> bytes:
    """remove padding added by pad()"""
    return data[: -data[-1]]
