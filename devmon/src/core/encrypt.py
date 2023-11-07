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
---Encrypt password to codes, for storing password(s) in 'devlist' files---
"""
import base64
import binascii


class HidePass(object):
    def __init__(self, secret: str = None, position: int = 0):
        self.secret = secret if secret else 'I love China & Chinese.'
        self.position = position

    def encrypt(self, password: str = None) -> bytes:
        l_pass = list(password)

        if self.position >= len(password):
            self.position = 0

        l_pass.insert(self.position, self.secret)

        # try:
        #     l_pass.insert(self.position, self.secret)
        # except IndexError:
        #     l_pass.insert(0, self.secret)

        mixed_pass = ''.join(l_pass)
        return base64.b64encode(mixed_pass.encode())

    def decrypt(self, codes: bytes = None) -> str:
        try:
            mixed_pass = base64.b64decode(codes).decode()
        except binascii.Error as err:
            return ''

        l_mixed_pass = list(mixed_pass)

        for i in range(0, len(self.secret)):
            l_mixed_pass.pop(self.position)

        return ''.join(l_mixed_pass)


if __name__ == '__main__':
    hp = HidePass(secret='I love China', position=1)
    print(hp.encrypt('loveShangHai%1998'))
    print(hp.decrypt(hp.encrypt('loveChina.com')))



