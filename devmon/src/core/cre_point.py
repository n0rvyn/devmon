#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-10-28 19:28
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: cre_point.py
# Tools: PyCharm

"""
---Creating time series points with SNMPAgent, oid and VOIDs---
"""

from type import PointMeta, Point, SNMPAgent, VOID, OID
from datetime import datetime


def oid_to_point(snmp_agent: SNMPAgent = None, oid: OID = None, l_void: list[VOID] = None):
    if not oid.perf:
        return Point()

    point_meta = PointMeta(snmp_agent.address, snmp_agent.region, snmp_agent.area, oid.label)
    data = {}

    for lv in l_void:
        try:
            float(lv.value)
        except (ValueError, TypeError):
            continue

        if lv.desc:
            data.update({lv.desc: float(lv.value)})

    point = Point(metadata=point_meta,
                  timestamp=datetime.now(),
                  data=data)

    return point



