#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
---Data type for command 'snmpwalk' options---
"""
from dataclasses import dataclass
from typing import Literal
from .entry import EntryValue, Entry


Version = Literal[
    '1', '2c', '3'
]


@dataclass
class SNMPDetail:
    community:    str = 'public'
    version:  Version = None
    # version:  Version = '2c'
    username:     str = None
    context:     list = None
    mib:          str = None
    retries:      int = 1
    timeout:      int = 1
    port:         int = None
    base:         str = None  # file: snmp.py line: 59
    enum:        dict = None  # the same as file: oid.py line: 63; file: devmon.py line: 278
    entries: list[Entry] = None


@dataclass
class SSHDetail:
    username:       str = 'root'
    password:       str = None
    pubkey:         str = None
    port:           int = 22
    timeout:        int = 60  # timeout (in seconds) for TCP connection
    auth_timeout:   int = 60  # timeout (in seconds) to want for SSH authorization
    banner_timeout: int = 60  # timeout (in seconds) for SSH banner to be present
    invoke_shell: bool = False
    entries: list[Entry] = None


@dataclass
class Host:
    address: str = None  # the address of the device
    region:  str = 'Default Region'  # Data Center, e.g. DCA, DCB...
    area:    str = 'Default Area'    # Business area, e.g. CBP, MBA...
    addr_in_cmdb: str = address      # an address related with CMDB resource ID
    rid: str = 'NO_RESOURCE_ID_ERROR'  # the device resource ID in CMDB


@dataclass
class Agent(Host):
    # address:      str = None  # the address of the device
    # region:       str = None  # Data Center, e.g. DCA, DCB...
    # area:         str = None  # Business area, e.g. CBP, MBA...
    # addr_in_cmdb: str = address  # an address related with CMDB resource ID
    # rid:          str = None  # the device resource ID in CMDB
    snmp_detail: SNMPDetail = None
    ssh_detail:   SSHDetail = None


@dataclass
class AgentGroup:
    agent: list[Host] = None
    snmp_detail: SNMPDetail = None
    ssh_detail: SSHDetail = None
