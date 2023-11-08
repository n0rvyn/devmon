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


import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = os.environ.get("INFLUXDB_TOKEN")
org = "project"
url = "http://172.16.10.250:8086"

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)


ORG = "project"
HOST = "http://172.16.10:8086"
TOKEN = '1KlzGnddGlNpsTUdQgRDYGGE8xQNriUTOKGAlQTMs0Xl0M6S7ubV9ZFbCXiXJEkT-S8tdgDkz6y2Rk6CDbXFNQ=='


class InfluxDB(object):
    def __init__(self, host: str = None, token: str = None, org: str = None):
        host = HOST
        token = TOKEN
        org = ORG
        self.client = InfluxDBClient3(host=host, token=token, org=org)
        self.database = "devmon"

    # def oid_to_point(self, snmp_agent: SNMPAgent, oid: OID = None, l_void: list[VOID] = None):
    def oid_to_point(self, address: str = None):
        point = (Point('Perf').tag('title1', 1995).tag('title2', 1996))

        return point

    def insert(self, point: Point = None):
        self.client.write(database=self.database, record=point)

    def select(self):
        query = ("SELECT *FROM 'census' WHERE time >= now() - interval '24 hours' "
                 "AND ('bees' IS NOT NULL OR 'ants' IS NOT NULL)")

        # Execute the query
        table = self.client.query(query=query, database=self.database, language='sql')

        # Convert to dataframe
        df = table.to_pandas().sort_values(by="time")
        print(df)

        """
        query = "SELECT mean('init') FROM 'census' WHERE time > now() - '10m'"

        # Execute the query
        table = self.client.query(query=query, database="devmon", language='influxql')

        # Convert to dataframe
        df = table.to_pandas().sort_values(by="time")
        print(df)
        
        query_api = client.query_api()

        query = from(bucket: "<BUCKET>")
        |> range(start: -10m)
        |> filter(fn: (r) => r._measurement == "measurement1")
        
        
        tables = query_api.query(query, org="project")

        for table in tables:
        for record in table.records:
        print(record)
        """


if __name__ == '__main__':
    pass

    """
    influx delete --host "https://us-east-1.com" --token {NbL5jpRcgmIblHsFun1K-rm-7P20pPtseXHaSl2NGGZu4SfD0EQ==} --org {OPS}  --bucket {devmon}  --start 1970-01-01T00:00:00Z   --stop $(date +"%Y-%m-%dT%H:%M:%SZ")
    """
    idb = InfluxDB()
    idb.insert(idb.oid_to_point('172.16.104'))





