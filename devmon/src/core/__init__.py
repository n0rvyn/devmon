#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

_FILE_ = os.path.abspath(__file__)
_SRC_ = os.path.abspath(os.path.join(_FILE_, '../../'))
_CORE_ = os.path.abspath(os.path.join(_SRC_, 'core'))
_TYPE_ = os.path.abspath(os.path.join(_SRC_, 'type'))


try:
    # from readfile import ReadConfig, ReadAgents
    from read_devlist import ReadAgents
    from snmp import SNMP, ContextSNMP
    from log import ColorLogger
    from pushmsg import PushMsg
    from mongo import MongoDB
    from cmdb import CMDB
    from cre_case import oid_to_case
    from encrypt import HidePass
except (ModuleNotFoundError, ImportError):
    from .read_devlist import ReadAgents
    from .snmp import SNMP, ContextSNMP
    from .log import ColorLogger
    from .pushmsg import PushMsg
    from .mongo import MongoDB
    from .cmdb import CMDB
    from .cre_case import oid_to_case
    from .encrypt import HidePass


__all__ = [
    'ReadAgents',
    'SNMP',
    'ColorLogger',
    'PushMsg',
    'MongoDB',
    'CMDB',
    'ContextSNMP',
    'oid_to_case',
    'HidePass'
]

