#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing file format converter"""

from __future__ import print_function

# local modules
import Analysis

# system modules
import argparse


def __main__():
    ap = argparse.ArgumentParser(description='Drawing file format converter')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('-d', dest='dump', action='store_true',
                    help='Write a dump file for fast loading')
    ap.add_argument('file', help='drawing file')
    ap.add_argument('output', help='output file')
    args = ap.parse_args()

    record = Analysis.DrawingRecord.load(args.file, args.fast)
    if args.dump:
        Analysis.DrawingRecord.dump(record, args.output)
    else:
        Analysis.DrawingRecord.save(record, args.output)


if __name__ == '__main__':
    __main__()
