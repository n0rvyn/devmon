#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
_ROOT_ = os.path.abspath(os.path.dirname(__file__))
_SRC_ = os.path.abspath(os.path.join(_ROOT_, 'src'))


try:
    from type import (SNMPAgent, VOID, OIDType, OID,
                      OutOpts, Version, Case, TheSameCasePart,
                      CaseUpdatePart, EventType, Point, PointMeta)
    from core import (SNMP, ReadAgents, ColorLogger, oid_to_case,
                      PushMsg, MongoDB, CMDB, ContextSNMP, HidePass,
                      MongoPoint, InfluxDB)
except ModuleNotFoundError:
    from .type import (SNMPAgent, VOID, OIDType, OID,
                       OutOpts, Version, Case, TheSameCasePart,
                       CaseUpdatePart, EventType, Point, PointMeta)
    from .core import (SNMP, ReadAgents, ColorLogger, oid_to_case,
                       PushMsg, MongoDB, CMDB, ContextSNMP, HidePass,
                       MongoPoint, InfluxDB)


__all__ = [
    'SNMPAgent',
    'SNMP',
    'ColorLogger',
    'ReadAgents',
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
    'InfluxDB'
]


