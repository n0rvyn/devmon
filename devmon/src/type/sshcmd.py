#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Literal


@dataclass
class LineFeature:
    keyword: str = None
    prefix: str = None
    suffix: str = None


@dataclass
class TableCmd:
    cmd: str = None
    title: str = None
    desc: str = None
    value: str = None
    

@dataclass
class DelmtIndexType:
    """
    delimiter: the delimiter which to split the line with.
    index: the index of value to be fetched starts from 0.
    """
    delimiter: str = None
    index: int = None


@dataclass
class KeyValuePair:
    feature: LineFeature = None
    key: list[DelmtIndexType] = None
    value: list[DelmtIndexType] = None


@dataclass
class LineCmd:
    cmd: str = None
    key_value_pairs: list[KeyValuePair] = None
    delimiter: str = None
    ikey: str = '0:1'
    ivalue: str = '1:'


