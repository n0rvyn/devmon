#!/usr/bin/env python3
# -*- coding: utf-8 -*-
try:
    from type import SNMPAgent, VOID, OIDType, OID, OutOpts, Version
    from core import SNMP, ReadConfig, ReadAgents, ColorLogger
except ModuleNotFoundError:
    from .type import SNMPAgent, VOID, OIDType, OID, OutOpts, Version
    from .core import SNMP, ReadConfig, ReadAgents, ColorLogger


__all__ = [
    'SNMPAgent',
    'ColorLogger',
    'ReadAgents'
]