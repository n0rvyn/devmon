#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-09-28 05:42
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: rid.py
# Tools: PyCharm

"""
---Read resource IDs data from CMDB, then insert to target MongoDB---
"""
import pymysql


class CMDB(object):
    def __init__(self, host: str, user: str = None, password: str = None, database: str = None):
        try:
            db = pymysql.connect(host=host, user=user, password=password, database=database)
            self.cursor = db.cursor()
        except pymysql.err.OperationalError as e:
            raise e

    def select_id(self, sql: str = None) -> list[dict]:
        data = self.cursor.fetchall()
        l_data = []

        for ip_hostname, rid in data:
            if '/' in ip_hostname:
                try:
                    _ip = ip_hostname.split('/')[0]
                    _hostname = ip_hostname.split('/')[1]

                    _d_data = {'ip': _ip, 'hostname': _hostname, 'rid': rid}

                except IndexError:
                    continue

            else:
                _d_data = {'ip_hostname': ip_hostname, 'rid': rid}

            l_data.append(_d_data)

        return l_data


if __name__ == '__main__':
    cmdb = CMDB('192.168.1.1', 'root', 'password', 'cmdb_db')
    print(cmdb.select_id())

