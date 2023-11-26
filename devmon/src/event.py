# -*- coding: utf-8 -*-
# dataclass definition for EventType
from typing import Literal


EventType = Literal[
    'alert', 'recovery', 'message'
]

