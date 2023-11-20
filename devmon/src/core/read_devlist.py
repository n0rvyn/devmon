#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-09-24 10:18
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: read_deflist.py
# Tools: PyCharm

"""
---Reading files from 'devlist' to dataclass SNMPAgent---

"""
import os.path
from yaml import safe_load
from dataclasses import asdict
from typing import Optional
from threading import Thread
import sys


_FILE_ = os.path.abspath(__file__)
_SRC_ = os.path.abspath(os.path.join(_FILE_, '../../'))
_CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
_TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))
sys.path.append(_SRC_)
#

try:
    from type import OID, VOID, WaterMark, OIDType, IDRange, SNMPAgent, SSHAgent, Agent
except Exception as e:
    raise e


# def ReadConfig(file: str = None):
#     config = {}
#     try:
#         with open(_CONFIG_, 'r+') as f:
#             config = safe_load(f)
#     except Exception as err:
#         print(err)
#
#     return config

def __read_yaml(file: str = None) -> Optional[dict]:
    try:
        with open(file, 'r+', encoding='utf8') as f:
            return safe_load(f)  # TODO '.localhost.yaml.un~'
    except FileNotFoundError:
        return None


def __read_many_yaml(files: list[str] = None, *ignored_files_prefix) -> list[dict]:
    data = []

    def _read(_file: str = None):
        basename = os.path.basename(_file)
        data.append(__read_yaml(_file)) if not basename.startswith(ignored_files_prefix) else None

    threads = [Thread(target=_read, args=(f,)) for f in files]
    [t.start() for t in threads]
    [t.join() for t in threads]

    return data


def __pickup_agent(data: dict = None) -> tuple[SNMPAgent, SSHAgent]:
    agent = Agent()
    agent_detail = {}

    snmp_agent = SNMPAgent()
    snmp_agent_detail = {}

    ssh_agent = SSHAgent()
    ssh_agent_detail = {}

    """
    Blocks deprecated in the future.
    """
    # try:
    #     data['snmp']['OIDs']['table'] = data['snmp']['OIDs']['id'] if data['snmp']['OIDs']['id'] else data['snmp']['OIDs']['table']
    # except KeyError:
    #     pass
    # try:
    #     data['snmp']['OIDs']['table'] = data['snmp']['OIDs']['id_range'] if data['snmp']['OIDs']['id_range'] else data['snmp']['OIDs']['table']
    # except KeyError:
    #     pass

    # TODO deleting in the future version1

    for key in asdict(agent):
        try:
            agent_detail.update({key: data[key]})
        except KeyError:
            agent_detail.update({key: asdict(agent)[key]})

    for key in asdict(snmp_agent):
        try:
            snmp_agent_detail.update({key: data['snmp'][key]})
        except KeyError:
            snmp_agent_detail.update({key: asdict(snmp_agent)[key]})

    for key in asdict(ssh_agent):
        try:
            ssh_agent_detail.update({key: data['ssh'][key]})
        except KeyError:
            ssh_agent_detail.update({key: asdict(ssh_agent)[key]})

    try:
        _ = snmp_agent_detail['OIDs']
        oids = []
        for oid_dict in snmp_agent_detail['OIDs']:
            oid = OID()

            for key in asdict(oid):
                try:
                    oid_dict[key]
                except KeyError:
                    oid_dict.update({key: asdict(oid)[key]})

            if oid_dict['watermark']:
                watermark_dict = oid_dict['watermark']

                watermark = WaterMark()
                for key in asdict(watermark):
                    try:
                        watermark_dict[key]
                    except KeyError:
                        watermark_dict.update({key: asdict(watermark)[key]})  # update the default value

                [watermark.__setattr__(key, value) for (key, value) in watermark_dict.items()]

                oid_dict['watermark'] = watermark
            [oid.__setattr__(key, value) for (key, value) in oid_dict.items()]
            oids.append(oid)

        # data['OIDs'] = oids
        # data['snmp']['OIDs'] = oids
        snmp_agent_detail['OIDs'] = oids

    except (KeyError, TypeError):
        pass

    try:
        _ = ssh_agent_detail['sshcmd']
        # add contents in the future version
        ssh_agent_detail['sshcmd'] = _
    except (KeyError, TypeError):
        pass

    [snmp_agent.__setattr__(key, value) for (key, value) in snmp_agent_detail.items()]
    [ssh_agent.__setattr__(key, value) for (key, value) in ssh_agent_detail.items()]
    [(snmp_agent.__setattr__(key, value), ssh_agent.__setattr__(key, value)) for (key, value) in agent_detail.items()]

    # return agent
    return snmp_agent, ssh_agent


def __read_agents(directory: str = None) -> tuple[list[SNMPAgent], list[SSHAgent]]:
    snmp_agents: list[SNMPAgent] = []
    ssh_agents: list[SSHAgent] = []

    abs_path = os.path.abspath(directory)
    files = [os.path.join(abs_path, f) for f in os.listdir(abs_path)]

    raw_data = __read_many_yaml(files, 'example', '.git')

    def pickup(_data: dict):
        _snmp_agent, _ssh_agent = __pickup_agent(_data)
        # agents.append(__pickup_snmp_agent(_data))
        snmp_agents.append(_snmp_agent)
        ssh_agents.append(_ssh_agent)

    threads = [Thread(target=pickup, args=(data, )) for data in raw_data]
    [t.start() for t in threads]
    [t.join() for t in threads]

    return snmp_agents, ssh_agents


def read_agents(*directory) -> tuple:
    """
    return: tuple( tuple(snmp_agents, ssh_agents), tuple(snmp_agents, ssh_agents), ... )
    """
    # agents: list[tuple[list, list]] = []
    agents: list[list] = []

    def read(_dir: str = None):
        agents.extend(__read_agents(_dir))

    threads = [Thread(target=read, args=(d,)) for d in directory]
    [t.start() for t in threads]
    [t.join() for t in threads]

    return tuple(agents)


# def ReadAgents() -> tuple[list, list, list, list]:
#     a_side_snmp_agents = []
#     b_side_snmp_agents = []
#
#     a_side_ssh_agents = []
#     b_side_ssh_agents = []
#
#     for d in [_A_SIDE_, _B_SIDE_, _M_ING_]:
#         try:
#             os.path.isdir(d)
#         except FileNotFoundError:
#             raise
#
#         for fl in os.listdir(d):
#             if fl.startswith(('example', '.git')):  # ignore .gitignore
#                 continue
#             if not fl.endswith('yaml'):
#                 continue
#             try:
#                 p = os.path.join(d, fl)
#                 with open(p, 'r+', encoding='utf8') as f:
#                     dev_detail: dict = safe_load(f)
#             except parser.ParserError as err:
#                 raise err
#
#             try:
#                 address = dev_detail['address']
#             except KeyError:
#                 continue
#             except TypeError:
#                 continue
#
#             try:
#                 if not dev_detail['addr_in_cmdb']:
#                     dev_detail['addr_in_cmdb'] = address
#             except KeyError:
#                 dev_detail['addr_in_cmdb'] = address
#
#             snmp_agent = SNMPAgent()
#             for key, val in dev_detail.items():  # modify from line: 120 snmp_agent = ...
#                 snmp_agent.__setattr__(key, val)
#
#             try:
#                 snmp_detail = dev_detail['snmp']
#
#                 # snmp_agent = SNMPAgent(address=address, region=region, area=area, addr_in_cmdb=addr_in_cmdb)
#                 d_snmp_agent = asdict(snmp_agent)
#
#                 l_oids = []  # a list of all OIDs' details for a single snmp agent
#                 for oid_detail in snmp_detail['OIDs']:
#                     oid = OID()  # creating an OID dataclass 'oid'
#                     d_oid = asdict(oid)  # creating a dict based on dataclass 'oid'
#
#                     for key in oid_detail.keys():  # trying to assign exist 'value's to 'key's
#                         try:
#                             if key == 'watermark':
#                                 try:
#                                     low = oid_detail[key]['low']
#                                     high = oid_detail[key]['high']
#                                 except KeyError:
#                                     continue  # a 'watermark' must have attributes: low & high
#
#                                 try:
#                                     restr = oid_detail[key]['restricted']
#                                 except KeyError:
#                                     restr = False  # but restricted is an option, the default value is 'False'
#
#                                 watermark = WaterMark(low=low, high=high, restricted=restr)
#                                 d_oid[key] = watermark
#
#                                 continue
#                             if key == 'id_range':
#                                 try:
#                                     o_start = oid_detail[key]['start']
#                                 except KeyError:
#                                     continue
#
#                                 try:
#                                     o_end = oid_detail[key]['end']
#                                 except KeyError:
#                                     o_end = None
#                                 try:
#                                     o_count = oid_detail[key]['count']
#                                 except KeyError:
#                                     o_count = None
#
#                                 id_range = IDRange(start=o_start,
#                                                    end=o_end,
#                                                    count=o_count)
#                                 d_oid[key] = id_range
#                                 continue
#
#                             d_oid[key] = oid_detail[key]
#                         except KeyError:
#                             continue
#
#                     for key, value in d_oid.items():  # assigning values to attributes of dataclass 'oid'
#                         oid.__setattr__(key, value)
#
#                     if (not oid.perf and not oid.show) and (not oid.read_ref_from and not oid.reference and not oid.watermark):
#                         # oid.perf does not need 'read_ref_from' or 'reference' or 'watermark'
#                         continue
#
#                     l_oids.append(oid)  # appending the dataclass 'oid' to a list
#
#                 for key in d_snmp_agent.keys():
#                     try:
#                         d_snmp_agent[key] = snmp_detail[key]
#                     except KeyError:
#                         continue
#
#                 for key, value in d_snmp_agent.items():
#                     snmp_agent.__setattr__(key, value)
#
#                 snmp_agent.OIDs = l_oids
#
#                 if d is _A_SIDE_:
#                     a_side_snmp_agents.append(snmp_agent)
#                 if d is _B_SIDE_:
#                     b_side_snmp_agents.append(snmp_agent)
#
#             except KeyError:  # 'snmp' key not in dict, maybe this is an SSH agent detail
#                 try:
#                     ssh_detail = dev_detail['ssh']
#
#                 except KeyError as err:
#                     raise err
#
#     return a_side_snmp_agents, b_side_snmp_agents, a_side_ssh_agents, b_side_ssh_agents


if __name__ == '__main__':
    pass



