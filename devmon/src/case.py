#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Literal
from .entry import Entry, EntryValue

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
    0,  # 0: not published;
    1,  # 1: alert published;
    2  # 2: recovery published
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
    visible: bool = True  # todo add to case


@dataclass
class TheSameCasePart:
    address: str = None
    rid: str = None  # resource ID from CMDB
    region: str = None  # DCA, DCB, DCC
    area: str = None  # CBP, MBA, IFA...
    addr_in_cmdb: str = address  # an address related with Resource ID in CMDB
    sources: str = None
    severity: CaseServ = '1'  # 1, 3, 5
    description: str = None
    object: str = None
    threshold: str = None  # watermark for countable value or reference for others
    index: str = None  # the index of OID and VOID; this parameter makes the OID table or OID range cases been separated
    # the SNMPD listened address;
    # make sure the different hosts those have the same OIDs configuration will be created to different cases.


@dataclass
class MetaData(TheSameCasePart):
    pass


@dataclass
class Data(CaseUpdatePart):
    pass


@dataclass
# class Case(TheSameCasePart, CaseUpdatePart):
class Case(MetaData, Data):
    id: str = None  # uniq id, generated by python3 method random
    entry: Entry = None
    entry_value: EntryValue = None


