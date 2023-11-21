#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-09-23 19:51
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: snmp.py
# Tools: PyCharm

"""
---An SSH Client based on 'paramiko' and OpenSSH
"""
import paramiko
import subprocess
import socket
import os
import sys


_FILE_ = os.path.abspath(__file__)
_SRC_ = os.path.abspath(os.path.join(_FILE_, '../../'))
_CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
_TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))

sys.path.append(_SRC_)
try:
    from type import Agent, SNMPDetail, SSHDetail, Entry, EntryValue
except ImportError as e:
    raise e


class PySSHClient(object):
    def __init__(self, agent: Agent = None):
        self.host = agent.address

        ssh_detail = agent.ssh_detail

        self.user = ssh_detail.username
        self.password = ssh_detail.password
        self.port = ssh_detail.port
        self.timeout = ssh_detail.timeout
        self.pubkey = ssh_detail.pubkey

        self.connected = False
        self.client = None
        print(agent)

    def connect(self, timeout: int = None):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=self.host,
                           port=self.port,
                           username=self.user,
                           password=self.password,
                           timeout=timeout if timeout else self.timeout,
                           auth_timeout=timeout if timeout else self.timeout)

            self.connected = True
        except (paramiko.ssh_exception.NoValidConnectionsError, socket.timeout, OSError):
            self.connected = False
        except (paramiko.ssh_exception.AuthenticationException, paramiko.ssh_exception.SSHException):
            self.connected = False

        self.client = client

        return self.connected

    def getoutput(self, cmd, timeout: int = 10) -> str:
        output = ''

        if cmd.endswith('&') or cmd.startswith('setcontext'):
            return output

        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)

            output = ''.join(stdout.readlines())
            error = stderr.readlines()

            if error:
                output += ''.join(error)

        except (AttributeError, paramiko.ssh_exception.SSHException, EOFError, ValueError) as err:
            raise err

        return output

    def getstatusoutput(self, cmd, timeout: int = 10) -> tuple[int, str]:
        cmd = f'{cmd}; echo $?'
        l_output = self.getoutput(cmd, timeout).rstrip('\n').split('\n')

        output = '\n'.join(l_output[0:-1])
        try:
            code = int(l_output[-1])
        except ValueError:
            code = 1

        return code, output

    def read_ssh_stat(self) -> list[EntryValue]:
        ssh_stat_value = 'up' if self.connect(1) else 'down'
        ssh_stat_void = EntryValue(objectname='sysSnmpdStat',
                                   instance='0',
                                    value=ssh_stat_value,
                                    reference='up')
        return [ssh_stat_void]

    def read_entry(self, cmd, timeout: int = 3) -> EntryValue:
        pass


class OpenSSHClient(object):
    def __init__(self, host: str = None, user: str = None, timeout: int = 3):
        self.host = host
        self.user = user
        self.timeout = timeout

    def _init_openssh(self):
        ssh_cmd = f'ssh {self.user}@{self.host} -T -o ConnectTimeout={self.timeout}'
        try:
            client = subprocess.Popen(ssh_cmd,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT,
                                      shell=True)

            client.stdin.write(b'echo EOT\n')
            client.stdin.flush()

            while True:
                line = client.stdout.readline().decode().strip('\n')

                if line == 'EOT':
                    break

            self.connected = True

        except BrokenPipeError as err:
            raise err

        self.client = client
        return self.connected

    def _rsh_openssh(self, cmd: str = None, timeout: int = 3) -> tuple[int, str]:
        if not cmd or not self.connected:
            return 127, ''

        cmd = f'{cmd}\n'.encode()
        EOT = 'echo EOT $?\n'.encode()

        code = 0
        output = ''

        try:
            self.client.stdin.write(cmd)
            self.client.stdin.write(EOT)
            self.client.stdin.flush()

            while True:
                line = self.client.stdout.readline().decode().strip('\n')

                if line.startswith('EOT'):
                    exit_code = line.split()[-1]
                    break

                output += f'{line}\n'

        except BrokenPipeError as err:
            raise err

        return code, output

    def getoutput(self, command, timeout=None) -> list:
        """
        return: output list after executed.
        """
        _output = []
        _return_code = 0

        if not self.connected:
            return _output

        else:
            try:
                _return_code, _output = self._rsh_openssh(command, timeout=timeout)
            except ValueError:
                pass

        return _output

    def getstatusoutput(self, command, timeout=None):
        _output = []
        _return_code = 0

        if not self.connected:
            return _output

        else:
            try:
                _return_code, _output = self._rsh_openssh(command, timeout=timeout)
            except ValueError:
                pass

        _output.insert(0, _return_code)
        return _output


if __name__ == '__main__':
    pass

