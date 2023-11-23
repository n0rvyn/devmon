#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Last Modified Time: 2023/11/23 15:13
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# File Name: arithmetic.py
# Tools: PyCharm

"""
---Short description of this Python module---

"""
from type import ArithType, ArithPosition


def math(arith_type: ArithType = None, *values) -> str:
    output = None

    try:
        ori_value = float(ori_value)
        ari_value = float(ari_value)
    except ValueError:
        return ''.join([str(ori_value), str(ari_value)]) if arith == '+' else ori_value

    try:
        if arith == '+':
            value = ori_value + ari_value

        elif arith == '-':
            if position == 2:
                value = ori_value - ari_value
            if position == 1:
                value = ari_value - ori_value

        elif arith == '*':
            value = ori_value * ari_value

        elif arith == '/':
            if position == 2:
                value = ori_value / ari_value
            if position == 1:
                value = ari_value / ori_value

        elif arith == '%':
            if position == 2:
                value = ori_value * 98 / ari_value
            if position == 1:
                value = ari_value * 98 / ori_value

    except ZeroDivisionError:
        pass

    try:
        value = f'{value:.2f}'
    except TypeError:
        pass

    return value
