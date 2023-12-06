#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Last Modified Time: 2023/4/28 09:23
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# File Name: pushmsg.py
# Tools: PyCharm

"""
---Pushing messages to remote log server---
"""
from subprocess import getoutput
from typing import Literal
from threading import Thread
import socket


EventType = Literal[
    'alert', 'recovery', 'message'
]


class PushMsg(object):
    def __init__(self, server: str, port: int = 514, nc_path: str = None):
        self.server = server
        self.port = port
        self.nc = nc_path if nc_path else getoutput('which nc')
        self.nc_args = '-w1 -u'

    def push(self, msg: str = None):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(3.0)
            msg = msg.encode()
            s.connect((self.server, self.port))
            s.sendall(msg)
            # s.sendto(msg, (self.nc_server, self.nc_port))

            try:
                s.settimeout(0.5)
                s.recv(64)
            except TimeoutError:
                return True
            except ConnectionRefusedError:
                return False

