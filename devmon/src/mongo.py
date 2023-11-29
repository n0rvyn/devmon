#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-04-29 20:12
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: mongo.py
# Tools: PyCharm

"""
---Operating MongoDB with 'pymongo'---

"""
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import errors
from threading import Thread
from datetime import datetime
from dataclasses import asdict
import pytz
from .point import Point, PointMeta
from .entry import Entry, EntryValue
from .agent import Agent, SNMPDetail, SSHDetail
from .case import Case, CaseUpdatePart, TheSameCasePart


class MongoDB(object):
    def __init__(self,
                 server: str = None, port: int = 27017,
                 username: str = None, password: str = None,
                 uri: str = None,
                 server_api=ServerApi('1'),
                 database: str = None,
                 collection: str = None,
                 timeseries: bool = False):

        if not (database and collection):
            raise 'Both Database & Collection must be specified!'

        host = uri if uri else server
        # if uri:
        #     self.client = MongoClient(uri, server_api=server_api)
        # else:
        self.client = MongoClient(host=host,
                                  port=port,
                                  username=username,
                                  password=password,
                                  server_api=server_api)

        db = self.client[database]

        if timeseries:
            try:
                db.create_collection(collection, timeseries={'timeField': 'timestamp',
                                                             'metaField': 'metadata',
                                                             'granularity': "seconds"})

                """
                db.runCommand({
                collMod: "weather24h",
                expireAfterSeconds: "off"})
                """
            except (errors.CollectionInvalid, errors.OperationFailure):
                pass  # the collection already exists.

        self.collection = db[collection]

    def insert_dict(self, data: dict, insert_even_exist: bool = False) -> bool:
        """
        Insert a Dict to MongoDB
        """
        no_data_before = len(list(self.collection.find(data)))

        if not insert_even_exist and no_data_before:
            return False

        self.collection.insert_one(data)  # after inserted to MongoDB, data will be added a key '_id'

        try:
            data.pop('_id')
        except KeyError:
            pass

        no_data_after = len(list(self.collection.find(data)))
        return True if no_data_after > no_data_before else False

    def update_value(self,
                     lookup_key: str, lookup_value: any,
                     update_key: str, to_value: any,
                     fresh_m_time: bool = True,
                     update_all: bool = False) -> bool:
        flt = {lookup_key: lookup_value}
        up = {"$set": {update_key: to_value}, "$currentDate": {"lastModified": True if fresh_m_time else False}}
        vfy = {lookup_key: lookup_value, update_key: to_value}

        # return self.client[database][collection].find_one_and_update(_filter, _updater)
        self.collection.update_one(flt, up) if not update_all else self.collection.update_many(flt, up)

        return True if self.collection.find_one(vfy) else False

    def find_many(self, case_filter: dict) -> list[dict]:
        return list(self.collection.find(case_filter))

    def find_one(self, case_filter: dict) -> dict:
        return self.collection.find_one(case_filter)

    def update_dict(self, flt: dict = None, update: dict = None):
        update = {'$set': update}
        return self.collection.update_one(filter=flt, update=update)

    def insert_dicts(self, data: list[dict]):
        threads = [Thread(target=self.insert_dict, args=(d,)) for d in data]
        [t.start() for t in threads]
        [t.join() for t in threads]

    def find_case(self, case: Case = None) -> Case:
        """
        Checking MongoDB to figure out the case exist or not.
        The core part of the Case() identified the same case.
        """
        flt = {'id': case.id}

        case_in_mongo = Case()
        d_case = self.find_one(flt)

        try:
            for key, value in d_case.items():
                case_in_mongo.__setattr__(key, value)
        except (TypeError, AttributeError):
            pass

        return case_in_mongo

    def insert_case(self, case: Case = None):
        if not case.address:
            return False

        case_in_mongo: Case = self.find_case(case)

        # if case_in_mongo.attach.count == 0:  # default case has 0 value for count
        if case_in_mongo.count == 0:  # default case has a zero value for key 'count'
            case.count = 1

            if case.alert:  # the new case does not exist in MongoDB, and 'alert = True'
                case.type = '1'

            else:  # case not exist in MongoDB, and 'alert = False'
                case.type = '3'

            # new case received, insert it to MongoDB
            return self.insert_dict(asdict(case), insert_even_exist=True)

        else:  # the case already exists
            if case_in_mongo.alert:
                if case.alert:  # alert the case exists and which remain alert, count++
                    case.count += case_in_mongo.count
                    case.type = '1'
                    case.publish = 0  # set to 0, waiting for pushing alert to rsyslog server

                else:  # Alert case exists, but stat turns to normal. It's a recovery event.
                    case.type = '2'  # case is recovered
                    case.publish = 1  # alert pushed, waiting for pushing recovery to rsyslog server

            else:  # normal case exists
                if case.alert:  # normal case exists and recalls as abnormal
                    case.count = 1  # abnormal case count reset
                    case.type = '1'  # alert case
                    case.publish = 0  # waiting for pushing alert

                else:  # normal case exists and remains normal
                    case.type = '3'
                    case.count += 1  # normal case count++
                    case.publish = 0  # reset publishing stat to 0

            # only update the 'attach' part of the case
            return self.update_case_attach(case_id=case_in_mongo.id, case=case)

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
        return self.update_dict(flt, update=update)

    # def close_case(self, case_id: str = None, content: str = None, current_value: str = None):
    #     """
    #     Where case in 'close case' means:
    #     1. The type of case is 1
    #     2. Already pushed alert event to rsyslog server
    #
    #     Which 'close' means:
    #     1. Push a recovery message to rsyslog server
    #     2. Set 'publish' to value 2
    #     """
    #     flt = {'id': case_id}
    #     d_case = self.find_one(flt)
    #     cid, event = self.create_event(d_case)
    #
    #     # if d_case['attach']['type'] == '1' and d_case['attach']['publish'] == 1:
    #     if d_case['type'] == '1' and d_case['publish'] == 1:
    #         self._debug(f'Met case {d_case} whose type=1, publish=1')
    #
    #         d_case['content'] = content
    #         d_case['current_value'] = current_value
    #         d_case['publish'] = 2
    #         d_case['current_value'] = current_value
    #         d_case['type'] = '2'
    #
    #         cid, recovery = self.create_event(d_case)
    #         self._debug(f'Create recovery message [{recovery}]')
    #
    #         r1 = self.push_recovery(cid, recovery)
    #         l1 = 'info' if r1 else 'error'
    #         self.clog.colorlog(f'Case [{cid}] push recovery to rsyslog server [{r1}]', l1)
    #
    #         case = Case()
    #
    #         for key, value in d_case.items():
    #             try:
    #                 case.__setattr__(key, value)
    #             except AttributeError:
    #                 pass
    #
    #         r2 = self.update_case_attach(cid, case)
    #         l2 = 'info' if r2 else 'error'
    #         self.clog.colorlog(f'Update case [{cid}] to mongoDB [{r2}]', l2)
    #
    #         b_rtn = True if r1 and r2 else False
    #
    #     # elif d_case['attach']['type'] == '2' and d_case['attach']['publish'] != 2:  # recovery not sent to rsyslog server
    #     elif d_case['type'] == '2' and d_case['publish'] != 2:  # recovery not sent to rsyslog server
    #         b_rtn = True if self.push_recovery(cid, event) else False
    #
    #     else:
    #         b_rtn = True if self._update_attach_value_by_id(cid, 'type', '3') else False
    #
    #     try:
    #         d_case = self.mongo.find_one({'id': case_id})
    #
    #         if d_case['publish'] == 0:
    #             pub_stat = 'Default'
    #         elif d_case['publish'] == 1:
    #             pub_stat = 'Alerted'
    #         elif d_case['publish'] == 2:
    #             pub_stat = 'Recovered'
    #         else:
    #             pub_stat = 'Unknown'
    #
    #         cid, msg = self.create_event(d_case)
    #
    #         print(f'Case: {d_case["id"]} Stat: {pub_stat} Event: {msg}')
    #     except IndexError:
    #         print(f'Fetching case {case_id} from MongoDB failed.')
    #         b_rtn = False
    #
    #     return True if b_rtn else False


class MongoPoint(object):
    def __init__(self):
        pass

    @staticmethod
    def void_to_point(agent: Agent = None, entry: Entry = None, l_values: list[EntryValue] = None) -> Point:
        if not entry.perf:
            return Point()

        point_meta = PointMeta(agent.address, agent.region, agent.area, entry.label)
        data = {}

        for e_val in l_values:
            try:
                float(e_val.value)
            except (ValueError, TypeError):
                continue

            if e_val.desc:
                data.update({e_val.desc: float(e_val.value)})

            elif entry.label:
                data.update({entry.label: float(e_val.value)})

        now = datetime.now()
        local_now = pytz.timezone('Asia/Shanghai').localize(now)

        point = Point(metadata=point_meta,
                      timestamp=local_now,
                      data=data)

        return point


if __name__ == '__main__':
    URI = "mongodb://localhost:27017"
    m = MongoDB(uri=URI, database='devmon', collection='devmon')

    print(m.update_value('id',
                         'Pb6kI11BglKq7Tt6',
                         'attach.visible', False))
    m.update_dict({'id': 'DKmAQW3Ax7q1uf8W8'},
                  {'core.rid': 'rid', 'core.area': 'Sky', 'null': '11111'})
