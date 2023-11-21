#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-04-29 20:12
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: mongots.py
# Tools: PyCharm

"""
---Operating MongoDB time series collection with 'pymongo'---

"""
import pandas
import pymongo.errors
import pymongoarrow
import pandas as pd
import pyarrow
import matplotlib.pyplot as plt
from pymongoarrow.monkey import patch_all
from pymongoarrow.api import write, Schema
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from type import Point

patch_all()


class MongoTS(object):
    def __init__(self, server: str = None,
                 port: int = 27017,
                 username: str = None,
                 password: str = None,
                 uri: str = None,
                 server_api=ServerApi('1'),
                 database: str = None,
                 collection: str = None):

        if not (database and collection):
            raise 'Both Database & Collection must be specified!'

        host = uri if uri else server

        client = MongoClient(host=host, port=port, server_api=server_api, username=username, password=password)
        db = client[database]

        try:
            db.create_collection(collection, timeseries={'timeField': 'timestamp',
                                                         'metaField': 'metadata',
                                                         'granularity': "seconds"})

            """
            db.runCommand({
            collMod: "weather24h",
            expireAfterSeconds: "off"})
            """
        except (pymongo.errors.CollectionInvalid, pymongo.errors.OperationFailure):
            pass  # collection already exist.

        self.coll = client[database][collection]

    def write_df(self, dataframe: pd.DataFrame = None):
        write('test_coll', dataframe)
        self.coll.find_one({})

    def insert_points(self, points: list[Point] = None):
        self.coll.insert_many(points)

    def pd_all(self):
        try:
            sw_names = dict(self.coll.find_one({}))['data'].keys()
            sw_perf = dict(self.coll.find_one({}))['data'].values()
        except KeyError:
            sw_names = []
            sw_perf = []  # todo values length less than 10

        i = 0
        for name in sw_names:
            i += 1
            df = self.coll.aggregate_pandas_all([
                {'$project': {
                    'value': f'$data.{name}',
                    'timestamp': '$timestamp'
                }}],
                schema=Schema({'value': float, 'timestamp': datetime}))

            df.sort_values('timestamp')

            if i > 10:
                break

            # df.plot(y='value', x='timestamp', label=name)
        # plt.show()
        # df['daily_pct_change'] = df['data'].sshd.pct_change() * 100


if __name__ == '__main__':
    URI = "mongodb://localhost:27017"
    m = MongoTS(uri=URI, database='test', collection='test_0031')
