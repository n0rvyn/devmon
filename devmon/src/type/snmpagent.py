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

OutOpts = Literal[
    'v', 'q', 'Q', 's', 'S'
]


@dataclass
class SNMPAgent:
    address: str
    region: str = None  # Data Center, e.g. DCA, DCB...
    area: str = None  # business area, e.g. CBP, MBA...
    addr_in_cmdb: str = None  # an address related with CMDB resource ID
    rid: str = None  # the device resource ID in CMDB
    community: str = 'public'
    version: Version = '2c'
    username: str = None
    context: str = None
    mib: str = None
    retries: int = 3
    timeout: int = 10
    base: str = None  # file: snmp.py line: 59
    OIDs: [OID] = None
