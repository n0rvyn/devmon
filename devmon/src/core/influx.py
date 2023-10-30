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
from type import SNMPAgent, OID, VOID

ORG = "OPS"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = 'NbL5jpRcgmIblHsFun5B1K-rm-7P20pPtseXHaSl2blC2rOiINc4Y73OSzAWvwzBVWKn9nv7dfNGGZu4SfD0EQ=='


class InfluxDB(object):
    def __init__(self, host: str = None, token: str = None, org: str = None):
        host = HOST
        token = TOKEN
        org = ORG
        self.client = InfluxDBClient3(host=host, token=token, org=org)
        self.database = "devmon"

    def oid_to_point(self, snmp_agent: SNMPAgent, oid: OID = None, l_void: list[VOID] = None):
        point = (Point('census').tag('address', snmp_agent))
        [point.field(void.desc, void.value) for void in l_void if float(void.value) > 0]

        return point

    def insert(self, point: Point = None):
        self.client.write(database=self.database, record=point)

    def select(self):
        query = ("SELECT * FROM 'census' WHERE time >= now() - interval '24 hours' "
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
        """


if __name__ == '__main__':
    pass

    """
    influx delete --host "https://us-east-1-1.aws.cloud2.influxdata.com" --token {NbL5jpRcgmIblHsFun5B1K-rm-7P20pPtseXHaSl2blC2rOiINc4Y73OSzAWvwzBVWKn9nv7dfNGGZu4SfD0EQ==} --org {OPS}  --bucket {devmon}  --start 1970-01-01T00:00:00Z   --stop $(date +"%Y-%m-%dT%H:%M:%SZ")
    """


