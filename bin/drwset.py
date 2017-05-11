#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drawing file converter/batch manipulator"""

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


def __main__():
    # arguments
    ap = argparse.ArgumentParser(description='Drawing file batch converter/manipulator',
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument('-d', dest='dump', action='store_true',
                     help='Write a dump file for fast loading')
    grp.add_argument('-t', dest='text', action='store_true',
                     help='Write a simple text file for inspection')
    ap.add_argument('-i', '--input', required=True, help='drawing file')
    ap.add_argument('-o', '--output', required=True, help='output file')
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument('--stats', help='Apply updated output from drwstats')
    grp.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), action='append',
                     help='Set a single field (can be repeated)')
    args = ap.parse_args()
    logging.basicConfig(format='%(levelname)s: %(message)s')

    # load
    record = Data.DrawingRecord.load(args.input, args.fast)

    # process
    if args.set:
        data = dict(args.set)
        try:
            DrawingStats.set(record, data)
        except ValueError as e:
            logging.error(e)
            sys.exit(1)
    elif args.stats:
        data = None
        fd = Tab.TabReader(args.stats, ['FILE'])
        for row in fd:
            if row['FILE'] == args.input:
                data = row
                break
        if data is None:
            logging.warning('input file not been updated (no matching entry in {})'.format(args.stats))
        else:
            try:
                DrawingStats.set(record, data)
            except ValueError as e:
                logging.error(e)
                sys.exit(1)

    # save
    if args.dump:
        Data.DrawingRecord.dump(record, args.output)
    elif args.text:
        Data.DrawingRecord.save_text(record, args.output)
    else:
        Data.DrawingRecord.save(record, args.output)


if __name__ == '__main__':
    __main__()
