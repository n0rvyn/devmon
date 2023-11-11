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
from type import SNMPAgent, OID, VOID

# _PWD_ = os.path.abspath(os.path.dirname(__file__))
# _SRC_ = os.path.abspath(os.path.join(_PWD_, '../'))
# _TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))
# _CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
# sys.path.append(_SRC_)


class InfluxDB(object):
    def __init__(self, host: str = None, token: str = None, org: str = None, database: str = None):
        self._host = host
        self._token = token
        self._org = org
        self.client = None

        # Define callbacks for writing responses
        def success(self, data: str):
            print(f"Successfully wrote batch: config: {self}, data: {data}")

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
        self.database = database

    # def ____insert_void(self, snmp_agent: SNMPAgent = None, oid: OID = None, l_void: list[VOID] = None):
    #     if not l_void:
    #         return False
    #
    #     point = (Point(oid.label)
    #              .tag('address', snmp_agent.address)
    #              .tag('region', snmp_agent.region)
    #              .tag('area', snmp_agent.area)
    #              .tag('label', oid.label))
    #
    #     for void in l_void:
    #         k = void.desc if void.desc else oid.label
    #
    #         try:
    #             v = float(void.value)
    #         except ValueError:
    #             continue
    #
    #         point.field(k, v)
    #         print(point)
    #
    #     # print(point)
    #     return self.client.write(database=self.database, record=point)

    @staticmethod
    def void_to_point(snmp_agent: SNMPAgent = None, oid: OID = None, l_void: list[VOID] = None) -> Point:
        if not l_void:
            return Point('Nul')

        if oid.label == 'gpfsFsSystemBytes':
            print(l_void)

        point = (Point(oid.label)
                 .tag('address', snmp_agent.address)
                 .tag('region', snmp_agent.region)
                 .tag('area', snmp_agent.area)
                 .tag('label', oid.label))

        for void in l_void:
            if not void:  # todo l_void == [None, None...] ???
                continue

            k = void.desc if void.desc else oid.label

            try:
                v = float(void.value)
            except (ValueError, TypeError):
                continue

            point.field(k, v)
        return point

    # def cal_point_shift(last_point: Point = None, point: Point = None) -> Point:
    #     new_point: Point = Point(point.measurement)
    #
    #     for (tag, value) in point._tags.items():
    #         new_point.tag(tag, value)
    #
    #     fields = {key: (value - last_point.fields[key]) for (key, value) in point.fields.items()}
    #     new_point.from_dict(fields)
    #
    #     # for (key, value) in point._fields.items():
    #     #     try:
    #     #         new_value = value - last_point._fields[key]
    #     #         new_point.field(key, new_value)
    #     #     except ValueError:
    #     #         pass
    #     print(new_point, last_point)
    #
    #     return new_point

    # def cal_many_points_shift(self, last_points: list[Point] = None, points: list[Point] = None) -> list[Point]:
    #     final_points = []
    #
    #     if len(last_points) != len(points):
    #         return points
    #
    #     last_points.sort()
    #     points.sort()
    #
    #     def cal_target(last_point: Point, point: Point):
    #         final_points.append(self.cal_point_shift(last_point, point))
    #
    #     threads = [Thread(target=cal_target, args=(last_points[i], points[i])) for i in range(len(last_points))]
    #     [t.start() for t in threads]
    #     [t.join() for t in threads]
    #
    #     return final_points

    def insert_points(self, points: list[Point] = None):
        return self.client.write(record=points, database=self.database)

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