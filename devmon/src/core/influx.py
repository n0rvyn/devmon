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
from influxdb_client_3 import InfluxDBClient3, Point, InfluxDBError, write_client_options, WriteOptions
import time
import os
import sys

_PWD_ = os.path.abspath(os.path.dirname(__file__))
_SRC_ = os.path.abspath(os.path.join(_PWD_, '../'))
_TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))
_CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
sys.path.append(_SRC_)
from type import SNMPAgent, OID, VOID

TOKEN = os.environ.get("INFLUXDB_TOKEN")
ORG = "orgs"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com/"


# ORG = "project"
# HOST = "http://172.16.10:8086"
# TOKEN = '1KlzGnddGlNpsTUdQgRDYGGE8xQNriUTOKGAlQTMs0Xl0M6S7ubV9ZFbCXiXJEkT-S8tdgDkz6y2Rk6CDbXFNQ=='
# LocI0WvYIBM690fYYg0i-X1msNsRAbKi9wU_4xyBXiWvv2VgEXz-x5gGT1dsCRE7-7MmLSKGW2ZvAlHSm__DHg==


class InfluxDB(object):
    def __init__(self, host: str = None, token: str = None, org: str = None):
        self._host = HOST
        self._token = TOKEN
        self._org = ORG
        self.client = None

        # Define callbacks for writing responses
        def success(self, data: str):
            print(f"Successfully wrote batch: data: {data}")

        def error(self, data: str, exception: InfluxDBError):
            print(f"Failed writing batch: config: {self}, data: {data}, error: {exception}")

        def retry(self, data: str, exception: InfluxDBError):
            print(f"Failed retry writing batch: config: {self}, data: {data}, error: {exception}")

        write_options = WriteOptions()
        wco = write_client_options(success_callback=success,
                                   error_callback=error,
                                   retry_callback=retry,
                                   WriteOptions=write_options)

        self.client = InfluxDBClient3(host=self._host,
                                      token=self._token,
                                      org=self._org,
                                      write_client_options=wco)
        self.database = "devmon"

    def insert_void(self, snmp_agent: SNMPAgent = None, oid: OID = None, l_void: list[VOID] = None):
        if not l_void:
            return False

        point = (Point(oid.label)
                 .tag('address', snmp_agent.address)
                 .tag('region', snmp_agent.region)
                 .tag('area', snmp_agent.area)
                 .tag('label', oid.label))
        for void in l_void:
            k = void.desc if void.desc else oid.label
            v = void.value
            point.field(k, v)

        print(point)
        return self.client.write(database=self.database, record=point)

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