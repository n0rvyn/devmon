#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
---Data type for command 'snmpwalk' options---
"""
from dataclasses import dataclass
from typing import Literal
from .oid import OID


Version = Literal[
    '1', '2c', '3'
]


# OutOpts = Literal[
#     'v', 'q', 'Q', 's', 'S'
# ]
#

@dataclass
class Agent:
    address:      str = None  # the address of the device
    region:       str = None  # Data Center, e.g. DCA, DCB...
    area:         str = None  # Business area, e.g. CBP, MBA...
    addr_in_cmdb: str = None  # an address related with CMDB resource ID
    rid:          str = None  # the device resource ID in CMDB


@dataclass
class SNMPAgent(Agent):
    # address:      str = None  # the address of the device
    # region:       str = None  # Data Center, e.g. DCA, DCB...
    # area:         str = None  # Business area, e.g. CBP, MBA...
    # description: str = 'Unknown'  # the device name or description
    # todo add a name for device; the key already exist in Case(); file: devmon.py line: 288
    # addr_in_cmdb: str = None  # an address related with CMDB resource ID
    # rid:          str = None  # the device resource ID in CMDB
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
    OIDs:   list[OID] = None


@dataclass
class SSHAgent(Agent):
    username: str = 'root'
    password: str = None
    port: int = 22
    pubkey: str = None
    timeout: int = 3

