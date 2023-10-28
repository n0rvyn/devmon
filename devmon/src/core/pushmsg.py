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
from subprocess import getstatusoutput
from platform import system
from os import path
import socket


class PushMsg(object):
    def __init__(self, server: str, port: int = 514, nc_path: str = None):
        self.server = server
        self.port = port
        self.nc = nc_path if nc_path else getoutput('which nc')
        self.nc_args = '-w1 -u'

        # if not path.exists(self.nc):
        #     raise FileNotFoundError

    def ____push(self, msg: str):
        # for macOS, '-w1' means different with different nc versions.
        if system() == 'Darwin':
            print("""\n# Warning: for macOS, 'nc' from 'brew' is not supported! Specified the 'nc' path to '/usr/bin/nc' before run this tool.\n""")

        echo_path = getoutput('which echo')
        cmd = f"""{echo_path} '{msg}' | {self.nc} {self.nc_args} {self.server} {self.port}"""
        return_code = getstatusoutput(cmd)[0]

        return True if return_code == 0 else False

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


if __name__ == '__main__':
    pm = PushMsg('localhost', nc_path='/usr/bin/nc', port=10514)
    print(pm.push(f"""{getoutput('date "+%y/%m/%d %H:%M:%S"')} Hello World! """))








