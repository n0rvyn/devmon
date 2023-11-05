#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class SSHAgent:
    address: str = None
    port: int = 22
    region: str = None
    area: str = None
    addr_in_cmdb: str = None
    username: str = 'root'
    password: str = None
    pubkey: str = None
    timeout: int = 3
