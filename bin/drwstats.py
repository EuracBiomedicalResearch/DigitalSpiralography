#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing statistics generator"""

from __future__ import print_function

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Data
from DrawingRecorder import DrawingStats
from DrawingRecorder import Tab

# system modules
import argparse
import codecs
import sys


def __main__():
    # enforce output to be UTF-8 (due to file contents)
    sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)

    ap = argparse.ArgumentParser(description='Print drawing statistics in parseable format')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('-c', dest='cmts', action='store_true',
                    help='Include extra COMMENTS attribute to the output')
    ap.add_argument('files', nargs='+', help='drawing file/s')
    args = ap.parse_args()

    fd = None
    for fn in args.files:
        try:
            # drawing record
            record = Data.DrawingRecord.load(fn, args.fast)
            stats = DrawingStats.get(record, args.cmts)
            stats['FILE'] = fn

            # header
            if fd is None:
                fd = Tab.TabWriter(sys.stdout, sorted(stats.keys()))

            # data
            fd.write(stats)

        except:
            logging.error('uncaught exception while analyzing {fn}'.format(fn=fn))
            raise


if __name__ == '__main__':
    __main__()
