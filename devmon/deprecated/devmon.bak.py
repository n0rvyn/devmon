#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-09-23 19:50
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: devmon.py
# Tools: PyCharm

"""
---Short description of this Python module---

"""
import os
import time

from yaml import safe_load
import os
import sys
from typing import Literal, Tuple
from dataclasses import asdict
from random import choices
from string import ascii_letters, digits
from threading import Thread
from time import perf_counter
from inspect import currentframe

_ROOT_ = os.path.abspath(os.path.dirname(__file__))
_SRC_ = os.path.abspath(os.path.join(_ROOT_, 'src'))
_CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
_TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))
_CONF_ = os.path.abspath(os.path.join(_ROOT_, 'conf/devmon.yaml'))
_LOG_ = os.path.abspath(os.path.join(_ROOT_, 'log/devmon.log'))

sys.path.append(_SRC_)
from core import ReadConfig, ReadAgents, SNMP, ColorLogger, PushMsg, MongoDB
from type import OID, WaterMark, IDRange, VOID, SNMPAgent, Case, CaseType, ROID


Side = Literal[
    'a', 'b'
]

EventType = Literal[
    'alert', 'recovery', 'message'
]

notify_start = notify_end = None


def readopts(file: str = _CONF_):
    try:
        with open(file, 'r+') as f:
            config = safe_load(f)
    except FileNotFoundError as err:
        raise err

    return config


class DevMon(object):
    def __init__(self):
        try:
            A_SIDE_SNMPs, B_SIDE_SNMPs, A_SIDE_SSHs, B_SIDE_SSHs, MAINTAIN_DEVS = ReadAgents()
        except TypeError as sign_value_err:
            raise sign_value_err

        self.a_side_snmps = A_SIDE_SNMPs
        self.b_side_snmps = B_SIDE_SNMPs

        config = readopts()
        try:
            log_level = config['log_level']
        except KeyError:
            log_level = 'WARNING'
        try:
            log_display = config['log_display']
        except KeyError:
            log_display = False

        self.f_info = currentframe()
        self.clog = ColorLogger(name=f'devmon', filename=_LOG_, level=log_level, display=log_display)

        try:
            rlog_server = config['rlog_server']
            rlog_port = config['rlog_port']
            nc = config['nc']
        except KeyError:
            raise f'rsyslog server/port configuration error.'

        self.pushmsg = PushMsg(nc_server=rlog_server, nc_path=nc, nc_port=rlog_port)

        try:
            mongo_uri = config['mongo_uri']
        except KeyError:
            mongo_uri = None
        try:
            mongo_server = config['mongo_server']
            mongo_user = config['mongo_user']
            mongo_pass = config['mongo_pass']
        except KeyError:
            mongo_user = mongo_pass = mongo_server = None
        try:
            mongo_port = config['mongo_port']
        except KeyError:
            mongo_port = '27017'
        try:
            mongo_db = config['mongo_db']
            mongo_col = config['mongo_col']
        except KeyError:
            mongo_db = mongo_col = 'devmon'

        self.mongo = MongoDB(server=mongo_server, uri=mongo_uri,
                             username=mongo_user, password=mongo_pass, port=mongo_port,
                             database=mongo_db, collection=mongo_col)

        try:
            self.multithread = config['multithread']
        except KeyError:
            self.multithread = False

        try:
            self.interval = config['interval']
        except KeyError:
            self.interval = 300

    def _debug(self, msg: str = None):
        lineno = self.f_info.f_back.f_lineno
        msg = f'line: {lineno}, {msg}'
        return self.clog.colorlog(msg, 'debug')

    def _info(self, msg: str = None):
        return self.clog.colorlog(msg, 'debug')

    def _warn(self, msg: str = None):
        return self.clog.colorlog(msg, 'debug')

    def _error(self, msg: str = None):
        return self.clog.colorlog(msg, 'debug')

    def _critical(self, msg: str = None):
        return self.clog.colorlog(msg, 'debug')

    def struc_oid_info_to_case(self, snmp_agent: SNMPAgent = None,
                               oid: OID = None,
                               alert: bool = False,
                               threshold: str = None,
                               case_desc: str = None,
                               void: VOID = None,
                               related_void: VOID = None) -> Case:
        """
        Creating Case() object based on SNMPAgent, OID and other information.
        """
        if not void:
            self._warn(f'Met None value void [{void}], return default Case [{Case()}]')
            return Case()

        if related_void.value and oid.label:
            ob = f'{oid.label} - {related_void.value}'
            desc = f'{oid.label} {related_void.value} {case_desc}'
        else:
            ob = f'{oid.explanation}'
            desc = f'{case_desc}'

        return Case(region=snmp_agent.region,
                    area=snmp_agent.area,
                    addr_in_cmdb=snmp_agent.addr_in_cmdb,
                    alert=alert,
                    count=1,
                    description=desc,  # todo
                    severity=oid.severity,  # field 2
                    content=desc,  # field 4
                    situation_desc=oid.explanation,  # field 3
                    object=ob,  # todo
                    threshold=threshold,  # field 6
                    current_value=void.value,  # field 7
                    oid=oid.id,
                    oid_range=oid.id_range,
                    related_symbol=oid.related_symbol,
                    void=void.value)

    """
            event = f'{case_in_mongo["sources"]}||' \
                f'{case_in_mongo["severity"]}||' \
                f'{case_in_mongo["situation_desc"]}||' \
                f'{case_in_mongo["content"]}||' \
                f'{case_in_mongo["type"]}||' \
                f'{case_in_mongo["threshold"]}||' \
                f'{case_in_mongo["current_value"]}||' \
                f'{case_in_mongo["rid"]}||' \
                f'{case_in_mongo["addr_in_cmdb"]}'
    """

    def _insert_case(self, case: Case = None):
        case.id = ''.join(choices(ascii_letters + digits, k=20))
        # case insert failed, case content empty or case already exist

        case_mongo: Case = self.is_case_exist(case)
        # the method 'is_case_exist' returns Case object
        # if the attribute 'count' of returned case is equal to default value 0
        # the case 'c' is not exist in MongoDB
        if case_mongo.count == 0:  # default case has 0 value for count
            self.clog.colorlog(f'Case {case.id} not exist in MongoDB, set count -> 1', 'info')
            self.clog.colorlog(f'New case: [{case}]', 'debug')
            case.count = 1
            if case.alert:  # new case not exist in MongoDB, and 'alert = True'
                case.type = '1'
                self.clog.colorlog(f'Set case [{case.id}] type -> 1', 'info')
            else:  # case not exist in MongoDB, and 'alert = False'
                case.type = '3'
                self.clog.colorlog(f'Set case [{case.id}] type -> 3', 'info')

            b_return = self.mongo.insert_dict(asdict(case), insert_even_exist=True)
            level = 'info' if b_return else 'error'
            self.clog.colorlog(f'Insert new case [{case.id}] [{b_return}]', level)

        else:  # case already exist
            self.clog.colorlog(f'Case [{case_mongo.id}] exist', 'info')
            self.clog.colorlog(f'New case: [{case}]', 'debug')
            self.clog.colorlog(f'Case in MongoDB: {case_mongo}', 'debug')

            if case_mongo.alert:
                if case.alert:  # alert case exist and remain alert
                    case.count += case_mongo.count  # count+1
                    case.type = '1'  # type remain '1' --> alert
                    case.publish = 0  # reset publish symbol  # todo verify
                    self.clog.colorlog(f'Alert case [{case_mongo.id}] in MongoDB recalled, '
                                       f'Set type->1, count++ {case.count}', 'warn')
                else:  # alert case exist, but turn to normal, it's a recovery event
                    case.type = '2'  # type '2' --> recovery
                    case.count = 1
                    self.clog.colorlog(f'Alert case [{case_mongo.id}] return normal, '
                                       f'set type -> 2, reset count->1', 'info')
            else:  # normal case exist
                if case.alert:  # normal case exist and recalled as abnormal
                    case.count = 1  # reset count to 1
                    case.type = '1'  # type remain '1' --> alert
                    case.publish = 0  # reset 'publish', waiting for push alert  # todo
                    self.clog.colorlog(f'Normal case [{case_mongo.id}] exist and recalled abnormal, '
                                       'set case type->1, reset count->1', 'warn')
                else:  # normal case exist and remain normal
                    case.type = 3
                    case.count = 1
                    self.clog.colorlog(f'Normal case [{case_mongo.id}] exist, '
                                       f'set type->3, reset count->1', 'info')

            # b_rtn = self.mongo.update_case(case_id=case_mongo.id, update_key='count', to_value=c.count)
            b_rtn = self.update_case(case_id=case_mongo.id, case=case)
            level = 'info' if b_rtn else 'error'
            self.clog.colorlog(f'Update exist case [{case_mongo.id}] [{b_rtn}]', level)

    def multi_insert_cases(self, cases: list[Case]):
        threads = [Thread(target=self._insert_case, args=(case, )) for case in cases]
        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]

    def insert_cases(self, cases: list[Case]):
        for ca in cases:
            self._insert_case(ca)

    def _update_value_by_id(self, case_id: str, update_key: str, to_value) -> bool:
        return self.mongo.update_value(lookup_key='id', lookup_value=case_id, update_key=update_key, to_value=to_value)

    def update_case(self, case_id: str = None, case: Case = None):
        """
        read the case created
        update to the case which has the same fields (depends on method is_case_exit()) in the MongoDB (id=case_id)
        """
        r1 = self._update_value_by_id(case_id=case_id, update_key='count', to_value=case.count)
        r2 = self._update_value_by_id(case_id=case_id, update_key='content', to_value=case.content)
        r3 = self._update_value_by_id(case_id=case_id, update_key='type', to_value=case.type)
        r4 = self._update_value_by_id(case_id=case_id, update_key='alert', to_value=case.alert)
        r5 = self._update_value_by_id(case_id=case_id, update_key='current_value', to_value=case.current_value)
        r6 = self._update_value_by_id(case_id=case_id, update_key='publish', to_value=case.publish)

        return True if r1 and r2 and r3 and r4 and r5 and r6 else False

    def is_case_exist(self, case: Case = None) -> Case:
        """
        lookup MongoDB to make sure the case exist or not.

        rid=None
        region=None
        area=None
        addr_in_cmdb=None
        sources='SNMP脚本监控平台'
        severity='1'
        # description='up(1)当前值等于参考值up(1)'
        # content=''
        situation_desc='if status'
        object='Interface Status'
        threshold='up(1)'

        The same case must have the same fields showed above.
        """
        # 'description': case.description, 'situation_desc': case.situation_desc,
        flt = {'rid': case.rid, 'region': case.region, 'area': case.area,
               'addr_in_cmdb': case.addr_in_cmdb, 'sources': case.sources, 'severity': case.severity,
               'situation_desc': case.situation_desc,
               'object': case.object, 'threshold': case.threshold}

        case_exist = Case()
        try:
            l_case = self.mongo.find_dict(flt)
            d_case = l_case[0]
        except IndexError:
            d_case = {}
        try:
            for key, value in d_case.items():
                case_exist.__setattr__(key, value)
        except TypeError:
            pass

        return case_exist

    def create_snmp_case_by_side(self, side: Side = None) -> list[Case]:
        """
        AttributeError: 'FetchSNMPStatus' object has no attribute 'a_side'
        :param side:
        :return:
        """
        cases = []
        if side == 'a':
            agents = self.a_side_snmps
        elif side == 'b':
            agents = self.b_side_snmps
        else:
            return [Case()]

        for agt in agents:
            title = f'{"-" * 40}{agt.address}{"-" * 40}'
            self.clog.colorlog(title, 'info')
            snmp_agent = SNMPAgent(address=agt.address,
                                   region=agt.region,
                                   area=agt.area,
                                   addr_in_cmdb=agt.addr_in_cmdb,
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
                l_vals = snmp.read(oid=oid_start, oid_end=oid_end, count=count)

                exclude_index = oid.exclude_index.split(',') if oid.exclude_index else []
                exclude_index = [i.strip() for i in exclude_index]

                # for index, val in l_vals:  # loop for each OID
                for void in l_vals:  # loop for each OID
                    index = void.index
                    val = void.value

                    if not index or str(index) in exclude_index:
                        continue

                    related_val = snmp.read_by_index_ad_symbol(index=index, symbol=oid.related_symbol)

                    if oid.arith_symbol and oid.arithmetic:
                        void = snmp.read_arith_symbol(index=index, symbol=oid.arith_symbol,
                                                       ori_value=val, arith=oid.arithmetic,
                                                       position=oid.arith_pos)
                        val = void.value

                    self.clog.colorlog(f'SNMP agent: [{snmp_agent}]', 'debug')
                    self.clog.colorlog(f'OID: [{oid}]', 'debug')
                    self.clog.colorlog(f'VOID: [{void}]', 'debug')

                    alert: bool = False
                    case_desc = threshold = None
                    if oid.watermark:  # the value of OID has a watermark
                        try:
                            val = int(val)
                        except TypeError:
                            # oid.watermark is specified, but the value fetched is not countable.
                            msg = f"The OID has a watermark {oid.watermark}, " \
                                  f"but the value fetched {val} is not integrable." \
                                  f"The OID is ignored."
                            self.clog.colorlog(msg, 'warn')
                            continue

                        try:
                            low = int(oid.watermark.low)
                            high = int(oid.watermark.high)
                        except TypeError:
                            err = f'The watermark {oid.watermark} is not integrable.'
                            self.clog.colorlog(err, 'error')
                            continue

                        threshold = f'{oid.watermark.low}-{oid.watermark.high}'
                        if low < val < high:  # normal
                            msg = f'id: {oid.id} id_range: {oid.id_range} value: {val} is normal.'
                            self.clog.colorlog(msg, 'info')
                            case_desc = f'当前值[{void.value}]在参考范围[{oid.watermark.low}-{oid.watermark.high}]内'
                        else:  # abnormal
                            warn = f'id: {oid.id} id_range: {oid.id_range} ' \
                                   f'value: {val} is lower than {low} or high than {high}.'
                            self.clog.colorlog(warn, 'warn')
                            case_desc = f'当前值[{void.value}]超出参考范围[{oid.watermark.low}-{oid.watermark.high}]'
                            alert = True

                    elif oid.reference:  # the value of OID has a reference
                        threshold = f'{oid.reference}'
                        if val == oid.reference:  # normal
                            msg = f'id: {oid.id} id_range: {oid.id_range} value: {val} is normal.'
                            self.clog.colorlog(msg, 'info')
                            case_desc = f'当前值[{void.value}]等于参考值[{oid.reference}]'
                        else:  # abnormal
                            warn = f'id: {oid.id} id_range: {oid.id_range} value: {val} is abnormal.'
                            self.clog.colorlog(warn, 'warn')
                            case_desc = f'当前值[{void.value}]与参考值[{oid.reference}]不符'
                            alert = True

                    case = self.struc_oid_info_to_case(snmp_agent=snmp_agent,
                                                       oid=oid,
                                                       alert=alert,
                                                       case_desc=case_desc,
                                                       void=void,
                                                       threshold=threshold,
                                                       related_void=related_val)
                    cases.append(case)
        return cases

    def multi_create_snmp_case_by_side(self, side: Side = None) -> list[Case]:
        """
        AttributeError: 'FetchSNMPStatus' object has no attribute 'a_side'
        :param side:
        :return:
        """
        cases = []
        if side == 'a':
            agents = self.a_side_snmps
        elif side == 'b':
            agents = self.b_side_snmps
        else:
            return [Case()]

        # a threading target for reading SNMP agents' information
        def read_agents(agt: SNMPAgent = None):
            snmp_agent = SNMPAgent(address=agt.address,
                                   region=agt.region,
                                   area=agt.area,
                                   addr_in_cmdb=agt.addr_in_cmdb,
                                   community=agt.community,
                                   version=agt.version,
                                   username=agt.version,
                                   mib=agt.mib,
                                   retries=agt.retries,
                                   timeout=agt.timeout)
            snmp = SNMP(snmp_agent)
            for oid in agt.OIDs:
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
                l_vals = snmp.read(oid=oid_start, oid_end=oid_end, count=count)
                self._debug(f'Read OID values list [{l_vals}]')

                exclude_index = oid.exclude_index.split(',') if oid.exclude_index else []
                exclude_index = [i.strip() for i in exclude_index]
                self._debug(f'Read excluded index list [{exclude_index}]')

                def cre_case(void: VOID = None) -> Case:
                    """
                    a threading target for creating case, based on SNMP agent, OID, and value of OID.
                    """
                    self._debug(f'Read SNMP agent: [{agt}], OID: [{oid}], Value: [{void}]')

                    index = void.index
                    val = void.value

                    if not index or str(index) in exclude_index:
                        self._debug(f'Index [{index}] is not exist or not a string or excluded by config file.')
                        return Case()

                    related_val = snmp.read_by_index_ad_symbol(index=index, symbol=oid.related_symbol)
                    self._debug(f'Read related value [{related_val}]')

                    # for oid which has to arithmetic with another value  # todo
                    if oid.arith_symbol and oid.arithmetic:
                        void = snmp.read_arith_symbol(index=index, symbol=oid.arith_symbol,
                                                       ori_value=val, arith=oid.arithmetic,
                                                       position=oid.arith_pos)
                        val = void.value
                        self._debug(f'Met arithmetic OID value [{void}], set void to new value [{void}]')

                    alert: bool = False
                    case_desc = threshold = None
                    self._debug(f'Reset [alert], [case_desc] & [threshold] to default value.')
                    if oid.watermark:  # the value of OID has a watermark
                        try:
                            val = float(val)
                        except TypeError:
                            # oid.watermark is specified, but the value fetched is not countable.
                            err = f"The OID has a watermark {oid.watermark}, " \
                                  f"but the value fetched {val} is not float-able." \
                                  f"The OID is ignored."
                            self._error(err)
                            return Case()

                        try:
                            low = int(oid.watermark.low)
                            high = int(oid.watermark.high)
                        except TypeError:
                            err = f'The watermark specified {oid.watermark} is not integrable.'
                            self._error(err)
                            return Case()

                        threshold = f'{oid.watermark.low}-{oid.watermark.high}'

                        if not oid.watermark.restricted:
                            if low <= val < high:  # normal
                                msg = f'id: {oid.id} id_range: {oid.id_range} value: {val} is normal.'
                                self.clog.colorlog(msg, 'info')
                                case_desc = f'当前值[{void.value}]在参考范围[{oid.watermark.low}-{oid.watermark.high}]内'
                            else:  # abnormal
                                warn = f'id: {oid.id} id_range: {oid.id_range} ' \
                                       f'value: {val} is lower than {low} or high than {high}.'
                                self.clog.colorlog(warn, 'warn')
                                case_desc = f'当前值[{void.value}]超出参考范围[{oid.watermark.low}-{oid.watermark.high}]'
                                alert = True

                        else:
                            if val < low or val > high:  # normal
                                msg = f'id: {oid.id} id_range: {oid.id_range} value: {val} is normal.'
                                case_desc = f'当前值[{void.value}]不在限制参考范围[{oid.watermark.low}-{oid.watermark.high}]'
                                self.clog.colorlog(msg, 'info')
                            else:  # abnormal
                                warn = f'id: {oid.id} id_range: {oid.id_range} ' \
                                       f'value: {val} is lower than {low} or high than {high}.'
                                self.clog.colorlog(warn, 'warn')
                                case_desc = f'当前值[{void.value}]在限制参考范围[{oid.watermark.low}-{oid.watermark.high}]内'
                                alert = True

                    elif oid.reference or oid.read_ref_from:  # the value of OID has a reference
                        if oid.read_ref_from:
                            roid: ROID = snmp.read_ref_from_value(index, oid.read_ref_from)
                            self._debug(f'Met OID [index: {index}, value: {void.value}] reference '
                                        f'need to be read from another oid [{oid.read_ref_from}], '
                                        f'so threshold is set to value [{roid.reference}]')
                            reference = threshold = f'{roid.reference}'
                        else:
                            reference = threshold = f'{oid.reference}'

                        # if val == oid.reference:  # normal
                        if val == reference:  # normal
                            case_desc = f'当前值[{void.value}]等于参考值[{reference}]'

                        else:  # abnormal
                            case_desc = f'当前值[{void.value}]与参考值[{reference}]不符'
                            alert = True

                        msg = f'Read OID: [id: {oid.id}, range: {oid.id_range}, index {index}, value: {val}, related symbol: {related_val.value}, reference {reference}]'
                        self._info(msg)

                    case = self.struc_oid_info_to_case(snmp_agent=snmp_agent,
                                                       oid=oid,
                                                       alert=alert,
                                                       case_desc=case_desc,
                                                       void=void,
                                                       threshold=threshold,
                                                       related_void=related_val)
                    cases.append(case)

                threads = [Thread(target=cre_case, args=(v,)) for v in l_vals]
                # for index, val in l_vals:  # loop for each OID
                # for _void in l_vals:  # loop for each OID
                _ = [t.start() for t in threads]
                _ = [t.join() for t in threads]

        ag_threads = [Thread(target=read_agents, args=(agent, )) for agent in agents]
        # for agt in agents:
        _ = [t.start() for t in ag_threads]
        _ = [t.join() for t in ag_threads]

        return cases

    def read_ssh_by_side(self, side: Side = None):
        pass

    def filter_alerts_not_published(self) -> list[dict]:
        """
        find all 'dict'(s) in MongoDB those 'type' equal to '1' and alert not pushed to rsyslog server
        """
        flt = {'type': '1', 'publish': 0}
        return self.mongo.find_dict(flt)

    def filter_alerts_all(self) -> list[dict]:
        """
        find all 'dict'(s) in MongoDB those 'type' equal to '1' and alert not pushed to rsyslog server
        """
        flt = {'type': '1'}
        return self.mongo.find_dict(flt)

    def filter_failed_recovery(self) -> list[dict]:
        """
        find all 'dict'(s) in MongoDB those 'type' equal to '2', alert message pushed, recovery not pushed.
        """
        # flt = {'type': '2', 'recovery_published': False, 'alert_published': True}
        flt = {'type': '2', 'publish': 1}  # alert published, recovery not published
        return self.mongo.find_dict(flt)

    def create_event(self, case_in_mongo: dict) -> tuple[str, str]:

        # todo create Event object
        event = f'{case_in_mongo["sources"]}||' \
                f'{case_in_mongo["severity"]}||' \
                f'{case_in_mongo["situation_desc"]}||' \
                f'{case_in_mongo["content"]}||' \
                f'{case_in_mongo["type"]}||' \
                f'{case_in_mongo["threshold"]}||' \
                f'{case_in_mongo["current_value"]}||' \
                f'{case_in_mongo["rid"]}||' \
                f'{case_in_mongo["addr_in_cmdb"]}'

        e_debug = f'Severity: {case_in_mongo["severity"]}||' \
                f'Situation Description: {case_in_mongo["situation_desc"]}||' \
                f'Content: {case_in_mongo["content"]}||' \
                f'Type: {case_in_mongo["type"]}||' \
                f'Threshold: {case_in_mongo["threshold"]}||' \
                f'Current Value: {case_in_mongo["current_value"]}||' \
                f'Resource ID: {case_in_mongo["rid"]}||' \
                f'Address in CMDB: {case_in_mongo["addr_in_cmdb"]}'
        self._debug(e_debug)

        return case_in_mongo['id'], event

    def create_events(self, cases_in_mongo: list[dict]) -> list[tuple]:
        # flt = {'type': {"$in": ['1', '2']}}
        events = []

        for case in cases_in_mongo:
            events.append(self.create_event(case))

        return events

    def _push_event(self, case_id, event: str = None, event_type: EventType = None) -> bool:
        """
        push event to rsyslog server, then update case['publish'] in MongoDB
        """
        if self.pushmsg.push(event):
            if event_type == 'alert':
                self.clog.colorlog(f'Push event [{event}] to rsyslog server, update [publish] to value 1', 'info')
                # return self._update_case(case_id=case_id, update_key='alert_published', to_value=True)
                return self._update_value_by_id(case_id=case_id, update_key='publish', to_value=1)
            elif event_type == 'recovery':
                # return self._update_case(case_id=case_id, update_key='recovery_published', to_value=True)
                return self._update_value_by_id(case_id=case_id, update_key='publish', to_value=2)
        else:
            self.clog.colorlog(f'Push case [{case_id}] '
                               f'event [{event}] '
                               f'type [{event_type}] to rsyslog server failed', 'critical')
            return False

    def push_alert(self, case_id: str = None, event: str = None):
        return self._push_event(case_id=case_id, event=event, event_type='alert')

    def push_recovery(self, case_id: str = None, event: str = None):
        return self._push_event(case_id=case_id, event=event, event_type='recovery')

    def push_all_alerts(self):
        """
        push all exist alert cases (not published before) to rsyslog server
        """
        threads = [Thread(target=self.push_alert, args=(cid, event, )) for cid, event in self.create_events(self.filter_alerts_not_published())]
        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]
        # return [self.push_alert(cid, event) for cid, event in self.create_events(self.filter_alerts_not_published())]

    def show_all_alerts(self):
        """
        show all exist alert cases (both published or not) to rsyslog server instead of push them
        """
        count = 0
        print('-' * 50, f'{"Alert Cases":12s}', '-' * 50)
        for alert in self.filter_alerts_all():
            cid, event = self.create_event(alert)
            count += 1

            al_pub = alert['publish']
            if al_pub == 1:
                pub_stat = 'Alerted'
            elif al_pub == 2:
                pub_stat = 'Recovered'
            else:
                pub_stat = 'Default'

            print(f'{count:2d}. Case: {cid} Stat: {pub_stat:9s} Event: {event}')

        count = 0
        print('-' * 50, f'{"Cases Failed Recovery":21s}', '-' * 50)
        for fr in self.filter_failed_recovery():
            cid, event = self.create_event(fr)
            count += 1

            pub_stat = 'Alerted' if fr['publish'] == 1 else 'Default'
            print(f'{count:2d}. Case: {cid} Stat: {pub_stat:9s} Event: {event}')

    def close_case(self, case_id: str = None, content: str = None, current_value: str = None):
        """
        What case in 'close case' means:
        1. the type of case is 1
        2. already pushed alert event to rsyslog server

        which 'close' means:
        1. push recovery message to rsyslog server
        2. set 'publish' to value 2
        """
        flt = {'id': case_id}
        cases = self.mongo.find_dict(flt)

        if len(cases) != 1:
            return False

        case = cases[0]
        cid, event = self.create_event(case)

        if case['type'] == '1' and case['publish'] == 1:
            self.clog.colorlog('Met case whose type=1, publish=1', 'info')
            l_event = event.split('||')
            l_event[3] = content
            l_event[6] = current_value

            recovery = '||'.join(l_event)
            self.clog.colorlog(f'Create recovery message [{recovery}]', 'info')

            r1 = self.push_recovery(cid, recovery)
            l1 = 'info' if r1 else 'error'
            self.clog.colorlog(f'Push recovery to rsyslog server [{r1}]', l1)

            case['publish'] = 2
            case['current_value'] = current_value
            case['content'] = content
            case['type'] = '3'

            o_case = Case()
            for key, value in case.items():
                try:
                    o_case.__setattr__(key, value)
                except AttributeError:
                    pass

            r2 = self.update_case(cid, o_case)
            l2 = 'info' if r2 else 'error'
            self.clog.colorlog(f'Update case [{cid}] to mongoDB [{r2}]', l2)

            return True if r1 and r2 else False
        elif case['type'] == '2' and case['publish'] != 2:  # recovery not sent to rsyslog server
            return self.push_recovery(cid, event)
        else:
            return self._update_value_by_id(cid, 'type', '3')

    def show_case(self, case_id: str = None):
        try:
            case = self.mongo.find_dict({'id': case_id})[0]
            if case['publish'] == 0:
                pub_stat = 'Default'
            elif case['publish'] == 1:
                pub_stat = 'Alerted'
            elif case['publish'] == 2:
                pub_stat = 'Recovered'
            else:
                pub_stat = 'Unknown'

            print(f'Case: {case["id"]} Stat: {pub_stat}')
            return True
        except IndexError:
            print(f'Fetching case {case_id} from MongoDB failed.')
            return False

    def run(self):
        multithread = self.multithread
        a2b_interval_in_sec = self.interval

        start = perf_counter()
        a_snmp_cases = self.multi_create_snmp_case_by_side('a') if multithread else self.create_snmp_case_by_side('a')
        self.clog.colorlog(f'All A side snmp agents checked, '
                           f'spent {perf_counter() - start:.2f} seconds.', 'info')

        start = perf_counter()
        self.multi_insert_cases(a_snmp_cases) if multithread else self.insert_cases(a_snmp_cases)
        self.clog.colorlog(f'All A side snmp cases inserted to MongoDB, '
                           f'spent {perf_counter() - start:.2f} seconds.', 'info')

        # self.show_all_alerts()
        # self.push_all_alerts()
        time.sleep(a2b_interval_in_sec)

        start = perf_counter()
        b_snmp_cases = self.multi_create_snmp_case_by_side('b')
        self.clog.colorlog(f'All B side snmp agents checked, '
                           f'spent {perf_counter() - start:.2f} seconds.', 'info')

        start = perf_counter()
        self.insert_cases(b_snmp_cases)
        self.clog.colorlog(f'All B side snmp cases inserted to MongoDB, '
                           f'spent {perf_counter() - start:.2f} seconds.', 'info')

        self.push_all_alerts()
        self.show_all_alerts()

    def service(self):
        """
        for running the tool as a Linux service

        check the status of failed device each 'interval' time
        """
        pass


if __name__ == '__main__':
    USAGE = f"Usage: \n" \
            f"  {sys.argv[0]} run \n" \
            f"  {sys.argv[0]} query \n" \
            f"  {sys.argv[0]} close <CASE(id)> <content> <current value>\n"

    devmon = DevMon()
    try:
        if sys.argv[1] == 'run':
            devmon.run()  # add sleep interval

        elif sys.argv[1] == 'query':
            devmon.show_all_alerts()

        elif sys.argv[1] == 'close':
            _id = sys.argv[2]
            _content = sys.argv[3]
            _cur_val = sys.argv[4]
            # push recovery message to syslog server
            devmon.close_case(case_id=_id, content=_content, current_value=_cur_val)
            devmon.show_case(_id)

    except IndexError:
        print(USAGE)
