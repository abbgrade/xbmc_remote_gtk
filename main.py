#!/usr/bin/env python
'''
Created on 30.05.2013

@author: abb
'''

import logging
logging.basicConfig(format = '%(asctime)s %(levelname)s %(name)s:%(message)s', level = logging.DEBUG)

import os
from xbmc_remote_gtk.controller import Core, Config

CONFIG_PATH = os.path.expanduser('~/.local/share/data/xbmc_remote_gtk/config.json')

if __name__ == '__main__':
    core = Core(Config(CONFIG_PATH))
