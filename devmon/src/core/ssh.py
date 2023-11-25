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
import time
import socket
import os
import sys
from .encrypt import HidePass
from random import randint
from threading import Thread


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

    def connect(self, timeout: int = None, auth_timeout: int = None, banner_timeout: int = None):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
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

    def getoutput(self, cmd, timeout: int = 10, invoke_shell: bool = None, get_pty: bool = False) -> str:
        output = ''

        if not self.connected or not self.client:
            return self.conn_error

        if cmd.endswith('&') or cmd.startswith('setcontext'):
            return output

        invoke_shell = self.invoke_shell if not invoke_shell else invoke_shell
        try:
            if invoke_shell:
                rsh = self.client.invoke_shell()
                # time.sleep(1)
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
            output = f'EXEC_CMD__ERROR {err}'

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
        ssh_stat_void = EntryValue(objectname='sysSshdStat',
                                   instance='0',
                                   value=ssh_stat_value,
                                   reference='up')
        return [ssh_stat_void]

    def _rsh(self,
             cmd: str = None,
             regexp: str = None,
             timeout: int = 300) -> EntryValue:
        # e_vals = [EntryValue(objectname=f'''"{cmd}"''',
        #                      instance=str(randint(0, 100)),
        #                      subtype='STRING',
        #                      value=val if not regexp else subprocess.getoutput(f'''echo {val} | {regexp}''')
        #                      )
        #           for val in self.getoutput(cmd,
        #                                     timeout=timeout).strip('\n').split('\n')]
        # return e_vals  # TODO add support for 'read_name_from' --> regexp
        val = self.getoutput(cmd, timeout=timeout).replace('\r', '').strip('\n ')

        return EntryValue(objectname=f'''"{cmd}"''',
                          instance=str(randint(0, 100)),
                          subtype='STRING',
                          value=(val
                                 if not regexp
                                 else subprocess.getoutput(f'''printf "{val}" | {regexp}''').strip('\n ')))

    def read_entry(self, entry: Entry) -> list[EntryValue]:
        cmd_lines = [entry.table] if entry.table else []

        try:
            cmd_lines.extend(entry.group)
        except TypeError:
            pass  # group is None

        e_vals = []

        def read(_cmd: str, _regexp: str = None):
            # e_vals.extend(self._rsh(_cmd, _regexp, timeout=timeout))
            e_vals.append(self._rsh(_cmd, _regexp, timeout=entry.timeout))

        threads = [Thread(target=read,
                          args=(cmd, entry.regexp, ),
                          name=f'T-{self.host}-{entry.label}'
                          ) for cmd in cmd_lines]

        [t.start() for t in threads]
        [t.join() for t in threads]

        return e_vals


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
