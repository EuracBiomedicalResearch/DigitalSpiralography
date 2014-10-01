#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing file format converter"""

from __future__ import print_function

# local modules
import Analysis

# system modules
import argparse


# utilities
def extra_set(record, key, value):
    if key not in record.extra_data:
        record.extra_data[key] = value


def __main__():
    ap = argparse.ArgumentParser(description='Drawing file format converter')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument('-d', dest='dump', action='store_true',
                    help='Write a dump file for fast loading')
    grp.add_argument('-t', dest='text', action='store_true',
                    help='Write a simple text file for inspection')
    ap.add_argument('file', help='drawing file')
    ap.add_argument('output', help='output file')
    args = ap.parse_args()

    # load
    record = Analysis.DrawingRecord.load(args.file, args.fast)
    extra_set(record, 'orig_version', record.extra_data['version'])
    extra_set(record, 'orig_format', record.extra_data['format'])

    # save
    if args.dump:
        Analysis.DrawingRecord.dump(record, args.output)
    elif args.text:
        Analysis.DrawingRecord.save_text(record, args.output)
    else:
        Analysis.DrawingRecord.save(record, args.output)


if __name__ == '__main__':
    __main__()
