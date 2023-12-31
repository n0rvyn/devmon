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
from dataclasses import asdict
from .agent import Agent, SNMPDetail, SSHDetail
from .entry import Entry, EntryValue
from .case import Case, MetaData, Data


def build_case(agent: Agent, entry: Entry = None,
               entry_value: EntryValue = None,
               rid: str = None,
               source: str = None) -> Case:
    """
    A threading target for creating case, based on SNMP agent, OID, and value of OID.
    """
    index = entry_value.instance
    val = entry_value.value
    related_val = entry_value.objectname
    reference = entry_value.reference if entry_value.reference else entry.reference
    alert: bool = False
    threshold = None

    if val is None:
        return Case()

    if entry.watermark:  # the value of OID has a watermark
        try:
            val = float(val)
        except (TypeError, ValueError):
            # oid.watermark is specified, but the value fetched is not countable.
            return Case()

        try:
            low = float(entry.watermark.low)
            high = float(entry.watermark.high)
        except TypeError:
            return Case()

        threshold = f'{entry.watermark.low}-{entry.watermark.high}'

        if not entry.watermark.restricted:
            if val < low or val >= high:  # abnormal
                alert = True

        else:  # oid.watermark.restricted is not specified or set to False
            if low < val <= high:  # abnormal
                alert = True

    elif reference:
        threshold = reference
        # `if val in threshold: ` always True if val is ''
        if not val or (str(val) not in str(threshold)):  # abnormal
            alert = True  # alert has a default value 'False'

    if entry_value.value is None:
        return Case()

    snmp_detail: SNMPDetail = agent.snmp_detail
    ssh_detail: SSHDetail = agent.ssh_detail

    objectname = entry_value.objectname if entry_value.objectname else ''
    description = entry.description
    instance = entry_value.instance

    case_object = f'{objectname} {instance}' if entry.show_index else f'{objectname}'

    def _trans_enum(_agent: Agent = None, _entry: Entry = None, _source: str = None, delimiter: str = ','):
        _rtn_val = []
        _snmp_detail = _agent.snmp_detail

        try:  # handle None value of '_entry'
            _lst_val = [v.strip() for v in _source.split(delimiter)]
        except AttributeError:
            return _source

        for _val in _lst_val:
            try:
                _rtn_val.append(_entry.enum[_val])
            except (KeyError, TypeError):
                try:
                    _rtn_val.append(_snmp_detail.enum[_val])
                except (KeyError, TypeError):
                    pass
        return f'{delimiter}'.join(_rtn_val)

    if entry.enum or snmp_detail.enum:  # 'enum' for single OID will rewrite the definition from SNMPAgent
        val = _trans_enum(agent, entry, entry_value.value)
        thd = _trans_enum(agent, entry, threshold)
    else:
        val = entry_value.value
        thd = threshold

    threshold = thd if thd else threshold
    # void of modifying the rest of the code
    value = val if val else entry_value.value

    msg = entry.alert if alert else entry.recovery

    # content = f'{identifier}，{description}{oid.alert}，阈值{threshold}，当前值{value}。'
    content = f'{objectname}，{description}{msg}，阈值{threshold}，当前值{value}。'
    current_val = f'当前值{value}'

    # rid = snmp_agent.rid if snmp_agent.rid else self.find_rid(snmp_agent.addr_in_cmdb)
    # rid = rid if rid else 'Null_Resource_ID'

    # core = TheSameCasePart(rid=rid,  # modify from 'rid=rid' to 'rid=add_rid'
    core = MetaData(rid=rid,  # modify from 'rid=rid' to 'rid=add_rid'
                    region=agent.region,
                    area=agent.area,
                    addr_in_cmdb=agent.addr_in_cmdb,
                    severity=entry.severity,
                    object=case_object,
                    sources=source,
                    description=description,
                    threshold=f'{threshold}',
                    # index=entry_value.instance,
                    address=agent.address)

    try:
        s_core = ''.join(asdict(core).values())
    except TypeError:
        s_core = ''

    b_core = s_core.encode()
    h = hashlib.shake_128(b_core)
    cid = h.hexdigest(25)  # TODO got the same ID if ONLY 'address' is specified for Host() dataclass

    # attach = CaseUpdatePart(count=1, alert=alert, content=content, current_value=current_val)
    attach = Data(count=1, alert=alert, content=content, current_value=current_val, index=entry_value.instance)

    case = Case(id=cid, entry=entry, entry_value=entry_value)
    for key, value in asdict(core).items():
        case.__setattr__(key, value)

    for key, value in asdict(attach).items():
        case.__setattr__(key, value)

    return case

# def entry_to_case(agent: Agent = None,
#                   entry: Entry = None,
#                   alert: bool = False,
#                   threshold: str = None,
#                   entry_value: EntryValue = None,
#                   add_rid: str = None,
#                   source: str = None) -> Case:
#     """
#     Creating Case() object which based on SNMPAgent, OID and other information.
#     # h = hashlib.shake_256(a.encode())
#     # h.hex digest(10)
#     """
#     if entry_value.value is None:
#         return Case()
#
#     # if entry_value.value is None and entry_value.objectname is None:
#     #     return Case()
#
#     snmp_detail: SNMPDetail = agent.snmp_detail
#     ssh_detail: SSHDetail = agent.ssh_detail
#
#     objectname = entry_value.objectname if entry_value.objectname else ''
#     description = entry.description
#     instance = entry_value.instance
#
#     case_object = f'{objectname} {instance}' if entry.show_index else f'{objectname}'
#
#     def _trans_enum(_agent: Agent = None, _entry: Entry = None, _source: str = None, delimiter: str = ','):
#         _rtn_val = []
#         _snmp_detail = _agent.snmp_detail
#
#         try:  # handle None value of '_entry'
#             _lst_val = [v.strip() for v in _source.split(delimiter)]
#         except AttributeError:
#             return _source
#
#         for _val in _lst_val:
#             try:
#                 _rtn_val.append(_entry.enum[_val])
#             except (KeyError, TypeError):
#                 try:
#                     _rtn_val.append(_snmp_detail.enum[_val])
#                 except (KeyError, TypeError):
#                     pass
#         return f'{delimiter}'.join(_rtn_val)
#
#     if entry.enum or snmp_detail.enum:  # 'enum' for single OID will rewrite the definition from SNMPAgent
#         val = _trans_enum(agent, entry, entry_value.value)
#         thd = _trans_enum(agent, entry, threshold)
#     else:
#         val = entry_value.value
#         thd = threshold
#
#     threshold = thd if thd else threshold
#     # void of modifying the rest of the code
#     value = val if val else entry_value.value
#
#     msg = entry.alert if alert else entry.recovery
#
#     # content = f'{identifier}，{description}{oid.alert}，阈值{threshold}，当前值{value}。'
#     content = f'{objectname}，{description}{msg}，阈值{threshold}，当前值{value}。'
#     current_val = f'当前值{value}'
#
#     # rid = snmp_agent.rid if snmp_agent.rid else self.find_rid(snmp_agent.addr_in_cmdb)
#     # rid = rid if rid else 'Null_Resource_ID'
#
#     core = TheSameCasePart(rid=add_rid,  # modify from 'rid=rid' to 'rid=add_rid'
#                            region=agent.region,
#                            area=agent.area,
#                            addr_in_cmdb=agent.addr_in_cmdb,
#                            severity=entry.severity,
#                            object=case_object,
#                            sources=source,
#                            description=description,
#                            threshold=f'{threshold}',
#                            index=entry_value.instance,
#                            address=agent.address)
#
#     try:
#         s_core = ''.join(asdict(core).values())
#     except TypeError:
#         s_core = ''
#
#     b_core = s_core.encode()
#     h = hashlib.shake_128(b_core)
#     cid = h.hexdigest(25)
#
#     attach = CaseUpdatePart(count=1, alert=alert, content=content, current_value=current_val)
#
#     case = Case(id=cid, entry=entry, entry_value=entry_value)
#     for key, value in asdict(core).items():
#         case.__setattr__(key, value)
#
#     for key, value in asdict(attach).items():
#         case.__setattr__(key, value)
#
#     return case
