#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drawing statistics generator"""

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Data
from DrawingRecorder import DrawingStats
from DrawingRecorder import Tab

# system modules
import argparse
import logging
import sys


def __main__():
    # enforce output to be UTF-8 (due to file contents)
    sys.stdout.reconfigure(encoding='utf-8')

    ap = argparse.ArgumentParser(description='Print drawing statistics in parseable format')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('-c', dest='cmts', action='store_true',
                    help='Include extra COMMENTS attribute to the output')
    ap.add_argument('files', nargs='+', help='drawing file/s')
    args = ap.parse_args()
    logging.basicConfig(format='%(levelname)s: %(message)s')

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

        except Exception as e:
            if len(args.files) == 1:
                raise e
            else:
                print('{fn}: uncaught exception {e}'.format(fn=fn, e=str(e)), file=sys.stderr)


if __name__ == '__main__':
    __main__()
