#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-10-28 10:00
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: oid_to_case.py
# Tools: PyCharm

"""
---Creating dataclass Case() from SNMPAgent, OID, VOID and so on...---
"""
import hashlib
from type import SNMPAgent, OID, VOID, Case, TheSameCasePart, CaseUpdatePart
from dataclasses import asdict


def oid_to_case(snmp_agent: SNMPAgent = None,
                oid: OID = None,
                alert: bool = False,
                threshold: str = None,
                void: VOID = None,
                add_rid: str = None,
                source: str = None) -> Case:
    """
    Creating Case() object which based on SNMPAgent, OID and other information.
    # h = hashlib.shake_256(a.encode())
    # h.hexdigest(10)
    """
    if not void.value:
        return Case()

    if void.desc and oid.label:
        obj = f'{oid.label}-{void.desc}'
    else:
        obj = f'{oid.label}'

    def _trans_enum(_agent: SNMPAgent = None, _oid: OID = None, _entry: str = None, delimiter: str = ','):
        _lst_val = [v.strip() for v in _entry.split(delimiter)]
        _rtn_val = []

        for _val in _lst_val:
            try:
                _rtn_val.append(_oid.enum[_val])
            except (KeyError, TypeError):
                try:
                    _rtn_val.append(_agent.enum[_val])
                except (KeyError, TypeError):
                    pass
        return f'{delimiter}'.join(_rtn_val)

    if oid.enum or snmp_agent.enum:  # 'enum' for single OID will rewrite the definition from SNMPAgent
        val = _trans_enum(snmp_agent, oid, void.value)
        thd = _trans_enum(snmp_agent, oid, threshold)  # todo AttributeError
    else:
        val = void.value
        thd = threshold

    threshold = thd
    void.value = val  # void of modifying the rest of the code

    if void.desc:
        content = f'{void.desc}，{oid.explanation}{oid.alert}，阈值{threshold}，当前值{void.value}。'
    else:
        content = f'{oid.explanation}{oid.alert}，阈值{threshold}，当前值{void.value}。'  # todo device only has index, no name available.

    current_val = f'当前值{void.value}'

    # rid = snmp_agent.rid if snmp_agent.rid else self.find_rid(snmp_agent.addr_in_cmdb)
    # rid = rid if rid else 'Null_Resource_ID'

    core = TheSameCasePart(rid=add_rid,  # modify from 'rid=rid' to 'rid=add_rid'
                           region=snmp_agent.region,
                           area=snmp_agent.area,
                           addr_in_cmdb=snmp_agent.addr_in_cmdb,
                           severity=oid.severity,
                           object=obj,
                           sources=source,
                           description=oid.explanation,
                           threshold=f'{threshold}',
                           index=void.index,
                           address=snmp_agent.address)

    try:
        s_core = ''.join(asdict(core).values())
    except TypeError:
        s_core = ''

    b_core = s_core.encode()
    h = hashlib.shake_128(b_core)
    cid = h.hexdigest(20)

    attach = CaseUpdatePart(count=1, alert=alert, content=content, current_value=current_val)

    case = Case(id=cid, oid=oid, void=void)
    for key, value in asdict(core).items():
        case.__setattr__(key, value)

    for key, value in asdict(attach).items():
        case.__setattr__(key, value)
    return case
