#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from datetime import datetime
from . import VOID


@dataclass
class PointMeta:
    address: str = None
    region: str = None
    area: str = None
    label: str = None


@dataclass
class Point:
    metadata: PointMeta = None
    timestamp: datetime = None
    data: dict = None

