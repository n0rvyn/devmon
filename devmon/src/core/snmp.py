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
import os
import subprocess
import sys
from subprocess import getstatusoutput
from typing import Literal, Optional
from threading import Thread

_FILE_ = os.path.abspath(__file__)
_SRC_ = os.path.abspath(os.path.join(_FILE_, '../../'))
_CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
_TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))

sys.path.append(_SRC_)

try:
    from type import SNMPAgent, OID, VOID, ArithType, IDRange
except ImportError as e:
    raise e

Position = Literal[
    1, 2
]

OUTOPTS = Literal[
    'a', 'b', 'e', 'E', 'f', 'F', 'n', 'p', 'q', 'Q', 's', 'S', 't', 'T', 'u', 'U', 'v', 'V', 'x', 'X'
]


# class OIDIsTableError(Exception):
#     print(f'OID is a table entry.')


class SNMP(object):
    def __init__(self, snmp_agent: SNMPAgent = None, snmpwalk: str = '/usr/bin/snmpwalk'):
        self.agent = snmp_agent
        self.snmpwalk = snmpwalk
        self.snmpd_stat = True

    def _read_oid(self, oid: str, outopts: OUTOPTS = 'U') -> Optional[str]:
        if not self.snmpd_stat or not oid:
            return None

        if self.agent.base:
            if not self.agent.base.endswith('.') and not oid.startswith('.'):
                oid = f'{self.agent.base}.{oid}'
            elif self.agent.base.endswith('.') and oid.startswith('.'):
                oid = f'{self.agent.base}.{oid}'
            else:
                oid = f'{self.agent.base}{oid}'

        ver = f'-v {self.agent.version}'
        retries = f'-r {self.agent.retries}'
        timeout = f'-t {self.agent.timeout}'
        comm = f"-c '{self.agent.community}'" if self.agent.version != '3' else ''
        user = f'-u {self.agent.username}'  # todo adding SanSwitch VF support
        mib = f'-m {self.agent.mib}' if self.agent.mib else ''
        cont = f'-n VF:{self.agent.context}' if self.agent.context else ''

        if '!' in comm:
            self.snmpwalk = f'set +H; {self.snmpwalk}'

        cmd = f"{self.snmpwalk} {ver} {comm} {mib} " \
              f"{user} {cont} " \
              f"{retries} {timeout} " \
              f"-O{outopts} " \
              f"{self.agent.address} {oid}"
        NO_VALUE_ERR = ['No Such Instance currently exists at this OID',
                        'No Such Object available on this agent at this OID']

        code, output = getstatusoutput(cmd)

        if output.startswith('Timeout'):  # once the snmpd is not reachable, set the parameter to False --> line: 49
            self.snmpd_stat = False  # the SNMPD server is not respond

        # value = output.split('=')[-1].strip()
        value = output.split('=')[-1].strip().strip('"')  # for some values been surrounded by `"
        # return output if code == 0 and value != NO_VALUE_ERR else None
        return output if code == 0 and value not in NO_VALUE_ERR else None

    def _read_oid_val(self, oid: str, outopts: OUTOPTS = 'v') -> Optional[str]:
        output = self._read_oid(oid, outopts)

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

    def ____read_related_symbol(self, index: str = None, symbol: str = None) -> Optional[str]:
        """
        UCD-SNMP-MIB::dskDevice.31 = STRING: /dev/mapper/rootvg-lv_portage

        lookup OID's symbol by 'UCD-SNMP-MIB::dskPercent.31 = INTEGER: 89'
        :return:
        """
        try:
            int(index)
            oid = f'{symbol}.{index}'
            return self._read_oid_val(oid)
        except ValueError:
            return None

    def ___read(self,
                oid: str = None,
                oid_end: str = None,
                count: int = None) -> list[VOID]:
        """
        Notice:
            'oid_from' ends with 'int' or not both are acceptable.
            'oid_to' MUST ends with 'int' to count the number of loop
            'oid_to' has high priority than 'count'
        """
        # type_ad_values = []
        voids = []

        if not oid_end and not count:  # oid specified can be single OID or table entry
            try:
                output_lines = self._read_oid(oid).split('\n')  # todo this is for reading a OID table
            except AttributeError:
                # return [(None, None)]
                return [VOID()]

            for ln in output_lines:
                void = VOID()  # reset the VOID dataclass
                try:
                    # type_val, val = l.split(':')
                    # HOST-RESOURCES-MIB::hrSWRunPerfMem.1199 = INTEGER: 8
                    oid, value = ln.split('=')
                    *_, val = value.split(':')
                    *_, index = oid.split('.')

                    void.index = index.strip()
                    void.value = val.strip().strip('"')  # for some values included `"
                except ValueError:
                    void.index = void.value = None
                voids.append(void)

            return voids

        index_to = None
        try:
            try:
                index_from = int(oid.split('.')[-1])
                oid_prefix = '.'.join(oid.split('.')[0:-1])
            except ValueError:
                index_from = 1
                oid_prefix = oid

            if oid_end:
                try:
                    index_to = int(oid_end.split('.')[-1]) + 1
                except ValueError:
                    raise 'OID format error!'

            elif count:
                index_to = index_from + count

            for i in range(index_from, index_to):
                # type_ad_values.append(self.read(f'{oid_prefix}.{str(i)}'))
                voids.extend(self.read(f'{oid_prefix}.{str(i)}'))  # call the function itself???

        except IndexError:
            pass

        return voids

    def _read_id(self,
                 oid: str = None,
                 related_symbol: str = None,
                 exclude_index: str = None,
                 read_ref_from: str = None,  # todo add support when symbol is ends with '.1'
                 arithmetic: ArithType = None,
                 arith_symbol: str = None,
                 arith_pos: Position = None) -> VOID:
        """
        Notice:
            'oid_from' ends with 'int' or not both are acceptable.
            'oid_to' MUST ends with 'int' to count the number of loop
            'oid_to' has high priority than 'count'
        """
        void = VOID()

        index = oid.split('.')[-1]
        try:
            int(index)
        except ValueError:
            index = '1'

        if exclude_index and str(index) in exclude_index:
            return void

        value = self._read_oid_val(oid)

        if related_symbol:
            desc = self._read_oid_val(f'{related_symbol}.{index}')
        else:
            desc = None

        if read_ref_from:
            ref = self._read_oid_val(f'{read_ref_from}.{index}')
        else:
            ref = None

        if arithmetic:
            value = self._read_arith_symbol(index, arith_symbol, arithmetic, value, arith_pos)
        else:
            pass

        void = VOID(index=index, value=value, desc=desc, reference=ref)

        return void

    def _read_id_range(self,
                       oid_start: str = None,
                       oid_end: str = None,
                       count: int = None,
                       related_symbol: str = None,
                       exclude_index: str = None,
                       read_ref_from: str = None,
                       arithmetic: ArithType = None,
                       arith_symbol: str = None,
                       arith_pos: Position = None) -> list[VOID]:

        voids = []

        def read_id_target(_oid: str = None,
                           _related_symbol: str = None,
                           _exclude_index: str = None,
                           _read_ref_from: str = None,
                           _arithmetic: ArithType = None,
                           _arith_symbol: str = None,
                           _arith_pos: Position = None):
            voids.append(
                self._read_id(_oid, _related_symbol, _exclude_index, _read_ref_from, _arithmetic, _arith_symbol,
                              _arith_pos))

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
                                  args=(oid, related_symbol, exclude_index, read_ref_from,
                                        arithmetic, arith_symbol, arith_pos,)))

        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]

        return voids

    def ____read_by_index_ad_symbol(self, index: str = None, symbol: str = None) -> VOID:
        """
        UCD-SNMP-MIB::dskDevice.31 = STRING: /dev/mapper/rootvg-lv_portage

        lookup OID's symbol by 'UCD-SNMP-MIB::dskPercent.31 = INTEGER: 89'
        :return:
        """
        try:
            int(index)
            oid = f'{symbol}.{index}'
            return self.read(oid=oid)[0]
        except ValueError:
            return VOID()

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

        except TypeError:
            return val

        return val

    def ____read_ref_from_value(self, index: str = None, symbol: str = None) -> str:
        """
        Read OID reference (if it has one) from another OID which has the same index
        """
        reference = None
        try:
            int(index)
            oid = f'{symbol}.{index}'
            reference = self._read_oid_val(oid)
        except ValueError:
            pass
        except AttributeError:
            pass

        return reference

    def _read_table_vals(self, table: str = None):
        output = self._read_oid(table, outopts='Q')
        l_oid_vals = output.split('\n') if output else []
        # l_oid_vals = self._read_oid(table, outopts='Q').split('\n')
        return [o_v.split('=')[-1].strip().strip('"') for o_v in l_oid_vals]  # add strip('"') for values `"value`"

    def _read_table(self,
                    table: str = None,
                    index_table: str = None,
                    related_symbol_table: str = None,
                    reference_symbol_table: str = None,
                    arith_symbol_table: str = None,
                    arith: ArithType = None,
                    arith_pos: int = 2) -> Optional[list[VOID]]:
        vals_table = self._read_table_vals(table)
        vals_related = self._read_table_vals(related_symbol_table)
        vals_arith = self._read_table_vals(arith_symbol_table)
        vals_index = self._read_table_vals(index_table)
        vals_ref = self._read_table_vals(reference_symbol_table)

        voids = []

        if not vals_table:
            return None
        else:
            for i in range(len(vals_table)):
                if vals_arith:
                    try:
                        ori_value = float(vals_table[i])
                        ari_value = float(vals_arith[i])
                    except TypeError:
                        continue
                    val = self._arith_value(arith=arith, ori_value=ori_value, ari_value=ari_value,
                                            position=arith_pos)
                else:
                    val = vals_table[i]

                if vals_index:
                    try:
                        index = vals_index[i]  # todo index out of range error!!!!!!
                    except IndexError:
                        index = None  # todo read index from OID.1
                else:
                    index = None

                if vals_related:
                    rel_val = vals_related[i]
                else:
                    rel_val = None

                if vals_ref:
                    ref = vals_ref[i]
                else:
                    ref = None

                voids.append(VOID(index=index, desc=rel_val, value=val, reference=ref))

        return voids

    def read_oid_dc(self, oid: OID = None) -> list[VOID]:
        voids = [VOID()]
        if oid.id:
            void = self._read_id(oid=oid.id, related_symbol=oid.related_symbol,
                                 exclude_index=oid.exclude_index,
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
                                        read_ref_from=oid.read_ref_from,
                                        arithmetic=oid.arithmetic,
                                        arith_symbol=oid.arith_symbol,
                                        arith_pos=oid.arith_pos
                                        )
            return voids

        if oid.table:
            voids = self._read_table(table=oid.table,
                                     index_table=oid.table_index,
                                     related_symbol_table=oid.related_symbol,
                                     arith_symbol_table=oid.arith_symbol,
                                     reference_symbol_table=oid.read_ref_from,
                                     arith=oid.arithmetic,
                                     arith_pos=oid.arith_pos)

        return voids


if __name__ == '__main__':
    agent = SNMPAgent(address='192.16.10.250', community='public')
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
