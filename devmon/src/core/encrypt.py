#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-10-14 09:28
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: encrypt.py
# Tools: PyCharm

"""
---Encrypt password to codes---
"""
import base64


class HidePass(object):
    def __init__(self):
        pass

    @staticmethod
    def encrypt(secret: str = None, position: int = 0, password: str = None) -> bytes:
        l_pass = list(password)
        try:
            l_pass.insert(position, secret)
        except IndexError:
            l_pass.insert(0, secret)

        mixed_pass = ''.join(l_pass)
        return base64.b64encode(mixed_pass.encode())

    @staticmethod
    def decrypt(secret: str = None, position: int = 0, codes: bytes = None) -> str:
        mixed_pass = base64.b64decode(codes).decode()
        l_mixed_pass = list(mixed_pass)

        for i in range(0, len(secret)):
            l_mixed_pass.pop(position)
            print(l_mixed_pass)

        return ''.join(l_mixed_pass)


if __name__ == '__main__':
    hp = HidePass()
    print(hp.encrypt('I love China', 5, 'loveShangHai%1998'))
    print(hp.decrypt('I love China', 5, b'bG92ZVhJIGxvdmUgQ2hpbFJTiwNA5'))



