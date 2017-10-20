"""
File: const.py
"""
__author__ = 'jpindar@jpindar.com'
VERSION = 0.0
PROGRAM_NAME = ''
HEADER_IMAGE = ''
ICON_FILE = ''
HZ_PER_GHZ = 1000000000
HZ_PER_MHZ = 1000000


class MyIgnoreException(Exception):
    pass


class MyAbortException(Exception):
    pass


class MyRetryException(Exception):
    pass
