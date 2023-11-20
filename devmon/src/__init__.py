#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
_ROOT_ = os.path.abspath(os.path.dirname(__file__))
_SRC_ = os.path.abspath(os.path.join(_ROOT_, 'src'))


try:
    from type import (SNMPAgent, VOID, OIDType, OID, ArithPosition, SSHAgent, Agent,
                      OutOpts, Version, Case, TheSameCasePart,
                      CaseUpdatePart, EventType, Point, PointMeta)
    from core import (SNMP, ColorLogger, oid_to_case, PySSHClient,
                      PushMsg, MongoDB, CMDB, ContextSNMP, HidePass,
                      MongoPoint, InfluxDB, read_agents)
except ModuleNotFoundError:
    from .type import (SNMPAgent, VOID, OIDType, OID, ArithPosition, SSHAgent, Agent,
                       OutOpts, Version, Case, TheSameCasePart,
                       CaseUpdatePart, EventType, Point, PointMeta)
    from .core import (SNMP, ColorLogger, oid_to_case, PySSHClient,
                       PushMsg, MongoDB, CMDB, ContextSNMP, HidePass,
                       MongoPoint, InfluxDB, read_agents)


__all__ = [
    'SNMPAgent',
    'SNMP',
    'ColorLogger',
    'PushMsg',
    'oid_to_case',
    'MongoDB',
    'CMDB',
    'ContextSNMP',
    'Case',
    'TheSameCasePart',
    'CaseUpdatePart',
    'OID',
    'VOID',
    'EventType',
    'HidePass',
    'Point',
    'PointMeta',
    'MongoPoint',
    'InfluxDB',
    'read_agents',
    'ArithPosition',
    'SSHAgent',
    'PySSHClient'
]


