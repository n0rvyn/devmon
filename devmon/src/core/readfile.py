#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-09-24 10:18
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: confeatcher.py
# Tools: PyCharm

"""
---Short description of this Python module---

"""
import os.path
from yaml import safe_load, parser
import sys
from dataclasses import asdict


_FILE_ = os.path.abspath(__file__)
_ROOT_ = os.path.abspath(os.path.join(_FILE_, '../../../'))

if _ROOT_.startswith('/tmp') or _ROOT_ == '/':
    _ROOT_ = '/etc/devmon'

_CONFIG_DIR_ = os.path.join(_ROOT_, 'conf')
_DEVLIST_DIR_ = os.path.join(_ROOT_, 'devlist')
_A_SIDE_ = os.path.join(_DEVLIST_DIR_, 'a-side')
_B_SIDE_ = os.path.join(_DEVLIST_DIR_, 'b-side')
_M_ING_ = os.path.join(_DEVLIST_DIR_, 'maintaining')

_CONFIG_ = os.path.join(_CONFIG_DIR_, 'devmon.yaml')

_SRC_ = os.path.abspath(os.path.join(_FILE_, '../../'))
_CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
_TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))

sys.path.append(_SRC_)

try:
    from type import SNMPAgent
    from type import OID, VOID, WaterMark, OIDType, IDRange
except Exception as e:
    raise e


def ReadConfig():
    config = {}
    try:
        with open(_CONFIG_, 'r+') as f:
            config = safe_load(f)
    except Exception as err:
        print(err)

    return config


def ReadAgents():
    """
    :return: 5-elements tuple
             (a_side_snmp_agents, b_side_snmp_agents, a_side_ssh_agents, b_side_ssh_agents, maintaining_devs)
    """
    a_side_snmp_agents = []
    b_side_snmp_agents = []

    a_side_ssh_agents = []
    b_side_ssh_agents = []

    maintaining_devs = []  # todo make this parameter global, to adding SSH agent been maintaining

    for d in [_A_SIDE_, _B_SIDE_, _M_ING_]:  # todo adding support for maintaining devices
        try:
            os.path.isdir(d)
        except FileNotFoundError:
            raise

        for fl in os.listdir(d):
            if fl.startswith(('example', '.git')):  # ignore .gitignore
                continue
            try:
                p = os.path.join(d, fl)
                with open(p, 'r+') as f:
                    dev_detail: dict = safe_load(f)
            except parser.ParserError as err:
                raise err

            try:
                address = dev_detail['address']
            except KeyError:
                continue
            except TypeError:
                continue

            region = area = None
            try:
                region = dev_detail['region']
            except KeyError:
                pass
            try:
                area = dev_detail['area']
            except KeyError:
                pass
            try:
                addr_in_cmdb = dev_detail['addr_in_cmdb']
            except KeyError:
                addr_in_cmdb = address

            # todo waiting for verify
            snmp_agent = SNMPAgent()
            for key, val in dev_detail.items():  # modify from line: 120 snmp_agent = ...
                snmp_agent.__setattr__(key, val)

            try:
                snmp_detail = dev_detail['snmp']

                # snmp_agent = SNMPAgent(address=address, region=region, area=area, addr_in_cmdb=addr_in_cmdb)
                d_snmp_agent = asdict(snmp_agent)

                l_oids = []  # a list of all OIDs' details for a single snmp agent
                for oid_detail in snmp_detail['OIDs']:
                    oid = OID()  # creating an OID dataclass 'oid'
                    d_oid = asdict(oid)  # creating a dict based on dataclass 'oid'

                    for key in oid_detail.keys():  # trying to assign exist 'value's to 'key's
                        try:
                            if key == 'watermark':
                                try:
                                    low = oid_detail[key]['low']
                                    high = oid_detail[key]['high']
                                except KeyError:
                                    continue  # a 'watermark' must have attributes: low & high

                                try:
                                    restr = oid_detail[key]['restricted']
                                except KeyError:
                                    restr = False  # but restricted is an option, the default value is 'False'

                                watermark = WaterMark(low=low, high=high, restricted=restr)
                                d_oid[key] = watermark

                                continue
                            if key == 'id_range':
                                try:
                                    o_start = oid_detail[key]['start']
                                except KeyError:
                                    continue

                                try:
                                    o_end = oid_detail[key]['end']
                                except KeyError:
                                    o_end = None
                                try:
                                    o_count = oid_detail[key]['count']
                                except KeyError:
                                    o_count = None

                                id_range = IDRange(start=o_start,
                                                   end=o_end,
                                                   count=o_count)
                                d_oid[key] = id_range
                                continue

                            d_oid[key] = oid_detail[key]
                        except KeyError:
                            continue

                    for key, value in d_oid.items():  # assigning values to attributes of dataclass 'oid'
                        oid.__setattr__(key, value)

                    l_oids.append(oid)  # appending the dataclass 'oid' to a list

                for key in d_snmp_agent.keys():
                    try:
                        d_snmp_agent[key] = snmp_detail[key]
                    except KeyError:
                        continue

                for key, value in d_snmp_agent.items():
                    snmp_agent.__setattr__(key, value)

                snmp_agent.OIDs = l_oids

                if d is _A_SIDE_:
                    a_side_snmp_agents.append(snmp_agent)
                if d is _B_SIDE_:
                    b_side_snmp_agents.append(snmp_agent)

            except KeyError:  # 'snmp' key not in dict, maybe this is an SSH agent detail
                try:
                    ssh_detail = dev_detail['ssh']

                except KeyError as ssh_key_err:
                    # raise f'{ssh_key_err}\nNeither SNMP nor SSH detail exist.'
                    raise ssh_key_err

            if d in _M_ING_:
                maintaining_devs.append(dev_detail)
                # todo reading device list as OID, SNMPAgent objects

    return a_side_snmp_agents, b_side_snmp_agents, a_side_ssh_agents, b_side_ssh_agents, maintaining_devs


if __name__ == '__main__':
    print(ReadConfig())
    a_snmp, *_ = ReadAgents()
    [print(agt) for agt in a_snmp]

