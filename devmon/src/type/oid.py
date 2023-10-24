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
    table_index:      str = None
    related_symbol:   str = None  # an OID prefix which identifies the id's name or symbol
    exclude_index:    str = None  # OIDs' index excluded for some discontinuous OID table
    label:            str = None  # the label of the OID, e.g., CPU, Memory, Fan...
    explanation:      str = None  # the meaning of OID
    alert:            str = "异常，请持续关注"  # the suffix of an alert
    severity:    CaseServ = '1'
    reference:        str = None
    read_ref_from:    str = None  # read reference from another OID
    watermark:  WaterMark = None
    arithmetic: ArithType = None
    arith_symbol:     str = None
    arith_pos:   ArithPos = 2  # a / b; b takes the position of 2

    # todo add support for OID values need to be combined
    # todo add support for OID values need to be arithmetic with more than 2 values.


@dataclass
class VOID:
    index: str = None
    desc: str = None
    value: str = None
    reference: str = None

#
# @dataclass
# class ROID:
#     index: str = None
#     reference: str = None
#
