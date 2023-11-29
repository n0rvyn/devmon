#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
---data type for OID
"""
from dataclasses import dataclass
from typing import Literal, Any


# OIDType = Literal[
#     'INTEGER', 'STRING'
# ]


CaseServ = Literal[
    '1', '3', '5'
]


@dataclass
class WaterMark:
    low:  float = None
    high: float = None
    restricted: bool = False


ArithType = Literal[
    '+', '-', '*', '/', '%'
]


ArithPosition = Literal[
    1, 2
]


@dataclass
class Entry:
    """
    Belows will be deprecated in the future version
    """
    # explanation: str = None
    # related_symbol:    str = None
    # arith_symbol: str = None
    # arith_pos: ArithPosition = 2 # a / b; b takes the position of 2
    # table_index: str = None
    # End of deprecation

    # an OID table entry, or many OIDs as a group (list)
    table: str = None
    group: list[str] = None   # A set of OIDs; when collecting perf data, insert these values in one document.

    # a single OID or OID table for reading the last subidentifier (index) from
    read_index_from: str = None   # An oid table for reading index from  # TODO to use or not to use, it's a question.

    # a single OID or OID table for reading the names or descriptions from
    read_name_from: str = None
    name_prefix: str = None
    # Adding index value as oid name's suffix. It's useful when determining a PID number with oid 'hrSWRunName'.
    show_index: bool = False
    name_regexp: str = None

    # parameters for excluding index, value or keywords from OID(s) or OID values
    exclude_index: str = None  # OIDs' index excluded for some discontinuous OID table; for oid -> snmp.py line: 214
    exclude_value: str = None  # exclude values from values' list; for table -> snmp.py line: 452
    exclude_keywords: list = None  # the value contains the keywords will be ignored.

    # a group name of a set of OID values, for filter values in the Time Series Database;
    # 1. using as a tag of InfluxDB's Point, or metadata label of MongoDB Time Series Collection;
    # 2. using as a title the of pm method;
    label: str = None

    # the description of the OID, for mixed up an alert message
    description: str = None
    alert: str = "异常，请关注"
    recovery: str = '已恢复'

    # the level of an alert message, '1', '3' or '5'
    severity: CaseServ = '1'

    # the reference of the OID value, any other values will trigger an alert
    reference: str = None
    # need to read reference value from another OID,
    # e.g., a switch's port has both operator stat and admin stat,
    # we read the admin state as a value and the operator stat as a reference
    read_ref_from: str = None

    # the OID value is in a range
    watermark: WaterMark = None

    # calculating OID value with another one specified
    arithmetic: ArithType = None
    # for 'str' type, only '+' arithmetic is available
    arith_value: Any = None
    read_arith_value_from: str = None
    arith_position: ArithPosition = 2
    # TODO add support for OID values need to be arithmetic with more than 2 values.

    # transform the numeric values to human-readable strings
    enum: dict = None

    # when set to True, the OID is just used for calculating performance data
    perf: bool = False

    # when set to True, the OID is only used for display messages executing the pm method
    show: bool = False

    # specifying a unit for the OID value
    unit: str = None

    # regular expressions support for ssh commands
    regexp: str = None

    # timeout in seconds to read the command output from a remote host
    timeout: int = 6


@dataclass
# class OIDValue:
class EntryValue:
    objectname: str = None
    instance: str = None
    subtype: str = None
    value: str = None
    reference: str = None
    unit: str = None


# @dataclass
# class VOID(OIDValue):
#     index = OIDValue.instance
#     desc = OIDValue.objectname
#     identifier: OIDValue.objectname
#     subtype = OIDValue.subtype
#     value: str = None
#     reference: str = None
#     unit: str = None


