#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Literal
from .oid import VOID, OID

# 1: alert
# 2: recovery
# 3: message
CaseType = Literal[
    '1', '2', '3'
]

CaseServ = Literal[
    '1', '3', '5'
]

CaseStat = Literal[
    'closed', 'open'
]


PublishStat = Literal[
    # 0: not published;
    # 1: alert published;
    # 2: recovery published
    0, 1, 2
]


@dataclass
class IDRange:
    start: str = None
    end:   str = None
    count: int = 0


@dataclass
class CaseUpdatePart:
    count: int = 0  # number of repeated times for an 'alert' case
    content: str = None  # diff from alert to recovery
    type: CaseType = '3'  # 1: alert, 2: recovery
    alert: bool = False  # the status of object is normal or not
    current_value: str = None
    publish: PublishStat = 0
    visible: bool = True  # todo add OID


@dataclass
class TheSameCasePart:
    rid: str = None  # resource ID from CMDB
    region: str = None  # DCA, DCB, DCC
    area: str = None  # CBP, MBA, IFA...
    addr_in_cmdb: str = None  # an address related with Resource ID in CMDB
    sources: str = None
    severity: CaseServ = '1'  # 1, 3, 5
    description: str = None
    object: str = None
    threshold: str = None  # watermark for countable value or reference for others
    index: str = None  # the index of OID and VOID; this parameter makes the OID table or OID range cases been separated
    # the SNMPD listened address;
    # make sure the different hosts those have the same OIDs configuration will be created to different cases.
    address: str = None


@dataclass
class Case(TheSameCasePart, CaseUpdatePart):
    id: str = None  # uniq id, generated by python3 method random
    oid: OID = None
    void: VOID = None


