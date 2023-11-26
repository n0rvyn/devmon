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
from yaml import safe_load, parser
from dataclasses import asdict
from threading import Thread
from .encrypt import HidePass
from .entry import Entry, EntryValue, WaterMark
from .agent import Agent, SNMPDetail, SSHDetail, Host


def __read_yaml(file: str = None) -> dict:
    try:
        with open(file, 'r+', encoding='utf8') as f:
            return safe_load(f)
    except (FileNotFoundError, parser.ParserError):
        return {}


def __read_many_yaml(files: list[str] = None, *ignored_files_prefix) -> list[dict]:
    data = []

    def _read(_file: str = None):
        basename = os.path.basename(_file)
        data.append(__read_yaml(_file)) if not basename.startswith(ignored_files_prefix) else None

    threads = [Thread(target=_read, args=(f,)) for f in files]
    [t.start() for t in threads]
    [t.join() for t in threads]

    return data


def __pickup_entry(detail: dict) -> list[Entry]:  # TODO add option type SNMPDetail or SSHDetail
    try:
        _ = detail['entries']
    except KeyError:
        return []

    if not detail['entries']:
        return []

    entries = []

    for entry_dict in detail['entries']:
        entry = Entry()

        for key in asdict(entry).keys():
            try:
                entry_dict[key]
            except KeyError:
                entry_dict.update({key: asdict(entry)[key]})

        if entry_dict['watermark']:
            watermark_dict = entry_dict['watermark']
            watermark = WaterMark()
            for key in asdict(watermark).keys():
                try:
                    watermark_dict[key]
                except KeyError:
                    watermark_dict.update({key: asdict(watermark)[key]})  # update the default value

            [watermark.__setattr__(key, value) for (key, value) in watermark_dict.items()]

            entry_dict['watermark'] = watermark
        [entry.__setattr__(key, value) for (key, value) in entry_dict.items()]
        entries.append(entry)

    return entries


def __pickup_hosts(host_data: list[dict] = None) -> list[Host]:
    if not host_data:
        return []

    hosts = []
    for h in host_data:
        host = Host()
        host_dict = asdict(host)
        for key in host_dict.keys():
            try:
                host_dict.update({key: h[key]})
            except KeyError:
                pass
        [host.__setattr__(key, value) for (key, value) in host_dict.items()]
        hosts.append(host)

    return hosts


def __pickup_agent(data: dict = None) -> list[Agent]:
    snmp_detail = SNMPDetail()
    snmp_detail_dict = asdict(snmp_detail)
    ssh_detail = SSHDetail()
    ssh_detail_dict = asdict(ssh_detail)

    try:
        host_list = data['host']
    except KeyError:
        host_list = [data]

    hosts = __pickup_hosts(host_list)

    for k_snmp in snmp_detail_dict.keys():
        try:
            snmp_detail_dict.update({k_snmp: data['snmp'][k_snmp]})
        except KeyError:
            pass

    for k_ssh in ssh_detail_dict.keys():
        try:
            ssh_detail_dict.update({k_ssh: data['ssh'][k_ssh]})
        except KeyError:
            pass

    snmp_detail_dict['entries'] = __pickup_entry(snmp_detail_dict)
    ssh_detail_dict['entries'] = __pickup_entry(ssh_detail_dict)

    [snmp_detail.__setattr__(key, value) for (key, value) in snmp_detail_dict.items()]
    [ssh_detail.__setattr__(key, value) for (key, value) in ssh_detail_dict.items()]

    # agent_detail['snmp_detail'] = snmp_detail
    # agent_detail['ssh_detail'] = ssh_detail
    #
    # [agent.__setattr__(key, value) for (key, value) in agent_detail.items()]
    agents: list[Agent] = []
    for host in hosts:
        agent = Agent()
        [agent.__setattr__(key, value) for (key, value) in asdict(host).items()]
        agent.snmp_detail = snmp_detail
        agent.ssh_detail = ssh_detail
        agents.append(agent)

    return agents


def __read_agents(directory: str = None) -> list[Agent]:
    # snmp_agents: list[SNMPAgent] = []
    # ssh_agents: list[SSHAgent] = []
    agents: list[Agent] = []

    abs_path = os.path.abspath(directory)
    files = [os.path.join(abs_path, f) for f in os.listdir(abs_path)]

    raw_data = __read_many_yaml(files, 'example', '.git')

    def pickup(_data: dict):
        # _snmp_agent, _ssh_agent = __pickup_agent(_data)
        # agents.append(__pickup_agent(_data))
        agents.extend(__pickup_agent(_data))
        # snmp_agents.append(_snmp_agent)
        # ssh_agents.append(_ssh_agent)

    threads = [Thread(target=pickup, args=(data, )) for data in raw_data]
    [t.start() for t in threads]
    [t.join() for t in threads]

    return agents
    # return snmp_agents, ssh_agents


def read_agents(*directory) -> tuple[list[Agent], ...]:
    """
    return: tuple( tuple(snmp_agents, ssh_agents), tuple(snmp_agents, ssh_agents), ... )
    """
    # agents: list[tuple[list, list]] = []
    agents: list[list[Agent]] = []

    def read(_dir: str = None):
        # agents.extend(__read_agents(_dir))
        agents.append(__read_agents(_dir))

    threads = [Thread(target=read, args=(d,)) for d in directory]
    [t.start() for t in threads]
    [t.join() for t in threads]

    return tuple(agents)


if __name__ == '__main__':
    print(read_agents('../../devlist/a-side'))
    print(read_agents('../../devlist/b-side'))
