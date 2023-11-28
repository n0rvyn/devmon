#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from typing import Literal
from dataclasses import dataclass


@dataclass
class Config:
    log_name: str = 'devmon'
    log_level: str = 'WARNING'
    log_show: str = False
    rlog_server: str = 'localhost'
    rlog_port: int = 514
    mongo_uri: str = None
    mongo_server: str = None
    mongo_user: str = None
    mongo_pass: str = None
    mongo_port: int = 27017
    mongo_db: str = 'devmon'
    mongo_col: str = 'devmon'
    mongo_cmdb_col: str = 'cmdb'
    mongo_ts_col: str = 'perfmon'
    multithread: bool = True
    multiprocess: bool = True
    interval: int = 300
    snmpwalk: str = '/usr/bin/snmpwalk'
    source: str = 'DevMon Console'
    patrol: int = 5
    notify_window: str = '8:00-18:00'
    cmdb_server: str = 'localhost'
    cmdb_db: str = 'cmdb'
    cmdb_user: str = 'root'
    cmdb_pass: str = None
    influx_url: str = 'http://localhost:8086'
    influx_token: str = None
    influx_org: str = 'org'
    influx_db: str = 'devmon'
    event_keys: list = ('sources', 'severity', 'description', 'content', 'type', 'object', 'current_value', 'rid', 'addr_in_cmdb')
    event_delimiter: str = '||'

