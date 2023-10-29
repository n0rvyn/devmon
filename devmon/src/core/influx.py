#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-10-29 16:27
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: influx.py
# Tools: PyCharm

"""
---Short description of this Python module---

"""
from influxdb_client_3 import InfluxDBClient3, Point
import time

ORG = "OPS"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = 'NbL5jpRcgmIblHsFun5B1K-rm-7P20pPtseXHaSl2blC2rOiINc4Y73OSzAWvwzBVWKn9nv7dfNGGZu4SfD0EQ=='


class InfluxClient(object):
    def __init__(self, host: str = None, token: str = None, org: str = None):
        self.client = InfluxDBClient3(host=host, token=token, org=org)
        self.database = "devmon"

    def insert(self, data: dict = None):
        for key in data:
            point = (
                Point("census")
                .tag("location", data[key]["location"])
                .field(data[key]["species"], data[key]["count"])
            )

            self.client.write(database=self.database, record=point)

    def select(self):
        query = ("SELECT *FROM 'census' WHERE time >= now() - interval '24 hours' "
                 "AND ('bees' IS NOT NULL OR 'ants' IS NOT NULL)")

        # Execute the query
        table = self.client.query(query=query, database=self.database, language='sql')

        # Convert to dataframe
        df = table.to_pandas().sort_values(by="time")
        print(df)

        query = "SELECT mean(count) FROM 'census' WHERE time > now() - '10m'"

        # Execute the query
        table = self.client.query(query=query, database="devmon", language='influxql')

        # Convert to dataframe
        df = table.to_pandas().sort_values(by="time")
        print(df)


if __name__ == '__main__':
    pass

    _data = {
        "point1": {
            "location": "Klamath",
            "species": "bees",
            "count": 23,
        },
        "point2": {
            "location": "Portland",
            "species": "ants",
            "count": 30,
        },
        "point3": {
            "location": "Klamath",
            "species": "bees",
            "count": 28,
        },
        "point4": {
            "location": "Portland",
            "species": "ants",
            "count": 32,
        },
        "point5": {
            "location": "Klamath",
            "species": "bees",
            "count": 29,
        },
        "point6": {
            "location": "Portland",
            "species": "ants",
            "count": 40,
        },
    }
