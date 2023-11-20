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
from dataclasses import asdict


_FILE_ = os.path.abspath(__file__)
_SRC_ = os.path.abspath(os.path.join(_FILE_, '../../'))
_CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
_TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))

sys.path.append(_SRC_)
try:
    from type import SSHAgent, LineCmd, KeyValuePair, DelmtIndexType, LineFeature
except ImportError as e:
    raise e


class PySSHClient(object):
    def __init__(self, agent: SSHAgent = None):
        self.host = agent.address
        self.user = agent.username
        self.password = agent.password
        self.port = agent.port
        self.timeout = agent.timeout
        self.pubkey = agent.pubkey

        self.connected = False
        self.client = None

    def connect(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=self.host,
                           port=self.port,
                           username=self.user,
                           password=self.password,
                           timeout=self.timeout,
                           auth_timeout=self.timeout)

            self.connected = True
        except (paramiko.ssh_exception.NoValidConnectionsError, socket.timeout, OSError) as err:
            self.connected = False
        except (paramiko.ssh_exception.AuthenticationException, paramiko.ssh_exception.SSHException) as err:
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

    def formattable(self, sshcmd=None):
        cmd = sshcmd.command
        exitcode, output = self.getstatusoutput(cmd)

        if exitcode != 0:
            return None

        title = None
        value = None
        for ln in output.split('\n'):
            pass

    def formatline(self, linecmd: LineCmd = None):
        cmd = linecmd.cmd
        data = {}

        exitcode, output = self.getstatusoutput(cmd)
        if exitcode != 0:
            return None

        def fetch_value(l_info: list[DelmtIndexType] = None, dataline: str = None) -> str:
            for delimiter_index in l_info:
                dlm = delimiter_index.delimiter
                idx = delimiter_index.index

                try:
                    dataline = dataline.split(dlm)[idx].strip()
                except IndexError:
                    continue

            return dataline

        if linecmd.delimiter:
            for ln in output.split('\n'):
                ln = ln.strip()
                ikey_from, ikey_to = linecmd.ikey.split(':')
                ival_from, ival_to = linecmd.ivalue.split(':')
                delimiter = linecmd.delimiter

                try:
                    lst = [li.strip() for li in ln.split(delimiter)]
                    ikey_from = int(ikey_from)
                    ival_from = int(ival_from)

                    try:
                        ikey_to = int(ikey_to)
                    except ValueError:
                        ikey_to = None
                    try:
                        ival_to = int(ival_to)
                    except ValueError:
                        ival_to = None

                    key = f'{delimiter}'.join(lst[ikey_from:ikey_to])
                    value = f'{delimiter}'.join(lst[ival_from:ival_to])

                    data.update({key: value})
                except IndexError:
                    continue

        if not linecmd.key_value_pairs:
            return data

        for key_value in linecmd.key_value_pairs:
            feature = key_value.feature
            l_info_key = key_value.key
            l_info_value = key_value.value

            key_dataline = val_dataline = None
            for ln in output.split('\n'):
                ln = ln.strip()
                pre = feature.prefix
                key = feature.keyword
                suf = feature.suffix

                pre = pre if pre else ''
                key = key if key else ''
                suf = suf if suf else ''
                if ln.startswith(pre) and ln.endswith(suf) and key in ln:
                    key_dataline = val_dataline = ln.strip()

            key_dataline = fetch_value(l_info_key, key_dataline)
            val_dataline = fetch_value(l_info_value, val_dataline)

            data.update({key_dataline: val_dataline})

        return data


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
        return output list after executed.
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
    agt = SSHAgent('192.16.10.250', username='root', password='password')

    ssh = PySSHClient(agt)
    ssh.connect()
    # opt = ssh.getoutput('ls -l')
    # sopt = ssh.getstatusoutput('lsmem')
    # print(opt, sopt)
    #
    line_cmd = LineCmd(cmd='lscpu',
                       key_value_pairs=[
                           KeyValuePair(feature=LineFeature(prefix='L1d'),
                                        key=[DelmtIndexType(delimiter=':', index=0)],
                                        value=[DelmtIndexType(':', index=1)]),
                           KeyValuePair(feature=LineFeature(prefix='BIOS', keyword='name'),
                                        key=[DelmtIndexType(delimiter=':', index=0)],
                                        value=[DelmtIndexType(':', 1), DelmtIndexType(' ', 2)])

                       ])

    print(ssh.formatline(line_cmd))

    mem_cmd_line = LineCmd(cmd='lsmem',
                           key_value_pairs=[
                               KeyValuePair(feature=LineFeature(prefix='Total', keyword='online memory'),
                                            key=[DelmtIndexType(':', 0)],
                                            value=[DelmtIndexType(':', 1)])
                           ])
    print(ssh.formatline(mem_cmd_line))

    all_cpu_line = LineCmd(cmd='lscpu',
                           delimiter=':',
                           ikey='0:1',
                           ivalue='1:')
    for k, v in ssh.formatline(all_cpu_line).items():
        print(f'{k:30s}', ':', v)


