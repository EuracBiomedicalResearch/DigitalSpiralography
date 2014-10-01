#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing file batch manipulator"""

from __future__ import print_function

# local modules
import Analysis

# system modules
import argparse
import datetime


# utilities
def extra_set(record, key, value):
    if key not in record.extra_data:
        record.extra_data[key] = value


# commands
def cmd_pattype(record, args):
    """Set patient type (1 arg: ID)"""
    extra_set(record, 'orig_pat_type', record.pat_type)
    record.pat_type = args[0]


def cmd_addcmt(record, args):
    """Add/append comment text (1 arg: text)"""
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmt = "{}: {}".format(stamp, args[0])
    if not record.comments:
        record.comments = cmt
    else:
        record.comments += "\n"
        record.comments += cmt


# command map
COMMANDS = {'pattype': (1, cmd_pattype),
            'addcmt': (1, cmd_addcmt)}


def __main__():
    # argument parser
    epilog = "available commands:\n"
    for cmd, data in COMMANDS.iteritems():
        epilog += "  {}:\t\t{}\n".format(cmd, data[1].__doc__)

    ap = argparse.ArgumentParser(description='Drawing file batch manipulator',
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=epilog)

    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument('-d', dest='dump', action='store_true',
                    help='Write a dump file for fast loading')
    grp.add_argument('-t', dest='text', action='store_true',
                    help='Write a simple text file for inspection')
    ap.add_argument('-i', '--input', required=True, help='drawing file')
    ap.add_argument('-o', '--output', required=True, help='output file')
    ap.add_argument('-c', dest='cmds', metavar='command', help='command (and arguments) to apply',
                    default=[], nargs='+', action='append')

    # validate
    args = ap.parse_args()
    for cmd in args.cmds:
        if cmd[0] not in COMMANDS:
            ap.error('invalid command {}'.format(cmd[0]))
        if len(cmd) - 1 != COMMANDS[cmd[0]][0]:
            ap.error('invalid number of arguments for command {}'.format(cmd[0]))

    # load
    record = Analysis.DrawingRecord.load(args.input, args.fast)
    extra_set(record, 'orig_version', record.extra_data['version'])
    extra_set(record, 'orig_format', record.extra_data['format'])

    # process
    if args.cmds:
        for cmd in args.cmds:
            COMMANDS[cmd[0]][1](record, cmd[1:])
        record.ts_updated = datetime.datetime.now()

    # save
    if args.dump:
        Analysis.DrawingRecord.dump(record, args.output)
    elif args.text:
        Analysis.DrawingRecord.save_text(record, args.output)
    else:
        Analysis.DrawingRecord.save(record, args.output)


if __name__ == '__main__':
    __main__()
