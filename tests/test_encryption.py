#!/usr/bin/env python3


import time
import hashlib
import types

import financial_game.encryption


def test_basic():
    test_cases = [(f"{i}"*i).encode('utf-8') for i in range(0, 256)]
    test_keys = [f"{i}"*i for i in range(0, 256)]

    for test_key in test_keys:
        for test_case in test_cases:
            encrypted = financial_game.encryption.encrypt(test_key, test_case)
            decrypted = financial_game.encryption.decrypt(test_key, encrypted)
            assert test_case == decrypted, f"key = '{test_key}' value = '{test_case}'"


if __name__ == "__main__":
    test_basic()
