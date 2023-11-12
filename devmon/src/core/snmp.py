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
from typing import Literal, Optional
from threading import Thread
from type import SNMPAgent, OID, VOID, ArithType, IDRange

Position = Literal[
    1, 2
]

OUTOPTS = Literal[
    'a', 'b', 'e', 'E', 'f', 'F', 'n', 'p', 'q', 'Q', 's', 'S', 't', 'T', 'u', 'U', 'v', 'V', 'x', 'X'
]


class SNMP(object):
    def __init__(self, snmp_agent: SNMPAgent = None, snmpwalk: str = '/usr/bin/snmpwalk', context: str = None):
        self.agent = snmp_agent
        self.snmpwalk = snmpwalk
        self.snmpd_stat = True  # todo add alert message for SNMPD down
        self.context = context

    def _read_oid(self, oid: str, *outopts) -> str:
        """
        return string like:
        HOST-RESOURCES-MIB::hrSWRunPerfCPU.28464 = 113
        """
        output = ''

        if not self.snmpd_stat or not oid:
            return output

        if self.agent.base:
            l_base = self.agent.base.rstrip('.').split('.')
            l_oid = oid.lstrip('.').split('.')
            l_base.extend(l_oid)
            oid = '.'.join(l_base)

        opt = ' '.join([f'-O{o}' for o in outopts]) if outopts else '-vQ -vU'

        ver = f'-v {self.agent.version}'
        retries = f'-r {self.agent.retries}'
        timeout = f'-t {self.agent.timeout}'
        comm = f"-c '{self.agent.community}'" if self.agent.version != '3' else ''
        user = f'-u {self.agent.username}' if self.agent.username else ''
        mib = f'-m {self.agent.mib}' if self.agent.mib else ''
        cont = f'-n VF:{self.context}' if self.context else ''

        self.snmpwalk = f'set -H; {self.snmpwalk}' if '!' in comm else self.snmpwalk  # todo -H or +H????

        cmd = f"{self.snmpwalk} {ver} {comm} {mib} " \
              f"{user} {cont} " \
              f"{retries} {timeout} " \
              f"{opt} " \
              f"{self.agent.address} {oid}"

        NO_VALUE_ERR = ['No Such Instance currently exists at this OID',
                        'No Such Object available on this agent at this OID',
                        'No log handling enabled']

        NO_VALUE_SUFFIX = ('Unknown Object Identifier',)

        code, output = getstatusoutput(cmd)
        code = 1 if output in NO_VALUE_ERR or output.endswith(NO_VALUE_SUFFIX) else code

        # once the snmpd is not reachable, set the parameter to False --> line: 49
        if output.startswith('Timeout'):
            self.snmpd_stat = False  # the SNMPD server is not respond

        # return output if code == 0 and value not in NO_VALUE_ERR else None
        return output if code == 0 else ''

    def ____read_oid_val(self, oid: str) -> Optional[str]:
        """
        return only the value of the OID.
        """
        # output = self._read_oid(oid, outopts)
        output = self._read_oid(oid, 'v')
        # display the value only (with the type and the unit)
        # like: INTEGER: 0 KBytes

        if output:
            if output.count('\n') > 1:
                return None

            val_type = output.split(':')[0]
            if val_type in ['INTEGER', 'Counter64']:
                val = output.split()[1].strip().strip('"')  # values include `"
            else:
                val = output.split(':')[-1].strip().strip('"')  # values include `"
        else:
            val = None

        return val

    def _read_oid_val(self, oid: str) -> str:
        return '\n'.join([ln.strip().strip('"') for ln in self._read_oid(oid, 'U', 'v', 'Q').split('\n')])

    def _read_oid_index(self, oid: str) -> str:
        return '\n'.join(ln.split('=')[0].split('.')[-1].strip()
                         for ln in self._read_oid(oid, 'U', 's', 'Q').split('\n'))

    def _read_id(self,
                 oid: str = None,
                 related_symbol: str = None,
                 exclude_index: str = None,
                 exclude_value: str = None,
                 read_ref_from: str = None,
                 arithmetic: ArithType = None,
                 arith_symbol: str = None,
                 arith_pos: Position = None,
                 unit: str = None) -> VOID:
        void = VOID()

        index = oid.split('.')[-1]
        try:
            int(index)
        except ValueError:
            index = '0'

        if exclude_index and str(index) in exclude_index:  # exclude index for oid or oid_range
            return void

        value = self._read_oid_val(oid)

        if related_symbol:
            if len(related_symbol.split('.')) > 1:
                desc = self._read_oid_val(related_symbol)
            else:
                desc = self._read_oid_val(f'{related_symbol}.{index}')
        else:
            desc = self._read_oid_desc(oid)

        if read_ref_from:
            ref = self._read_oid_val(f'{read_ref_from}.{index}')
        else:
            ref = None

        if arithmetic:
            value = self._read_arith_symbol(index, arith_symbol, arithmetic, value, arith_pos)
        else:
            pass

        # exclude value for oid and oid_range
        if exclude_value and (str(value) in exclude_value or str(desc) in exclude_value):
            return void

        void = VOID(index=index, value=value, desc=desc, reference=ref, unit=unit)

        return void

    def _read_id_range(self,
                       oid_start: str = None,
                       oid_end: str = None,
                       count: int = None,
                       related_symbol: str = None,
                       exclude_index: str = None,
                       exclude_value: str = None,
                       read_ref_from: str = None,
                       arithmetic: ArithType = None,
                       arith_symbol: str = None,
                       arith_pos: Position = None,
                       unit: str = None) -> list[VOID]:

        voids = []

        def read_id_target(_oid: str = None,
                           _related_symbol: str = None,
                           _exclude_index: str = None,
                           _exclude_value: str = None,
                           _read_ref_from: str = None,
                           _arithmetic: ArithType = None,
                           _arith_symbol: str = None,
                           _arith_pos: Position = None,
                           _unit: str = None):
            voids.append(self._read_id(_oid, _related_symbol, _exclude_index,
                                       _exclude_value, _read_ref_from, _arithmetic, _arith_symbol, _arith_pos, _unit))

        try:
            index_from = int(oid_start.split('.')[-1])
            oid_prefix = '.'.join(oid_start.split('.')[0:-1])
        except ValueError:
            index_from = 1
            oid_prefix = oid_start
        try:
            index_to = int(oid_end.split('.')[-1])
        except ValueError:
            index_to = index_from + count
        except AttributeError:
            index_to = index_from + count

        threads = []
        for i in range(index_from, index_to):
            oid = f'{oid_prefix}.{i}'
            threads.append(Thread(target=read_id_target,
                                  args=(oid, related_symbol, exclude_index,
                                        exclude_value, read_ref_from,
                                        arithmetic, arith_symbol, arith_pos,)))

        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]

        return voids

    @staticmethod
    def _arith_value(arith: ArithType = None,
                     ori_value: float = None,
                     ari_value: float = None,
                     position: int = 2) -> str:
        value = None
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

    def _read_arith_symbol(self,
                           index: str = None,
                           symbol: str = None,
                           arith: ArithType = None,
                           ori_value: str = None,
                           position: Position = 2) -> str:
        """
        Read OID values those need to calculate with another value which has the same index
        e.g.
            HOST-RESOURCES-MIB::hrStorageUsed.1 = INTEGER: 3239539
            HOST-RESOURCES-MIB::hrStorageSize.1 = INTEGER: 4194304
        """
        # void = VOID(index=index)
        val = None

        try:
            int(index)
            ori_value = float(ori_value)

            oid = f'{symbol}.{index}'
            # ari_value = float(self.read(oid=oid)[0].value)
            ari_value = float(self._read_oid_val(oid))
            val = self._arith_value(arith=arith, ori_value=ori_value, ari_value=ari_value, position=position)

        except (TypeError, ValueError):
            return val

        return val

    # def ____read_ref_from_value(self, index: str = None, symbol: str = None) -> str:
    #     """
    #     Read OID reference (if it has one) from another OID which has the same index
    #     """
    #     reference = None
    #     try:
    #         int(index)
    #         oid = f'{symbol}.{index}'
    #         reference = self._read_oid_val(oid)
    #     except ValueError:
    #         pass
    #     except AttributeError:
    #         pass
    #
    #     return reference

    def _____read_table_vals(self, table: str = None):
        # output = self._read_oid(table, outopts='Q')
        output = self._read_oid_val(table)
        l_oid_vals = output.split('\n') if output else []
        # l_oid_vals = self._read_oid(table, outopts='Q').split('\n')
        return [o_v.split('=')[-1].strip().strip('"').strip() for o_v in
                l_oid_vals]  # add strip('"') for values `"value`"

    def _____read_table_index(self, table: str = None):
        output = self._read_oid(table, outopts='Q')
        l_oid_vals = output.split('\n') if output else []
        return [o_v.split('=')[0].strip().split('.')[-1] for o_v in l_oid_vals]

    def _read_table_vals(self, table: str = None) -> list[str]:
        return self._read_oid_val(table).split('\n')

    def _read_table_indexes(self, table: str = None) -> list[str]:
        return self._read_oid_index(table).split('\n')

    def _read_table(self,
                    table: str = None,
                    index_table: str = None,
                    related_symbol_table: str = None,
                    exclude_index: str = None,
                    exclude_value: str = None,
                    exclude_keywords: list[str] = None,
                    reference_symbol_table: str = None,
                    arith_symbol_table: str = None,
                    arith: ArithType = None,
                    arith_pos: int = 2,
                    unit: str = None,
                    group: bool = False) -> Optional[list[VOID]]:
        vals_table = self._read_table_vals(table)
        vals_related = self._read_table_vals(related_symbol_table)
        vals_arith = self._read_table_vals(arith_symbol_table)
        vals_index = self._read_table_vals(index_table) if index_table else self._read_table_indexes(table)
        vals_ref = self._read_table_vals(reference_symbol_table)

        voids = []

        # vals_table = vals_table if vals_table != [''] else None
        vals_related = None if vals_related == [''] else vals_related
        # vals_arith = None if vals_arith == [''] else vals_arith
        vals_index = None if vals_index == [''] else vals_index
        vals_ref = None if vals_ref == [''] else vals_ref  # todo verity None type or [''] value

        def _contains(_s: str = None, _keywords: list[str] = None):
            for _key in _keywords:
                if _key in _s:
                    return True

            return False

        for n in range(1, len(vals_table) + 1):
            i = n - 1
            if not vals_table[i]:
                continue

            if vals_arith != ['']:  # modify from >>if vals_arith<<
                try:
                    ori_value = float(vals_table[i])
                    ari_value = float(vals_arith[i])
                except (TypeError, ValueError, IndexError):
                    continue

                val = self._arith_value(arith=arith, ori_value=ori_value, ari_value=ari_value,
                                        position=arith_pos)
            else:
                val = vals_table[i]

            try:
                index = vals_index[i]
            except (IndexError, TypeError):
                index = str(i)
                # index = None

            try:
                rel_val = vals_related[i] if not group else f'{table}.{vals_related[i]}'
            except (IndexError, TypeError):
                # rel_val = None
                rel_val = f'{self._read_oid_desc(table)}.{index}'

            try:
                ref = vals_ref[i]
            except (IndexError, TypeError):
                ref = None

            if exclude_index and str(index) in exclude_index:
                continue
            if exclude_value and (str(rel_val) in exclude_value or str(val) in exclude_value):
                continue

            if exclude_keywords and (
                    _contains(str(rel_val), exclude_keywords) or _contains(str(val), exclude_keywords)):
                continue

            voids.append(VOID(index=index, desc=rel_val, value=val, reference=ref, unit=unit))

        return voids

    def ____read_group(self,
                       oids: list[str] = None,
                       related_symbol: str = None,
                       exclude_index: str = None,
                       exclude_value: str = None,
                       read_ref_from: str = None,
                       arithmetic: ArithType = None,
                       arith_symbol: str = None,
                       arith_pos: Position = None) -> list[VOID]:
        return [self._read_id(oid=oid,
                              related_symbol=related_symbol,
                              exclude_index=exclude_index,
                              exclude_value=exclude_value,
                              read_ref_from=read_ref_from,
                              arithmetic=arithmetic,
                              arith_symbol=arith_symbol,
                              arith_pos=arith_pos)
                for oid in oids]

    def _read_group(self,
                    tables: list[str] = None,
                    index_table: str = None,
                    related_symbol_table: str = None,
                    exclude_index: str = None,
                    exclude_value: str = None,
                    exclude_keywords: list[str] = None,
                    reference_symbol_table: str = None,
                    arith_symbol_table: str = None,
                    arith: ArithType = None,
                    arith_pos: int = 2,
                    unit: str = None
                    ):
        voids = []

        [voids.extend(self._read_table(table=table,
                                       index_table=index_table,
                                       related_symbol_table=related_symbol_table,
                                       exclude_index=exclude_index,
                                       exclude_value=exclude_value,
                                       exclude_keywords=exclude_keywords,
                                       reference_symbol_table=reference_symbol_table,
                                       arith_symbol_table=arith_symbol_table,
                                       arith=arith,
                                       arith_pos=arith_pos,
                                       unit=unit, group=True)) for table in tables]
        return voids

    def read_oid_dc(self, oid: OID = None) -> list[VOID]:
        """
        Read OID dataclass: OID
        """
        voids = [VOID()]
        if oid.id:  # deprecated
            print(f'Warning: [{oid.label}] id is deprecated, use table instead.')
            void = self._read_id(oid=oid.id, related_symbol=oid.related_symbol,
                                 exclude_index=oid.exclude_index,
                                 exclude_value=oid.exclude_value,
                                 read_ref_from=oid.read_ref_from,
                                 arithmetic=oid.arithmetic,
                                 arith_symbol=oid.arith_symbol,
                                 arith_pos=oid.arith_pos)
            return [void]

        if oid.id_range:
            voids = self._read_id_range(oid_start=oid.id_range.start,
                                        oid_end=oid.id_range.end,
                                        count=oid.id_range.count,
                                        related_symbol=oid.related_symbol,
                                        exclude_index=oid.exclude_index,
                                        exclude_value=oid.exclude_value,
                                        read_ref_from=oid.read_ref_from,
                                        arithmetic=oid.arithmetic,
                                        arith_symbol=oid.arith_symbol,
                                        arith_pos=oid.arith_pos,
                                        unit=oid.unit)
            return voids

        if oid.table:
            voids = self._read_table(table=oid.table,
                                     index_table=oid.table_index,
                                     related_symbol_table=oid.related_symbol,
                                     exclude_index=oid.exclude_value,
                                     exclude_value=oid.exclude_value,
                                     exclude_keywords=oid.exclude_keywords,
                                     arith_symbol_table=oid.arith_symbol,
                                     reference_symbol_table=oid.read_ref_from,
                                     arith=oid.arithmetic,
                                     arith_pos=oid.arith_pos,
                                     unit=oid.unit)

        if oid.group:
            voids = self._read_group(tables=oid.group,
                                     related_symbol_table=oid.related_symbol,
                                     exclude_value=oid.exclude_value,
                                     exclude_index=oid.exclude_index,
                                     exclude_keywords=oid.exclude_keywords,
                                     reference_symbol_table=oid.read_ref_from,
                                     arith=oid.arithmetic,
                                     arith_symbol_table=oid.arith_symbol,
                                     arith_pos=oid.arith_pos,
                                     unit=oid.unit)

        return voids

    @staticmethod
    def _read_oid_desc(oid: str = None):
        """
        Read description from OID
        From:
            1. GPFS-MIB::gpfsFileSystemStatCacheHit."gpfs_data"
            2. UCD-SNMP-MIB::ssSwapIn.0
        To:
            1. gpfs_data
            2. ssSwapIn
        """
        oid_parts = oid.split('.')
        while True:
            try:
                if oid_parts[-1].isnumeric():
                    oid_parts.pop(-1)
                else:
                    return oid_parts[-1]
            except IndexError:
                return None


class ContextSNMP(object):
    def __init__(self, snmp_agent: SNMPAgent, snmpwalk: str = '/usr/bin/snmpwalk'):
        context = snmp_agent.context
        context = context if context else [None]  # [None] instead of [] because [None] has 1 loop, [] is nothing.

        self.snmps = [SNMP(snmp_agent, snmpwalk, c) for c in context]

    def read_oid_dc(self, oid: OID = None) -> list[VOID]:
        """
        Read OID dataclass: OID
        """
        voids = []
        for s in self.snmps:
            void = s.read_oid_dc(oid)
            voids.extend(void) if void else []

        return voids


if __name__ == '__main__':
    agent = SNMPAgent(address='172.16.10.250', community='public')
    snmp = SNMP(agent)

    # read single OID
    s_oid = OID(id='UCD-SNMP-MIB::memTotalFree.0', related_symbol='UCD-SNMP-MIB::memAvailSwap',
                read_ref_from='HOST-RESOURCES-MIB::hrMemorySize',
                arithmetic='%', arith_symbol='UCD-SNMP-MIB::memTotalReal', arith_pos=2)
    print(snmp.read_oid_dc(s_oid))

    # read OID range
    r_oid = OID(id_range=IDRange(start='UCD-SNMP-MIB::memTotalFree.0', count=1),
                related_symbol='UCD-SNMP-MIB::memAvailSwap',
                read_ref_from='HOST-RESOURCES-MIB::hrMemorySize',
                arithmetic='%', arith_symbol='UCD-SNMP-MIB::memTotalReal', arith_pos=2)
    print(snmp.read_oid_dc(r_oid))

    # read OID table
    t_oid = OID(table='hrStorageUsed', table_index='hrStorageIndex', related_symbol='hrStorageDesc',
                read_ref_from='hrStorageIndex',
                arithmetic='%', arith_symbol='hrStorageSize', arith_pos=2)
    print(snmp.read_oid_dc(t_oid))
