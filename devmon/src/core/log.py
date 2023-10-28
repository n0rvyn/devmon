#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Last Modified Time: 2023/4/28 09:31
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# File Name: logger.py
# Tools: PyCharm

"""
---Log formatter---

"""
import os
import logging
import sys

levels = ['debug', 'info', 'warn', 'error', 'critical']
logging_levels = dict(debug=logging.DEBUG, info=logging.INFO,
                      warn=logging.WARN, error=logging.ERROR, critical=logging.CRITICAL)


class ColorLogger(logging.Logger):
    def __init__(self, name, filename, level: str = 'warn', display=True):
        self.level = logging_levels[level]
        self.name = name
        self.logfile = filename

        logging.Logger.__init__(self, name=name, level=self.level)

        self.addHandler(logging.StreamHandler(sys.stdout)) if display else ''
        self.addHandler(logging.FileHandler(filename))

    def colorlog(self, msg: str, level: levels):
        color = {'info': '\033[0;37m', 'debug': '\033[0;32m',
                 'warn': '\033[0;33m', 'error': '\033[0;31m', 'critical': '\033[1;31m'}
        EOC = '\033[0m'

        try:
            fmt = f'%(asctime)s [%(name)s]: {color[level]}%(levelname)8s{EOC}: %(message)s'
        except KeyError:
            fmt = f'%(asctime)s [%(name)s]: {color["info"]}%(levelname)8s{EOC}: %(message)s'

        formatter = logging.Formatter(fmt=fmt, datefmt='%y/%m/%d %H:%M')
        record = logging.LogRecord(name=self.name,
                                   level=logging_levels[level],
                                   pathname='../format', lineno=1,
                                   msg=msg, args=(),
                                   exc_info=None)

        # todo pathname???
        msg = formatter.format(record)
        if level == 'debug':
            return self.debug(msg)
        if level == 'info':
            return self.info(msg)
        if level == 'warn':
            return self.warning(msg)
        if level == 'error':
            return self.error(msg)
        if level == 'critical':
            return self.critical(msg)

    def cleaner(self, max_size_mb: int):
        try:
            file_size = int(os.path.getsize(self.logfile)) // 1024 // 1024
        except FileNotFoundError:
            return False
        if file_size >= max_size_mb:
            return open(self.logfile, 'w').close()


if __name__ == '__main__':
    for _l in levels:
        logger = ColorLogger('test logger', '../../log/colorlog.log', level=_l)
        print('='*25, f'logger level: {_l:9s}', '='*25)
        logger.colorlog('hello world!', 'debug')
        logger.colorlog('hello world!', 'info')
        logger.colorlog('hello world!', 'warn')
        logger.colorlog('hello world!', 'error')
        logger.colorlog('hello world!', 'critical')
        print()

        logger.cleaner(50)


