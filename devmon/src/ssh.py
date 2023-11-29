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
import threading

import paramiko
import subprocess
from subprocess import PIPE
import time
import socket
import os
import sys
from random import randint
from threading import Thread
from random import random

try:
    from .agent import Agent, SNMPDetail, SSHDetail
    from .entry import Entry, EntryValue
    from .encrypt import HidePass
except ImportError:
    from encrypt import HidePass
    from agent import Agent, SNMPDetail, SSHDetail
    from entry import EntryValue, Entry


class PySSHClient(object):
    def __init__(self, agent: Agent = None, hide_pass: HidePass = None):
        self.host = agent.address

        ssh_detail = agent.ssh_detail

        _password = ssh_detail.password
        _password = hide_pass.decrypt(_password.encode()) if _password and hide_pass else _password

        self.user = ssh_detail.username
        # self.password = ssh_detail.password if not hide_pass else hide_pass.decrypt(ssh_detail.password.encode())
        self.password = _password
        self.port = ssh_detail.port
        self.pubkey = ssh_detail.pubkey

        self.timeout = ssh_detail.timeout
        self.auth_timeout = ssh_detail.auth_timeout
        self.banner_timeout = ssh_detail.banner_timeout

        self.connected = False
        self.client = None

        self.buff_size = 10240
        self.invoke_shell = ssh_detail.invoke_shell

        self.conn_error = None

        self.openssh = agent.ssh_detail.openssh

        eoc = agent.ssh_detail.end_of_command
        eos = agent.ssh_detail.end_of_symbol
        self.end_of_command = eoc if eoc else 'echo EOT'
        self.end_of_symbol = eos if eos else 'EOT'

    def _connect_paramiko(self, timeout: int = None, auth_timeout: int = None, banner_timeout: int = None) -> bool:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            time.sleep(random()*10 + random()*10)  # TODO necessary???
            client.connect(hostname=self.host,
                           port=self.port,
                           username=self.user,
                           password=self.password,
                           timeout=timeout if timeout else self.timeout,
                           auth_timeout=auth_timeout if auth_timeout else self.auth_timeout,
                           banner_timeout=banner_timeout if banner_timeout else self.banner_timeout)

            self.connected = True

        except (paramiko.ssh_exception.SSHException,
                paramiko.ssh_exception.NoValidConnectionsError,
                paramiko.ssh_exception.AuthenticationException,
                TypeError, OSError, TimeoutError, ConnectionResetError,
                Exception, EOFError,
                socket.error, socket.timeout) as err:

            self.conn_error = f'CONN_SSHD_ERROR: {err}'

        self.client = client
        return self.connected

    def _getoutput_paramiko(self, cmd, timeout: int = 10, invoke_shell: bool = None, get_pty: bool = False) -> str:
        output = ''
        time.sleep(random())

        if not self.connected or not self.client:
            return self.conn_error

        if not cmd or cmd.endswith('&') or cmd.startswith('setcontext'):
            return output

        invoke_shell = self.invoke_shell if not invoke_shell else invoke_shell
        try:
            if invoke_shell:
                rsh = self.client.invoke_shell()
                # time.sleep(1)
                # time.sleep(random())
                rsh.send(f'''{cmd}\n''')
                time.sleep(timeout)
                output = rsh.recv(self.buff_size).decode()

            else:
                stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout, get_pty=get_pty)

                output = ''.join(stdout.readlines())
                error = stderr.readlines()

                output += ''.join(error) if error else ''

        except (AttributeError,
                paramiko.ssh_exception.SSHException,
                paramiko.ssh_exception.ChannelException,
                EOFError, ValueError,
                # paramiko.buffered_pipe.PipeTimeout,
                TimeoutError) as err:
            output = f'EXEC_CMD_ERROR {err}'

        output = output.replace('\r', '').strip('\n ')

        return output

    def _connect_openssh(self, timeout: int = None) -> bool:
        timeout = timeout if timeout else self.timeout

        ssh_cmd = (f'sshpass -p {self.password} '
                   f'ssh {self.user}@{self.host} -T '
                   f'-o ConnectTimeout={timeout} '
                   f'-o StrictHostKeyChecking=No')
        try:
            client = subprocess.Popen(ssh_cmd,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT,
                                      shell=True)

            # client.stdin.write(b'echo EOT\n')
            time.sleep(random())
            client.stdin.write(f'\n\n{self.end_of_command}\n'.encode())
            client.stdin.flush()

            while True:
                line = client.stdout.readline().decode().strip('\n')

                if line.startswith(self.end_of_symbol):
                # if line == 'EOT':
                    break

            self.connected = True
            self.client = client

        except BrokenPipeError as err:
            self.connected = False
            self.conn_error = f'CONN_SSHD_ERROR: {err}'

        return self.connected

    def _exec_command_openssh(self, cmd: str = None) -> PIPE:
        output = None, None, None

        if not self.connected or not cmd:
            return output

        cmd = f'{cmd}\n'.encode()
        # EOT = 'echo EOT $?\n'.encode()
        EOT = f'{self.end_of_command}\n'.encode()

        # exit_code = 0
        # output = ''

        try:
            self.client.stdin.write(cmd)
            self.client.stdin.write(EOT)
            self.client.stdin.flush()

            # while True:
            #     line = self.client.stdout.readline().decode().strip('\n')
            #
            #     if line.startswith('EOT'):
            #         exit_code = line.split()[-1]
            #         break
            #
            #     output += f'{line}\n'

        except BrokenPipeError as err:
            raise err

        return self.client.stdout

    def _getoutput_openssh(self, cmd):
        output = ''
        stdout = self._exec_command_openssh(cmd)
        try:
            while True:
                line = stdout.readline().decode()

                if line.startswith(self.end_of_symbol):
                    break
                output += line
        except (BrokenPipeError, AttributeError) as err:
            output = f'EXEC_CMD_ERROR {err}'

        return output.strip('\n ')

    def getoutput(self, cmd: str = None, timeout: int = 10, invoke_shell: bool = None, get_pty: bool = False):
        return (self._getoutput_paramiko(cmd, timeout, invoke_shell, get_pty)
                if not self.openssh else self._getoutput_openssh(cmd))

    def ____getstatusoutput(self, cmd, timeout: int = 10) -> tuple[int, str]:
        cmd = f'{cmd}; echo $?'
        l_output = self._getoutput_openssh(cmd).rstrip('\n').split('\n')

        output = '\n'.join(l_output[0:-1])
        try:
            code = int(l_output[-1])
        except ValueError:
            code = 1

        return code, output

    def connect(self, timeout: int = None, auth_timeout: int = None, banner_timeout: int = None) -> bool:
        return (self._connect_openssh(timeout)
                if self.openssh else self._connect_paramiko(timeout, auth_timeout, banner_timeout))

    def read_ssh_stat(self) -> list[EntryValue]:
        ssh_stat_value = 'up' if self.connect(self.timeout) else 'down'
        ssh_stat_void = EntryValue(objectname='sysSshdStat',
                                   instance='0',
                                   value=ssh_stat_value,
                                   reference='up')
        return [ssh_stat_void]

    def _rsh(self,
             cmd: str = None,
             regexp: str = None,
             read_name_from: str = None,
             name_regexp: str = None,
             name_prefix: str = None,
             timeout: int = 300) -> list[EntryValue]:
        vals = self.getoutput(cmd, timeout=timeout)
        time.sleep(random())
        # TODO no sleep cause Secsh channel 11 open FAILED: open failed: Connect failed
        names = self.getoutput(read_name_from, timeout) if read_name_from else ''

        pre_name = name_prefix if name_prefix else cmd

        def run_regexp(_value: str = None, _regexp: str = None) -> str:
            return subprocess.getoutput(f'''echo "{_value}" | {_regexp}''').strip('\n ')

        l_vals = vals.split('\n') if not regexp else run_regexp(vals, regexp).split('\n')
        l_names = names.split('\n') if not name_regexp else run_regexp(names, name_regexp).split('\n')

        return [EntryValue(objectname=l_names[i] if len(l_vals) == len(l_names) and read_name_from else pre_name,
                           instance=str(randint(0, 100)),
                           subtype='STRING',
                           value=l_vals[i]) for i in range(len(l_vals))]

    def read_entry(self, entry: Entry, multithread: bool = True) -> list[EntryValue]:
        e_vals = []
        cmd_lines = [entry.table] if entry.table else []

        try:
            cmd_lines.extend(entry.group)
        except TypeError:
            pass  # group is None

        if multithread:
            def read(_cmd: str,
                     _regexp: str = None,
                     _read_name_from: str = None,
                     _name_regexp: str = None,
                     _name_prefix: str = None):
                e_vals.extend(self._rsh(_cmd,
                                        _regexp,
                                        _read_name_from,
                                        _name_regexp,
                                        _name_prefix,
                                        timeout=entry.timeout))
                # e_vals.append(self._rsh(_cmd, _regexp, timeout=entry.timeout))

            threads = [Thread(target=read,
                              args=(cmd,
                                    entry.regexp,
                                    entry.read_name_from,
                                    entry.name_regexp,
                                    entry.name_prefix, ),
                              name=f'T-{self.host}-{entry.label}'
                              ) for cmd in cmd_lines]

            [t.start() for t in threads]
            [t.join() for t in threads]

        else:
            [e_vals.extend(self._rsh(cmd,
                                     entry.regexp,
                                     entry.read_name_from,
                                     entry.name_regexp,
                                     timeout=entry.timeout)) for cmd in cmd_lines]

        return e_vals

    def _shutdown_para(self):
        return self.client.close() if self.client else False

    def _shutdown_openssh(self):
        return self._exec_command_openssh('exit')

    def shutdown(self):
        return self._shutdown_para() if not self.openssh else self._shutdown_openssh()


if __name__ == '__main__':
    agent = Agent(address='21.21.78.192', ssh_detail=SSHDetail(username='root', password='R00t@789', openssh=True))
    client = PySSHClient(agent=agent)
    client.connect()
    print(client.getoutput('vmstat 2 2'))

    agent = Agent(address='21.21.78.192', ssh_detail=SSHDetail(username='root', password='R00t@789', openssh=False))
    pyclient = PySSHClient(agent=agent)
    pyclient.connect()
    print(pyclient.getoutput('vmstat 2 2'))

    print(client.shutdown(), pyclient.shutdown())

