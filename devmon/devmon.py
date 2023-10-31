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
import datetime
import time
from yaml import safe_load
import os
import sys
from typing import Literal
from dataclasses import asdict
# from random import choices
# from string import ascii_letters, digits
from threading import Thread
from time import perf_counter
from inspect import currentframe
from pymongo import errors, timeout
from src import oid_to_case, ReadAgents, SNMP, ColorLogger, PushMsg, MongoDB, CMDB, ContextSNMP, HidePass
from src import OID, VOID, SNMPAgent, Case, TheSameCasePart, CaseUpdatePart, EventType
from src import Point, PointMeta, MongoTS, oid_to_point, InfluxDB


_ROOT_ = os.path.abspath(os.path.dirname(__file__))
_ROOT_ = '/etc/devmon' if _ROOT_.startswith('/tmp') else _ROOT_
_CONF_ = os.path.abspath(os.path.join(_ROOT_, 'conf/devmon.yaml'))
_LOG_ = os.path.abspath(os.path.join(_ROOT_, 'log/devmon.log'))

# _SRC_ = os.path.abspath(os.path.join(_ROOT_, 'src'))
# _CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
# _TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))

# sys.path.append(_SRC_)
# from core import ReadAgents, SNMP, ColorLogger, PushMsg, MongoDB, CMDB, ContextSNMP
# from type import OID, VOID, SNMPAgent, Case, TheSameCasePart, CaseUpdatePart


Side = Literal[
    'a', 'b'
]

# EventType = Literal[
#     'alert', 'recovery', 'message'
# ]

notify_start = notify_end = None


# def read_config(file: str = _CONF_):
#     try:
#         with open(file, 'r+') as f:
#             config = safe_load(f)
#     except FileNotFoundError as err:
#         raise err
#
#     return config


class DevMon(object):
    def __init__(self):
        self.a_side_snmps = None
        self.b_side_snmps = None
        self.clog = None
        self.pushmsg = None
        self.mongo = None
        self.event_keys = None
        self.event_delimiter = None
        self.multithread = None
        self.interval = None
        self.snmpwalk = None
        self.source = None
        # self.snmp_agents = []
        # self.snmp_cases = []
        self.patrol = None
        self.notify_window = None
        self.cmdb_server = self.cmdb_user = self.cmdb_pass = self.cmdb_db = None

    def _load_agents(self):
        try:
            A_SIDE_SNMPs, B_SIDE_SNMPs, A_SIDE_SSHs, B_SIDE_SSHs, MAINTAIN_DEVS = ReadAgents()
        except TypeError as err:  # todo move config file definition in this file.
            raise err

        # define class attributes for SNMP agents from both a and b sides
        self.a_side_snmps = A_SIDE_SNMPs
        self.b_side_snmps = B_SIDE_SNMPs

    def _load_config(self, pm: bool = False):
        # read configuration from file 'ROOT/conf/devmon.yaml'
        # config = read_config()
        try:
            with open(_CONF_, 'r+') as f:
                config = safe_load(f)
        except FileNotFoundError as err:
            raise err

        # read logger configuration
        name = f'devmon'
        try:
            log_level = config['log_level']
        except KeyError:
            log_level = 'WARNING'
        try:
            log_display = config['log_display']
        except KeyError:
            log_display = False

        self.clog = ColorLogger(name=name, filename=_LOG_, level=log_level, display=log_display)
        self._debug(f'Loading configuration finished.\n'
                    f'Logger name {name}, file {_LOG_}, level {log_level}, display {log_display}.')

        try:
            rlog_server = config['rlog_server']
            rlog_port = config['rlog_port']
            # nc = config['nc']
        except KeyError:
            raise f'rsyslog server/port configuration error.'

        # self.pushmsg = PushMsg(server=rlog_server, nc_path=nc, port=rlog_port)
        self.pushmsg = PushMsg(server=rlog_server, port=rlog_port)
        self._debug(f'Read rsyslog server {rlog_server} port {rlog_port}.')

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

        try:
            cmdb_col = config['cmdb_mongo_col']
        except KeyError:
            cmdb_col = 'cmdb'

        try:
            ts_db = config['mongo_ts_db']
            ts_col = config['mongo_ts_col']
        except KeyError:
            ts_db = 'perfmon'
            ts_col = 'test'  # todo should the different metadata be stored at the different collection or all-in-one???

        self.mongo = MongoDB(server=mongo_server, uri=mongo_uri,
                             username=mongo_user, password=mongo_pass, port=mongo_port,
                             database=mongo_db, collection=mongo_col)

        self.cmdb_mongo = MongoDB(server=mongo_server, uri=mongo_uri,
                                  username=mongo_user, password=mongo_pass, port=mongo_port,
                                  database=mongo_db, collection=cmdb_col)

        self.mongots = MongoDB(server=mongo_server, uri=mongo_uri,
                                  username=mongo_user, password=mongo_pass, port=mongo_port,
                                  database=ts_db, collection=ts_col)
        if not pm:
            try:
                with timeout(2):
                    self.mongo.client.admin.command('ping')
            except errors.ServerSelectionTimeoutError:
                print('MongoDB connection timeout after 2 seconds.')
                exit(1)
            self._debug(f'Initiated MongoDB client finished.\n'
                        f'Mongo Server {mongo_server}, uri {mongo_uri}, '
                        f'user {mongo_user}, port {mongo_port}, db {mongo_db}, collection {mongo_col}')

        try:
            self.event_keys = config['event_key']
            self.event_delimiter = config['event_delimiter']
        except KeyError:
            self.event_keys = ['sources', 'severity', 'situation_desc',
                               'content', 'type', 'threshold',
                               'current_value', 'rid', 'addr_in_cmdb']
            self.event_delimiter = '||'
        self._debug(f'Read event keys {self.event_keys}, delimiter {self.event_delimiter}.')

        try:
            self.multithread = config['multithread']
        except KeyError:
            self.multithread = False

        try:
            self.interval = config['interval']
        except KeyError:
            self.interval = 300

        try:
            self.snmpwalk = config['snmpwalk']
        except KeyError:
            self.snmpwalk = '/usr/bin/snmpwalk'

        try:
            self.source = config['source']
        except KeyError:
            self.source = 'SNMP Console'

        try:
            self.patrol = config['patrol']
        except KeyError:
            self.patrol = 5

        try:
            self.notify_window = config['notify_window']
        except KeyError:
            self.notify_window = '8:00-18:00'

        try:
            self.cmdb_server = config['cmdb_server']
            self.cmdb_user = config['cmdb_user']
            self.cmdb_db = config['cmdb_db']
            self.cmdb_pass = config['cmdb_pass']
        except KeyError:
            pass

    def refresh_config(self, pm: bool = False):
        self._load_agents()
        self._load_config(pm=pm)

    def _debug(self, msg: str = None):
        f_info = currentframe()
        lineno = f_info.f_back.f_lineno
        msg = f'[line: {lineno:3d}] {msg}'
        return self.clog.colorlog(msg, 'debug')

    def _info(self, msg: str = None):
        f_info = currentframe()
        lineno = f_info.f_back.f_lineno
        msg = f'[line: {lineno:3d}] {msg}'
        return self.clog.colorlog(msg, 'info')

    def _warn(self, msg: str = None):
        f_info = currentframe()
        lineno = f_info.f_back.f_lineno
        msg = f'[line: {lineno:3d}] {msg}'
        return self.clog.colorlog(msg, 'warn')

    def _error(self, msg: str = None):
        f_info = currentframe()
        lineno = f_info.f_back.f_lineno
        msg = f'[line: {lineno:3d}] {msg}'
        return self.clog.colorlog(msg, 'error')

    def _critical(self, msg: str = None):
        f_info = currentframe()
        lineno = f_info.f_back.f_lineno
        msg = f'[line: {lineno:3d}] {msg}'
        return self.clog.colorlog(msg, 'critical')

    def _notify(self):
        pass

    def oid_to_case(self, snmp_agent: SNMPAgent = None,
                     oid: OID = None,
                     alert: bool = None,
                     threshold: str = None,
                     void: VOID = None) -> Case:
        rid = snmp_agent.rid if snmp_agent.rid else self.find_rid(snmp_agent.addr_in_cmdb)
        rid = rid if rid else 'Null_Resource_ID'

        dbg = (f'Met snmp details waiting to be convert to case, agent: '
               f'[{snmp_agent}], oid: [{oid}], '
               f'alert [{alert}], threshold: [{threshold}],'
               f'void: [{void}], rid: [{rid}, source: [{self.source}')
        self._debug(f'{dbg}')
        return oid_to_case(snmp_agent=snmp_agent,
                           oid=oid,
                           alert=alert,
                           threshold=threshold,
                           void=void,
                           add_rid=rid,
                           source=self.source)

    # def ______oid_to_case(self, snmp_agent: SNMPAgent = None,
    #                 oid: OID = None,
    #                 alert: bool = False,
    #                 threshold: str = None,
    #                 # case_desc: str = None,
    #                 void: VOID = None) -> Case:
    #     """
    #     Creating Case() object which based on SNMPAgent, OID and other information.
    #     # h = hashlib.shake_256(a.encode())
    #     # h.hexdigest(10)
    #     """
    #     if not void.value:
    #         self._warn(
    #             f'Met None value VOID [{void}], agent [{snmp_agent.address}], OID [id: {oid.id}, id range: {oid.id_range}]')
    #         return Case()
    #
    #     if void.desc and oid.label:
    #         obj = f'{oid.label}-{void.desc}'
    #     else:
    #         obj = f'{oid.label}'
    #
    #     def _trans_enum(_agent: SNMPAgent = None, _oid: OID = None, _entry: str = None, delimiter: str = ','):
    #         _lst_val = [v.strip() for v in _entry.split(delimiter)]
    #         _rtn_val = []
    #
    #         for _val in _lst_val:
    #             try:
    #                 _rtn_val.append(_oid.enum[_val])
    #             except (KeyError, TypeError):
    #                 try:
    #                     _rtn_val.append(_agent.enum[_val])
    #                 except (KeyError, TypeError):
    #                     pass
    #         return f'{delimiter}'.join(_rtn_val)
    #
    #     if oid.enum or snmp_agent.enum:  # 'enum' for single OID will rewrite the definition from SNMPAgent
    #         val = _trans_enum(snmp_agent, oid, void.value)
    #         thd = _trans_enum(snmp_agent, oid, threshold)
    #     else:
    #         val = void.value
    #         thd = threshold
    #
    #     threshold = thd
    #     void.value = val  # void of modifying the rest of the code
    #
    #     if void.desc:
    #         content = f'{void.desc}{oid.explanation}{oid.alert} 阈值{threshold}'
    #     else:
    #         content = f'{oid.explanation}{oid.alert} 阈值{threshold}'
    #
    #     current_val = f'当前值{void.value}'
    #
    #     rid = snmp_agent.rid if snmp_agent.rid else self.find_rid(snmp_agent.addr_in_cmdb)
    #     rid = rid if rid else 'Null_Resource_ID'
    #
    #     core = TheSameCasePart(rid=rid,
    #                            region=snmp_agent.region,
    #                            area=snmp_agent.area,
    #                            addr_in_cmdb=snmp_agent.addr_in_cmdb,
    #                            severity=oid.severity,
    #                            object=obj,
    #                            sources=self.source,
    #                            description=oid.explanation,
    #                            threshold=f'{threshold}',
    #                            index=void.index,
    #                            address=snmp_agent.address)
    #
    #     try:
    #         s_core = ''.join(asdict(core).values())
    #     except TypeError:
    #         s_core = ''
    #
    #     b_core = s_core.encode()
    #     h = hashlib.shake_128(b_core)
    #     cid = h.hexdigest(20)
    #
    #     attach = CaseUpdatePart(count=1, alert=alert, content=content, current_value=current_val)
    #
    #     case = Case(id=cid, oid=oid, void=void)
    #     for key, value in asdict(core).items():
    #         case.__setattr__(key, value)
    #
    #     for key, value in asdict(attach).items():
    #         case.__setattr__(key, value)
    #     return case

    def _insert_case(self, case: Case = None):
        # generate 20-digit-long string as the new case ID
        # case.id = ''.join(choices(ascii_letters + digits, k=20))

        # the 'core' part of the case exist in MongoDB
        case_mongo: Case = self.is_case_exist(case)

        # the method 'is_case_exist' return Case object
        # if the attribute 'count' of the returned case is equal to default value 0
        # the case 'c' not exists in MongoDB
        self._debug(f'Received case from method [is_case_exist] [{case_mongo}]')

        # if case_mongo.attach.count == 0:  # default case has 0 value for count
        if case_mongo.count == 0:  # default case has a zero value for key 'count'
            # case.count = 1
            case.count = 1
            self._debug(f'New case: [{case}] received, waiting for inserting.')

            if case.alert:  # the new case does not exist in MongoDB, and 'alert = True'
                case.type = '1'
                # case.attach.type = '1'
                self._debug(f'Case [{case}] alert is True, set case.attach.type to 1.')

            else:  # case not exist in MongoDB, and 'alert = False'
                case.type = '3'
                # case.attach.type = '3'
                self._debug(f'Case [{case}] alert is False, set case.attach.type to 3.')

            # new case received, insert it to MongoDB
            i_rtn = self.mongo.insert_dict(asdict(case), insert_even_exist=True)  # todo

            lvl = 'info' if i_rtn else 'error'
            self.clog.colorlog(f'Insert new case [{case.id}] [{i_rtn}]', lvl)

        else:  # the case already exists
            self._debug(f'The core part of case received already exist in MongoDB, '
                        f'case in Mongo: [{case_mongo}], new case: [{case}].')

            if case_mongo.alert:
                if case.alert:  # alert case exist and remain alert, count++
                    case.count += case_mongo.count
                    case.type = '1'
                    case.publish = 0  # set to 0, waiting for pushing alert to rsyslog server

                    self._debug(f'Alert case [{case_mongo.id}] recalled, set attach.type to 1, count++.')

                else:  # Alert case exists, but stat turns to normal. It's a recovery event.
                    case.type = '2'  # case is recovered
                    # case.attach.count = 1  # do not reset the count
                    case.publish = 1  # alert pushed, waiting for pushing recovery to rsyslog server

                    self._debug(f'Alert case [{case_mongo.id}] stat return to normal, '
                                f'set attach.type to 2, reset attach.count to 1.')

            else:  # normal case exists
                if case.alert:  # normal case exists and recalls as abnormal
                    case.count = 1  # abnormal case count reset
                    case.type = '1'  # alert case
                    case.publish = 0  # waiting for pushing alert

                    self._debug(f'Normal case [{case_mongo.id}] exit but recalled as abnormal, '
                                f'set attach.type to 1, reset attach.count to 1.')

                else:  # normal case exists and remains normal
                    case.type = '3'
                    case.count += 1  # normal case count++
                    case.publish = 0  # reset publishing stat to 0

                    self._debug(f'Normal case [{case_mongo.id}] exist, '
                                f'set attach.type to 3, reset attach.count to 1.')

            # only update the 'attach' part of the case
            u_rtn = self.update_case_attach(case_id=case_mongo.id, case=case)
            msg = f'Update exist case [{case_mongo.id}] [{u_rtn}]'
            errmsg = f'Update exist case [{case_mongo.id}] [{u_rtn}] [{case_mongo}] [{case}]'
            self._info(msg) if u_rtn else self._error(errmsg)

    def multi_insert_cases(self, cases: list[Case]):
        threads = [Thread(target=self._insert_case, args=(case,)) for case in cases]
        [t.start() for t in threads]
        [t.join() for t in threads]

    def insert_cases(self, cases: list[Case]):
        [self._insert_case(ca) for ca in cases]

    def _update_attach_value_by_id(self, case_id: str, update_key: str, to_value):
        flt = {'id': case_id}
        update = {update_key: to_value}
        return self.mongo.update_dict(flt, update)
        # return self.__update_value_by_id(case_id, update_key, to_value)

    def update_case_attach(self, case_id: str = None, case: Case = None):
        """
        Read the case created
        update to the case which has the same fields (depends on method is_case_exit()) in the MongoDB (id=case_id)
        """
        attach = CaseUpdatePart()
        for key, value in asdict(case).items():
            attach.__setattr__(key, value)

        flt = {'id': case_id}
        update = {key: value for key, value in asdict(attach).items()}
        return self.mongo.update_dict(flt, update=update)  # todo do not return True of False

        # rtn = 0
        # for key, value in case_update_part.items():
        #     rtn += 0 if self._update_attach_value_by_id(case_id, key, value) else 1
        #
        #     msg = f'Updating the case [{case_id}] attach [{key}] value [{value}] [{rtn}]'
        #     self._info(msg) if rtn else self._error(msg)

    def is_case_exist(self, case: Case = None) -> Case:
        """
        Checking MongoDB to figure out the case exist or not.
        The core part of the Case() identified the same case.
        """
        # flt = {'core': asdict(case.core)}  # todo update exist case failed; case exist and case need to be updated has the different 'core.object'
        # flt = {f'core.{key}': value for key, value in asdict(case.core).items()}
        flt = {'id': case.id}

        case_exist = Case()
        d_case = self.mongo.find_one(flt)

        try:
            for key, value in d_case.items():
                case_exist.__setattr__(key, value)
        except TypeError:
            pass
        except AttributeError:
            pass

        return case_exist

    def _read_snmp_agent(self, agent: SNMPAgent, perf: bool = False) -> list[tuple[SNMPAgent, OID, list[VOID]]]:
        # snmp = SNMP(agent, snmpwalk=self.snmpwalk)
        snmp = ContextSNMP(agent, snmpwalk=self.snmpwalk)
        agent_oid_voids = []

        # for oid in agent.OIDs:
        #     l_voids = snmp.read_oid_dc(oid)
        #     # self.snmp_agents.append((agent, oid, l_voids)) if l_voids else ''
        #     agent_oid_voids.append((agent, oid, l_voids)) if l_voids else ''

        def __read_oid(_oid: OID = None):
            if perf and not _oid.perf:
                return None
            _l_voids = snmp.read_oid_dc(_oid)
            agent_oid_voids.append((agent, _oid, _l_voids)) if _l_voids else ''

        threads = [Thread(target=__read_oid, args=(oid, )) for oid in agent.OIDs]
        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]

        return agent_oid_voids

    def create_snmp_cases(self, side: Side = None, multithread: bool = True, device: str = None) -> list[Case]:
        agents = None

        if side == 'a':
            agents = self.a_side_snmps

        elif side == 'b':
            agents = self.b_side_snmps

        elif device:
            for agt in self.a_side_snmps + self.b_side_snmps:
                if agt.address == device:
                    agents = [agt]
                    break

        if not agents:
            self._error(f'device [{device}] not found in the devlist, return None value case.')
            return [Case()]

        # self.snmp_agents = []
        # self.snmp_cases = []

        v_threads = []
        snmp_agents = []
        snmp_cases = []

        def read_agent(agent: SNMPAgent):
            snmp_agents.extend(self._read_snmp_agent(agent))
            # The method already returns a list, so snmp_agents should extend rather than append.
            # The snmp_agent is a list of tuple, not a list of list.

        def cre_cases(_agent: SNMPAgent, _oid: OID, _void: VOID):
            snmp_cases.append(self._cre_snmp_case(_agent, _oid, _void))

        if multithread:
            # r_threads = [Thread(target=self._read_snmp_agent, args=(agent, )) for agent in agents]
            r_threads = [Thread(target=read_agent, args=(agent,)) for agent in agents]
            _ = [t.start() for t in r_threads]
            _ = [t.join() for t in r_threads]

            # for agent, oid, l_voids in self.snmp_agents:
            for agent, oid, l_voids in snmp_agents:
                for void in l_voids:
                    # v_threads.append(Thread(target=self._cre_snmp_case, args=(agent, oid, void, )))
                    v_threads.append(Thread(target=cre_cases, args=(agent, oid, void,)))

                # v_threads = [Thread(target=self._cre_snmp_case, args=(agent, snmp, oid, void, exclude_index, )) for void in l_voids]
                # missing some void in l_voids .... # todo ?????

            _ = [t.start() for t in v_threads]
            _ = [t.join() for t in v_threads]

        else:
            for agent in agents:
                # self._read_snmp_agent(agent)
                read_agent(agent)  # result already appended

            # for agent, snmp, oid, l_voids, exclude_index in self.snmp_agents:
            for agent, oid, l_voids in snmp_agents:
                for void in l_voids:
                    # self._cre_snmp_case(agent, oid, void)
                    cre_cases(agent, oid, void)  # result already append

        # return self.snmp_cases
        return snmp_cases

    def _cre_snmp_case(self, agent: SNMPAgent,
                       # snmp: SNMP = None,
                       oid: OID = None,
                       void: VOID = None) -> Case:
        """
        A threading target for creating case, based on SNMP agent, OID, and value of OID.
        """
        self._debug(f'Read SNMP agent: [{agent.address}], OID: [{oid}], Value: [{void}]')

        index = void.index
        val = void.value
        related_val = void.desc
        reference = void.reference if void.reference else oid.reference

        alert: bool = False
        threshold = None
        self._debug(f'Reset [alert], [case_desc] & [threshold] to default value.')

        if not val:
            self._debug(f'Address [{agent.address} OID [{oid}] got a None value.')
            return Case()  # todo

        if oid.watermark:  # the value of OID has a watermark
            try:
                val = float(val)
            except TypeError:
                # oid.watermark is specified, but the value fetched is not countable.
                err = f"The OID has a watermark [{oid.watermark}], " \
                      f"but the value fetched [{val}] is not float-able." \
                      f"The OID is ignored."
                self._error(err)
                return Case()

            try:
                low = float(oid.watermark.low)
                high = float(oid.watermark.high)
            except TypeError:
                self._error(f'The watermark specified {oid.watermark} is not integrable.')
                return Case()

            threshold = f'{oid.watermark.low}-{oid.watermark.high}'

            if not oid.watermark.restricted:
                if val <= low or val > high:  # abnormal
                    alert = True

            else:  # oid.watermark.restricted is not specified or set to False
                if low <= val < high:  # abnormal
                    alert = True

            msg = f'Read OID: [id: {oid.id} or range: {oid.id_range}], index: [{index}], value: [{val}], watermark: [{oid.watermark}]'
            self._info(msg)

        # elif oid.reference or oid.read_ref_from:  # the value of OID has a reference
        elif reference:
            threshold = reference
            if not str(val) in str(threshold):  # abnormal  # todo waiting for been verified with multiple reference
                alert = True  # alert has a default value 'False'

            msg = f'Read OID: [id: {oid.id} or range: {oid.id_range}, index {index}, value: {val}, related symbol: {related_val}, threshold: {threshold}]'
            self._info(msg)

        case = self.oid_to_case(snmp_agent=agent,
                                oid=oid,
                                alert=alert,
                                void=void,
                                threshold=threshold)
        # self.snmp_cases.append(case)
        return case

    def read_ssh_by_side(self, side: Side = None):
        pass

    def filter_alerts_not_published(self) -> list[dict]:
        """
        Find out all dict(s) in MongoDB those 'type' equal to '1' and alert not pushed to rsyslog server
        """
        flt = {'type': '1', 'publish': 0}
        # flt = {'attach.type': '1', 'attach.publish': 0}
        return self.mongo.find_many(flt)

    def filter_alerts_all(self) -> list[dict]:
        """
        Fine out all 'dict'(s) in MongoDB those 'type' equal to '1' and alert not pushed to rsyslog server
        """
        flt = {'type': '1'}
        # flt = {'attach.type': '1'}
        return self.mongo.find_many(flt)

    def filter_alerts_published(self) -> list[dict]:
        """
        Find out all 'dict(s)' in MongoDB those 'type' equal to '1' and alert not pushed to rsyslog server
        """
        flt = {'type': '1', 'publish': 1}
        # flt = {'attach.type': '1', 'attach.publish': 1}
        return self.mongo.find_many(flt)

    def filter_failed_recovery(self) -> list[dict]:
        """
        find all 'dict(s)' in MongoDB those 'type' equal to '2', alert message pushed, recovery not pushed.
        """
        # flt = {'type': '2', 'recovery_published': False, 'alert_published': True}
        # 1. attach.publish equals 0 --> alert not pushed
        # 2. attach.publish equals 1 --> alert pushed, recovery not pushed
        # 3. attach.publish equals 2 --> recovery pushed
        # alert pushed, recovery not pushed, but case is closed due to type already set to 2
        # flt = {'attach.type': '2', 'attach.publish': 1}
        flt = {'type': '2', 'publish': 1}
        return self.mongo.find_many(flt)

    def create_event(self, case_in_mongo: dict) -> tuple[str, str]:
        # flt = {'type': {"$in": ['1', '2']}}
        l_event = []

        try:
            for key in self.event_keys:
                try:
                    l_event.append(case_in_mongo[key])
                except KeyError:
                    l_event.append('')
        except TypeError:  # case_in_mongo not exist or met wrong input
            pass

        event = f'{self.event_delimiter}'.join(l_event)

        return case_in_mongo['id'], event

    def create_events(self, cases_in_mongo: list[dict]) -> list[tuple]:
        events = []

        for case in cases_in_mongo:
            events.append(self.create_event(case))

        return events

    def _push_event(self, case_id, event: str = None, event_type: EventType = None) -> bool:
        """
        Push event to rsyslog server, then update case['publish'] in MongoDB
        """
        if self.pushmsg.push(event):
            if event_type == 'alert':
                self.clog.colorlog(f'Push event [{event}] to rsyslog server, update [publish] to value 1', 'info')
                return self._update_attach_value_by_id(case_id=case_id, update_key='publish', to_value=1)

            elif event_type == 'recovery':
                r1 = self._update_attach_value_by_id(case_id=case_id, update_key='publish', to_value=2)
                r2 = self._update_attach_value_by_id(case_id=case_id, update_key='type',
                                                     to_value='2')  # todo verify !!!
                return True if r1 and r2 else False

        else:
            self._critical(f'Push case [{case_id}], event [{event}], type [{event_type}] to rsyslog server failed.')

            return False

    def push_alert(self, case_id: str = None, event: str = None):
        return self._push_event(case_id=case_id, event=event, event_type='alert')

    def push_recovery(self, case_id: str = None, event: str = None):
        return self._push_event(case_id=case_id, event=event, event_type='recovery')

    def push_all_alerts(self):
        """
        push all exist alert cases (not published before) to rsyslog server
        """
        threads = [Thread(target=self.push_alert, args=(cid, event,)) for cid, event in
                   self.create_events(self.filter_alerts_not_published())]
        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]
        # return [self.push_alert(cid, event) for cid, event in self.create_events(self.filter_alerts_not_published())]

    def push_all_recoveries(self):
        """
        push all exist alert cases (not published before) to rsyslog server
        """
        threads = [Thread(target=self.push_recovery, args=(cid, event,)) for cid, event in
                   self.create_events(self.filter_failed_recovery())]
        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]

    def show_all_alerts(self):
        """
        show all exist alert cases (both published or not) to rsyslog server instead of push them
        """
        count = 0
        print('-' * 50, f'{"Alert Published Cases":^25s}', '-' * 50)

        def print_alert(_alerts: list[dict] = None):
            _count = 0
            for _alert in _alerts:
                _cid, _event = self.create_event(_alert)
                _count += 1

                # al_pub = alert['attach']['publish']
                _al_pub = _alert['publish']
                if _al_pub == 1:
                    _pub_stat = 'Alerted'
                elif _al_pub == 2:
                    _pub_stat = 'Recovered'
                else:
                    _pub_stat = 'Default'

                print(f'|{_count:2d}. Case: {_cid} Stat: {_pub_stat:9s} Event: {_event}')

        print_alert(self.filter_alerts_published())

        # # for alert in self.filter_alerts_all():
        # for alert in self.filter_alerts_published():
        #     cid, event = self.create_event(alert)
        #     count += 1
        #
        #     # al_pub = alert['attach']['publish']
        #     al_pub = alert['publish']
        #     if al_pub == 1:
        #         pub_stat = 'Alerted'
        #     elif al_pub == 2:
        #         pub_stat = 'Recovered'
        #     else:
        #         pub_stat = 'Default'
        #
        #     print(f'|{count:2d}. Case: {cid} Stat: {pub_stat:9s} Event: {event}')
        print('-' * 127)

        count = 0
        print('-' * 50, f'{"Alert not Published":^25s}', '-' * 50)
        print_alert(self.filter_alerts_not_published())
        # for alert in self.filter_alerts_not_published():
        #     cid, event = self.create_event(alert)
        #     count += 1
        #
        #     # al_pub = alert['attach']['publish']
        #     al_pub = alert['publish']
        #     if al_pub == 1:
        #         pub_stat = 'Alerted'
        #     elif al_pub == 2:
        #         pub_stat = 'Recovered'
        #     else:
        #         pub_stat = 'Default'
        #
        #     print(f'|{count:2d}. Case: {cid} Stat: {pub_stat:9s} Event: {event}')
        print('-' * 127)

        count = 0
        print('-' * 50, f'{"Cases Failed Recovery":^25s}', '-' * 50)
        for fr in self.filter_failed_recovery():
            cid, event = self.create_event(fr)
            count += 1

            # pub_stat = 'Alerted' if fr['attach']['publish'] == 1 else 'Default'
            pub_stat = 'Alerted' if fr['publish'] == 1 else 'Default'
            print(f'|{count:2d}. Case: {cid} Stat: {pub_stat:9s} Event: {event}')
        print('-' * 127)

    def close_case(self, case_id: str = None, content: str = None, current_value: str = None):
        """
        What case in 'close case' means:
        1. the type of case is 1
        2. already pushed alert event to rsyslog server

        which 'close' means:
        1. push a recovery message to rsyslog server
        2. set 'publish' to value 2
        """
        flt = {'id': case_id}
        # cases = self.mongo.find_dict(flt)
        # d_case = cases[0]
        d_case = self.mongo.find_one(flt)
        cid, event = self.create_event(d_case)

        # if d_case['attach']['type'] == '1' and d_case['attach']['publish'] == 1:
        if d_case['type'] == '1' and d_case['publish'] == 1:
            self._debug(f'Met case {d_case} whose type=1, publish=1')

            d_case['content'] = content
            d_case['current_value'] = current_value
            d_case['publish'] = 2
            d_case['current_value'] = current_value
            d_case['type'] = '2'

            cid, recovery = self.create_event(d_case)
            self._debug(f'Create recovery message [{recovery}]')

            r1 = self.push_recovery(cid, recovery)
            l1 = 'info' if r1 else 'error'
            self.clog.colorlog(f'Case [{cid}] push recovery to rsyslog server [{r1}]', l1)

            # case_core = TheSameCasePart()
            # case_attach = CaseUpdatePart()
            case = Case()

            for key, value in d_case.items():
                try:
                    case.__setattr__(key, value)
                except AttributeError:
                    pass
            # for key, value in d_case['core'].items():
            #     try:
            #         case_core.__setattr__(key, value)
            #     except AttributeError:
            #         pass
            #
            # for key, value in d_case['attach'].items():
            #     try:
            #         case_attach.__setattr__(key, value)
            #     except AttributeError:
            #         pass

            # case.core = case_core
            # case.attach = case_attach

            r2 = self.update_case_attach(cid, case)
            l2 = 'info' if r2 else 'error'
            self.clog.colorlog(f'Update case [{cid}] to mongoDB [{r2}]', l2)

            b_rtn = True if r1 and r2 else False

        # elif d_case['attach']['type'] == '2' and d_case['attach']['publish'] != 2:  # recovery not sent to rsyslog server
        elif d_case['type'] == '2' and d_case['publish'] != 2:  # recovery not sent to rsyslog server
            b_rtn = True if self.push_recovery(cid, event) else False

        else:
            b_rtn = True if self._update_attach_value_by_id(cid, 'type', '3') else False

        try:
            d_case = self.mongo.find_one({'id': case_id})

            # if d_case['attach']['publish'] == 0:
            #     pub_stat = 'Default'
            # elif d_case['attach']['publish'] == 1:
            #     pub_stat = 'Alerted'
            # elif d_case['attach']['publish'] == 2:
            #     pub_stat = 'Recovered'
            # else:
            #     pub_stat = 'Unknown'

            if d_case['publish'] == 0:
                pub_stat = 'Default'
            elif d_case['publish'] == 1:
                pub_stat = 'Alerted'
            elif d_case['publish'] == 2:
                pub_stat = 'Recovered'
            else:
                pub_stat = 'Unknown'

            cid, msg = self.create_event(d_case)

            print(f'Case: {d_case["id"]} Stat: {pub_stat} Event: {msg}')
        except IndexError:
            print(f'Fetching case {case_id} from MongoDB failed.')
            b_rtn = False

        return True if b_rtn else False

    def run(self, show: bool = True):

        multithread = self.multithread
        a2b_interval_in_sec = self.interval

        start = perf_counter()
        a_snmp_cases = self.create_snmp_cases('a', multithread)
        self._info(f'All A side snmp agents checked, spent {perf_counter() - start:.2f} seconds.')

        start = perf_counter()
        self.multi_insert_cases(a_snmp_cases) if multithread else self.insert_cases(a_snmp_cases)
        self._info(f'All A side snmp cases inserted to MongoDB, spent {perf_counter() - start:.2f} seconds.')

        time.sleep(a2b_interval_in_sec)

        start = perf_counter()
        b_snmp_cases = self.create_snmp_cases('b', multithread)
        self._info(f'All B side snmp agents checked, spent {perf_counter() - start:.2f} seconds.')

        start = perf_counter()
        self.insert_cases(b_snmp_cases)
        self._info(f'All B side snmp cases inserted to MongoDB, spent {perf_counter() - start:.2f} seconds.')

        if show:
            self.push_all_alerts()
            self.push_all_recoveries()
            self.show_all_alerts()

    def service_run(self):
        """
        Running the tool as a Linux service.
        Checking the status of failed device each 'interval' time.
        """
        try:
            patrol = float(self.patrol) * 60
        except TypeError:
            patrol = 300

        while True:
            self.run(show=False)
            time.sleep(patrol)

    def sync_rid(self):
        cmdb = CMDB(host=self.cmdb_server, user=self.cmdb_user, password=self.cmdb_pass, database=self.cmdb_db)
        mongo_data = cmdb.select_id()

        return self.cmdb_mongo.collection.insert_many(mongo_data)

    def find_rid(self, addr: str = None):
        flt = {'ip': addr}  # todo verifying 'ip_hostname' key
        return self.cmdb_mongo.find_one(flt)

    def perf(self):
        agents: list[SNMPAgent] = self.a_side_snmps + self.b_side_snmps
        points: list[Point] = []

        for agent in agents:
            for (_, oid, l_void) in self._read_snmp_agent(agent, perf=True):
                points.append(oid_to_point(agent, oid, l_void))

        mg = MongoTS(uri='mongodb+srv://zeur913:zeur0607@online.svytn1p.mongodb.net/', username='zeur913', password='zeur0607',
                     database='test', collection='test_0031')
        for p in points:
            if p.data:
                mg.coll.insert_one(asdict(p))
        print(datetime.datetime.utcnow())
        # mg.pd_all()

    def pm_snmp(self, device: str = None):
        """
        Preventive maintenance for SNMP agents
        :return:
        """
        self.refresh_config(pm=True)
        if device:
            cases = self.create_snmp_cases(device=device)
        else:
            cases = self.create_snmp_cases('a') + self.create_snmp_cases('b')

        all_stats = {}
        for c in cases:
            # if c.count == 0:
            #     continue
            if not c.void:
                continue

            if c.void.desc:
                obj = f'{c.void.desc}'
            else:
                obj = f'{c.oid.label}'

            if c.oid.watermark and c.oid.watermark.restricted:
                name = '限制区'
            else:
                name = '阈值区'

            if c.alert:
                err = f'标签{c.oid.label:30s}{c.current_value:20s}{name}{c.threshold:10s}设备{obj:20s}'
                faulty = 1
            else:
                err = ''
                faulty = 0

            label = c.oid.label

            try:
                all_stats[c.address][label]['alert'] += faulty
                all_stats[c.address][label]['errors'].append(err)
            except KeyError:
                try:
                    all_stats[c.address][label].update({'alert': faulty, 'errors': [err]})
                except KeyError:
                    try:
                        all_stats[c.address].update({label: {'alert': faulty, 'errors': [err]}})
                    except KeyError:
                        all_stats.update({c.address: {label: {'alert': faulty, 'errors': [err]}}})

        hosts = list(all_stats.keys())
        hosts.sort()
        for host in hosts:
            err = []
            print('=' * 97)
            print('-' * 40, f'{host:^15s}', '-' * 40)
            label_detail = all_stats[host]
            for exp in label_detail.keys():
                faulty = label_detail[exp]['alert']
                err.extend(label_detail[exp]['errors'])

                if faulty > 0:
                    print(f'{exp:.<90s} \033[0;31mFAILED\033[0m')
                else:
                    print(f'{exp:.<90s} \033[0;37mPASSED\033[0m')

            err = list(set(err))
            try:
                err.remove('')
            except ValueError:
                pass
            err.sort()
            print('\n'.join(err))

    def pm_ssh(self):
        pass


if __name__ == '__main__':
    USAGE = f"Usage: \n" \
            f"  {sys.argv[0]} [run | service]  # one-time run or as a service \n" \
            f"  {sys.argv[0]} pm [device] \n" \
            f"  {sys.argv[0]} query \n" \
            f"  {sys.argv[0]} perf  # run performance checking\n" \
            f"  {sys.argv[0]} sync  # syncing resources ID from CMDB to MongoDB \n" \
            f"  {sys.argv[0]} close <CASE(id)> <content(field 4)> <current value(field 7)>\n"

    devmon = DevMon()
    try:
        if sys.argv[1] in ['run', 'query', 'sync', 'close', 'service', 'perf']:
            devmon.refresh_config()

        if sys.argv[1] == 'run':
            devmon.run()  # add a sleep interval

        elif sys.argv[1] == 'pm':
            try:
                dev = sys.argv[2]
            except IndexError:
                dev = None
            devmon.pm_snmp(device=dev)

        elif sys.argv[1] == 'perf':
            devmon.perf()

        elif sys.argv[1] == 'query':
            devmon.show_all_alerts()

        elif sys.argv[1] == 'sync':
            devmon.sync_rid()

        elif sys.argv[1] == 'service':
            devmon.service_run()

        elif sys.argv[1] == 'close':
            _id = sys.argv[2]
            _content = sys.argv[3]
            _cur_val = sys.argv[4]
            # push a recovery message to syslog server
            devmon.close_case(case_id=_id, content=_content, current_value=_cur_val)

        else:
            print(USAGE)
    except IndexError:
        print(USAGE)
