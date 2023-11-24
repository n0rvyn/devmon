#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-09-23 19:51
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: snmp.py
# Tools: PyCharm

"""
---A client for reading OID from snmp agent---
"""
from subprocess import getstatusoutput
from typing import Literal
from threading import Thread
from type import Entry, EntryValue, ArithType, Case, ArithPosition, Agent, SNMPDetail

Position = Literal[
    1, 2
]

# OUTOPTS = Literal[
#     'a', 'b', 'e', 'E', 'f', 'F', 'n', 'p', 'q', 'Q', 's', 'S', 't', 'T', 'u', 'U', 'v', 'V', 'x', 'X'
# ]


NO_VALUE_PREFIX = ('No log handling enabled')

NO_VALUE_SUFFIX = ('Unknown Object Identifier',
                   'No Such Instance currently exists at this OID',
                   'No Such Object available on this agent at this OID',
                   )
# SNMPD_DOWN_PREFIX = ('Timeout', 'No log handling enabled')
SNMPD_DOWN_PREFIX = 'Timeout'


class SNMP(object):
    def __init__(self,
                 agent: Agent = None,
                 snmpwalk: str = '/usr/bin/snmpwalk',
                 context: str = None):
        self.agent = agent
        self.snmp_detail = agent.snmp_detail
        self.snmpwalk = snmpwalk
        self.context = context
        self.down = False  # determine if the SNMPD is already down

    def __snmpwalk(self, oid: str, *outopts) -> str:
        """
        Reading str-line value(s) with Linux `snmpwalk` command.

        Param:
            oid (str): a string-line OID
            outopts(tuple): the output options of `snmpwalk`

        Return:
            str: the value of the OID specified depends on the arguments of 'outopts'
        """
        output = ''

        if not oid and self.down:
            return output

        if self.snmp_detail.base:
            l_base = self.snmp_detail.base.rstrip('.').split('.')
            l_oid = oid.lstrip('.').split('.')
            l_base.extend(l_oid)
            oid = '.'.join(l_base)

        opt = ' '.join([f'-O{o}' for o in outopts]) if outopts else '-vQ -vU'

        ver = f'-v {self.snmp_detail.version}'
        retries = f'-r {self.snmp_detail.retries}'
        timeout = f'-t {self.snmp_detail.timeout}'
        comm = f"-c '{self.snmp_detail.community}'" if self.snmp_detail.version != '3' else ''
        user = f'-u {self.snmp_detail.username}' if self.snmp_detail.username else ''
        mib = f'-m {self.snmp_detail.mib}' if self.snmp_detail.mib else ''
        cont = f'-n VF:{self.context}' if self.context else ''
        addr_with_port = (f'{self.agent.address}:{self.snmp_detail.port}'
                          if self.snmp_detail.port else self.agent.address)

        snmpwalk = f'set -H; {self.snmpwalk}' if '!' in comm else self.snmpwalk

        cmd = f"{snmpwalk} {ver} {comm} {mib} " \
              f"{user} {cont} " \
              f"{retries} {timeout} " \
              f"{opt} " \
              f"{addr_with_port} {oid}"

        code, output = getstatusoutput(cmd)
        # in some case, read a wrong value but exit code is 0.
        code = 1 if output.startswith(NO_VALUE_PREFIX) or output.endswith(NO_VALUE_SUFFIX) else code

        # once the snmpd is not reachable, set the parameter to False --> line: 49
        if output.startswith(SNMPD_DOWN_PREFIX):
            self.down = True  # the SNMPD server is not respond

        # return output if code == 0 and value not in NO_VALUE_ERR else None
        return output if code == 0 else ''

    def __read_value_only(self, oid: str = None) -> str:
        return self.__snmpwalk(oid, 'v', 'U', 'Q')

    def __read_as_oid_value(self,
                            oid: str,
                            reference: str = None,
                            unit: str = None,
                            read_ref_from: str = None,
                            read_name_from: str = None,
                            name_prefix: str = None,
                            exclude_index: str = None,
                            exclude_value: str = None,
                            exclude_keywords: list = None,
                            arithmetic: ArithType = None,
                            arith_value: any = None,
                            read_arith_value_from: str = None,
                            arith_position: ArithPosition = 2) -> list[EntryValue]:
        """
        An OID value is a string like: 'hrSWRunPerfMem.29919 = INTEGER: 288248 KBytes'

        In this case, which:
            objectname -> hrSWRunPerfMem
            instance -> 29919
            subtype -> INTEGER
            value -> 288248
            unit -> KBytes
        """
        vals = []
        lines = self.__snmpwalk(oid, 'a', 's', 'e').split('\n')
        refs = self.__read_value_only(read_ref_from).split('\n') if read_ref_from else []
        names = self.__read_value_only(read_name_from).split('\n') if read_name_from else []
        arith_values_read = self.__read_value_only(read_arith_value_from).split('\n') if read_arith_value_from else []

        for ln in lines:
            if not ln:
                continue

            try:
                (object_part, value_part) = ln.split('=')
            except ValueError:
                continue

            _oid = object_part.split('.')
            instance = _oid[-1]
            objectname = _oid[0] if not name_prefix else name_prefix
            # objectname, instance = object_part.split('.')

            subtype = value_part.split(':')[0]
            try:
                value, _unit = value_part.split(':')[-1].split()
            except ValueError:
                value = value_part.split(':')[-1]
                _unit = None

            unit = _unit if not unit else unit  # unit specified has higher priority than the value read

            vals.append(EntryValue(objectname=objectname.strip().strip('"').strip("'").strip(),
                                   instance=instance.strip(),
                                   subtype=subtype.strip(),
                                   value=value.strip().strip('"').strip("'").strip(),
                                   unit=unit,
                                   reference=reference))

        r_vals = []

        def _contains(_s: str = None, _keywords: list[str] = None):
            for _key in _keywords:
                if _key in _s:
                    return True

            return False

        for i in range(len(vals)):
            name = names[i] if len(names) == len(lines) else vals[i].objectname

            if exclude_keywords and _contains(name, exclude_keywords):
                continue

            if arith_value:
                new_value = self._arith_value(arithmetic, vals[i].value, arith_value, arith_position)
            elif len(arith_values_read) == len(lines):
                new_value = self._arith_value(arithmetic, vals[i].value, arith_values_read[i], arith_position)
            else:
                new_value = vals[i].value

            # TODO add before or after the value has been changed.
            if (exclude_index and vals[i].instance in exclude_index) or (
                    exclude_value and new_value in exclude_value):
                continue

            r_vals.append(EntryValue(name,
                                     vals[i].instance,
                                     vals[i].subtype,
                                     # vals[i].value,
                                     new_value,
                                     refs[i] if len(refs) == len(lines) else vals[i].reference,
                                     vals[i].unit))
        return r_vals

    def read(self, entry: Entry = None) -> list[EntryValue]:
        vals = []

        oids: list[str] = [entry.table] if entry.table else []
        oids.extend(entry.group) if entry.group else None

        def _read_target(_oid: str = None,
                         _unit: str = None,
                         _reference: str = None,
                         _read_ref_from: str = None,
                         _read_name_from: str = None,
                         _name_prefix: str = None,
                         _exclude_index: str = None,
                         _exclude_value: str = None,
                         _exclude_keywords: list = None,
                         _arithmetic: ArithType = None,
                         _arith_value: any = None,
                         _read_arith_value_from: str = None,
                         _arith_position: ArithPosition = 2
                         ):
            val = self.__read_as_oid_value(_oid,
                                           reference=_reference,
                                           unit=_unit,
                                           read_ref_from=_read_ref_from,
                                           read_name_from=_read_name_from,
                                           name_prefix=_name_prefix,
                                           exclude_index=_exclude_index,
                                           exclude_value=_exclude_value,
                                           exclude_keywords=_exclude_keywords,
                                           arithmetic=_arithmetic,
                                           arith_value=_arith_value,
                                           read_arith_value_from=_read_arith_value_from,
                                           arith_position=_arith_position
                                           )
            vals.extend(val) if val else None

        threads = [Thread(target=_read_target,
                          args=(o,
                                entry.unit,
                                entry.reference,
                                entry.read_ref_from,
                                entry.read_name_from,
                                entry.name_prefix,
                                entry.exclude_index,
                                entry.exclude_value,
                                entry.exclude_keywords,
                                entry.arithmetic,
                                entry.arith_value,
                                entry.read_arith_value_from,
                                entry.arith_position)) for o in oids] if oids else []
        [t.start() for t in threads]
        [t.join() for t in threads]

        return vals

    def read_snmp_stat(self) -> list[EntryValue]:
        snmp_stat_value = 'down' if self.down else 'up'

        snmp_stat_void = EntryValue(objectname='sysSnmpdStat',
                                    instance='0',
                                    value=snmp_stat_value,
                                    reference='up')
        return [snmp_stat_void]

    @staticmethod
    def _arith_value(arith: ArithType = None,
                     ori_value: any = None,
                     ari_value: any = None,
                     position: int = 2) -> str:
        value = None

        try:
            ori_value = float(ori_value)
            ari_value = float(ari_value)
        except ValueError:
            return ''.join([str(ori_value), str(ari_value)]) if arith == '+' else ori_value

        try:
            if arith == '+':
                value = ori_value + ari_value

            elif arith == '-':
                if position == 2:
                    value = ori_value - ari_value
                if position == 1:
                    value = ari_value - ori_value

            elif arith == '*':
                value = ori_value * ari_value

            elif arith == '/':
                if position == 2:
                    value = ori_value / ari_value
                if position == 1:
                    value = ari_value / ori_value

            elif arith == '%':
                if position == 2:
                    value = ori_value * 98 / ari_value
                if position == 1:
                    value = ari_value * 98 / ori_value

        except ZeroDivisionError:
            pass

        try:
            value = f'{value:.2f}'
        except TypeError:
            pass

        return value


class ContextSNMP(object):
    def __init__(self, agent: Agent, snmpwalk: str = '/usr/bin/snmpwalk'):
        context = agent.snmp_detail.context
        context = context if context else [None]  # [None] instead of [] because [None] has 1 loop, [] is nothing.

        self.snmps = [SNMP(agent, snmpwalk, c) for c in context]

    def read(self, entry: Entry = None) -> list[EntryValue]:
        """
        Read OID dataclass: OID
        """
        voids = []
        for s in self.snmps:
            # void = s.read_oid_dc(oid)
            void = s.read(entry)
            voids.extend(void) if void else []

        return voids

    def read_snmp_stat(self) -> list[EntryValue]:
        return self.snmps[0].read_snmp_stat()


if __name__ == '__main__':
    pass
