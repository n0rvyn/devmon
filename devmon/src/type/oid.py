#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
---data type for OID
"""
from dataclasses import dataclass
from typing import Literal


OIDType = Literal[
    'INTEGER', 'STRING'
]


CaseServ = Literal[
    '1', '3', '5'
]


@dataclass
class WaterMark:
    low:  float = None
    high: float = None
    restricted: bool = False  # todo ....!


@dataclass
class IDRange:
    start: str = None
    end:   str = None
    count: int = 0


ArithType = Literal[
    '+', '-', '*', '/', '%'
]


ArithPos = Literal[
    1, 2
]


@dataclass
class OID:
    id:               str = None  # both single OID and OID table entry is allowed.
    id_range:     IDRange = None
    table:            str = None
    group:            str = None  # A set of OIDs; when collecting perf data, insert these values in one document. # todo
    table_index:      str = None
    related_symbol:   str = None  # an OID prefix which identifies the id's name or symbol
    exclude_index:    str = None  # OIDs' index excluded for some discontinuous OID table; for oid -> snmp.py line: 214
    exclude_value:    str = None  # exclude values from values' list; for table -> snmp.py line: 452
    label:            str = None  # the label of the OID, e.g., CPU, Memory, Fan...
    explanation:      str = None  # the meaning of OID
    alert:            str = "异常，请持续关注"  # the suffix of an alert
    severity:    CaseServ = '1'
    reference:        str = None  # -oe no symbol label for enum values  # todo
    read_ref_from:    str = None  # read reference from another OID
    watermark:  WaterMark = None
    arithmetic: ArithType = None
    arith_symbol:     str = None
    arith_pos:   ArithPos = 2  # a / b; b takes the position of 2
    enum:            dict = None  # transform int values to human-readable iterm
    perf:            bool = False  # set to True to calculate performance of OID
    show:            bool = False  # set to True to show the value ONLY
    # file: devmon.py line: 258

    # todo add support for OID values need to be combined
    # todo add support for OID values need to be arithmetic with more than 2 values.
    # todo add support for showing multiple values in one window


@dataclass
class VOID:
    index: str = None
    desc: str = None
    value: str = None
    reference: str = None

