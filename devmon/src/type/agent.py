#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
---Data type for command 'snmpwalk' options---
"""
from dataclasses import dataclass
from typing import Literal
from .oid import EntryValue, Entry


Version = Literal[
    '1', '2c', '3'
]


@dataclass
class SNMPDetail:
    community:    str = 'public'
    version:  Version = '2c'
    username:     str = None
    context:     list = None
    mib:          str = None
    retries:      int = 1
    timeout:      int = 1
    port:         int = None
    base:         str = None  # file: snmp.py line: 59
    enum:        dict = None  # the same as file: oid.py line: 63; file: devmon.py line: 278
    entries:   list[Entry] = None


@dataclass
class SSHDetail:
    username:   str = 'root'
    password:   str = None
    pubkey:     str = None
    port:       int = 22
    timeout:    int = 3
    entries: list[Entry] = None


@dataclass
class Agent:
    address:      str = None  # the address of the device
    region:       str = None  # Data Center, e.g. DCA, DCB...
    area:         str = None  # Business area, e.g. CBP, MBA...
    addr_in_cmdb: str = address  # an address related with CMDB resource ID
    rid:          str = None  # the device resource ID in CMDB
    snmp_detail: SNMPDetail = None
    ssh_detail:   SSHDetail = None
