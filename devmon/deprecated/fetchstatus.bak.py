#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-09-24 15:53
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: fetchstatus.py
# Tools: PyCharm

"""
---Short description of this Python module---

"""
import os
import sys
from subprocess import getstatusoutput
from typing import Literal
from dataclasses import asdict

_FILE_ = os.path.abspath(__file__)
_SRC_ = os.path.abspath(os.path.join(_FILE_, '../../'))
_CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
_TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))

sys.path.append(_SRC_)

try:
    from core import ReadConfig, ReadAgents, SNMP
    from type import OID, WaterMark, IDRange, VOID, SNMPAgent
except ImportError:
    from .readfile import ReadConfig, ReadAgents


Side = Literal[
    'a', 'b'
]


class FetchSNMPStatus(object):
    def __int__(self):
        # self.a_side = A_SIDE_SNMPs
        # self.b_side = B_SIDE_SNMPs
        pass

    def insert_case(self):
        pass

    def find_case(self):
        pass

    def update_case(self):
        pass

    def read_by_side(self, side: Side = None):
        """
        AttributeError: 'FetchSNMPStatus' object has no attribute 'a_side'
        :param side:
        :return:
        """
        try:
            A_SIDE_SNMPs, B_SIDE_SNMPs, A_SIDE_SSHs, B_SIDE_SSHs, MAINTAIN_DEVS = ReadAgents()
        except TypeError as sign_value_err:
            raise sign_value_err

        if side == 'a':
            agents = A_SIDE_SNMPs
        elif side == 'b':
            agents = B_SIDE_SNMPs
        else:
            return None

        for agt in agents:
            print('-'*40, agt.address, '-'*40)  # todo delete after test
            snmp_agent = SNMPAgent(address=agt.address,
                              community=agt.community,
                              version=agt.version,
                              username=agt.version,
                              mib=agt.mib,
                              retries=agt.retries,
                              timeout=agt.timeout)
            snmp = SNMP(snmp_agent)
            for oid in agt.OIDs:
                type_val = val_oid = l_vals = None

                if oid.id:
                    oid_start = oid.id
                    oid_end = count = None
                elif oid.id_range:
                    oid_start = oid.id_range.start
                    oid_end = oid.id_range.end
                    count = oid.id_range.count
                else:
                    continue

                # read_range also read single OID as long as 'oid_to = count = None'
                # l_vals = snmp_agent.read(oid=oid_start, oid_end=oid_end, count=count)
                l_vals = snmp.read(oid=oid_start, oid_end=oid_end, count=count)

                exclude_index = oid.exclude_index.split(',') if oid.exclude_index else []
                exclude_index = [i.strip() for i in exclude_index]

                for index, val in l_vals:  # loop for each OID
                    if not index or str(index) in exclude_index:
                        continue

                    related_val = snmp.read_by_index_ad_symbol(index=index, symbol=oid.related_symbol)

                    common = f"Host: {agt.address}, " \
                             f"Label: {oid.label}, " \
                             f"Explanation: {oid.explanation}, " \
                             f"Watermark: {oid.watermark} " \
                             f"Value: {val}, " \
                             f"Related Symbol: {related_val}" \
                             f"Reference: {oid.reference}."

                    normal = f"\033[0;38mNormal. \033[0m {common} "

                    warning = f"\033[0;31mWarning!\033[0m {common}"

                    critical = f"Critical -> The OID has a watermark {oid.watermark}, " \
                               f"but the value fetched {val} is not integrable."

                    if oid.watermark:  # the value of OID has a watermark
                        try:
                            val = int(val)
                        except TypeError:
                            # OID's watermark is specified, but the value fetched is not countable.
                            print(critical)
                            continue
                        try:
                            low = int(oid.watermark.low)
                            high = int(oid.watermark.high)

                        except TypeError:
                            err = f'The watermark {oid.watermark} or val: {val} is not integrable,'
                            print(err)
                            continue

                        if low < val < high:
                            print(normal)
                        else:
                            print(warning)

                    elif oid.reference:  # the value of OID has a reference
                        if val == oid.reference:
                            print(normal)
                        else:
                            print(warning)


class FetchSSHStatus(object):
    def __init__(self):
        pass


if __name__ == '__main__':
    f_status = FetchSNMPStatus()
    f_status.read_by_side('a')


