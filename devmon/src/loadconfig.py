#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 2023-11-28 19:21
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: readconfig.py
# Tools: PyCharm

"""
---Reading configuration information from 'ROOT/etc/conf/devmon.yaml'
"""

from yaml import safe_load
from .config import Config
from dataclasses import asdict


def load_config(config: str = None) -> Config:
    try:
        with open(config, 'r+') as f:
            raw_config = safe_load(f)
    except FileNotFoundError as err:
        raise err

    config = Config()
    config_detail = asdict(config)

    for key in config_detail:
        try:
            config_detail[key] = raw_config[key]
        except KeyError:
            pass

    [config.__setattr__(key, value) for (key, value) in config_detail.items()]

    return config
