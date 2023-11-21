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
from type import PointMeta, Point, Entry, EntryValue, Agent, SNMPDetail, SSHDetail
from datetime import datetime
import pytz


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
