#!/usr/bin/env python

import sys
import os
try:
    from setuptools import setup, find_packages
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()
    from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name = 'xbmc_remote_gtk',
    version = '0.0',
    description = 'XBMC Remote',
    long_description = read('README.md'),
    author = 'Steffen Kampmann',
    author_email = 'steffen.kampmann@gmail.com',
    license = 'GPLv3',
    url = '',
    packages = ['xbmc_remote_gtk'],
    scripts = ['xbmc_remote_gtk'],
    data_files = [
        ('/usr/share/applications', ['xbmc_remote_gtk.desktop']),
    ],
)
