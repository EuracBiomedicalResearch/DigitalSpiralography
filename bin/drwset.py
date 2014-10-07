#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing file converter/batch manipulator"""

from __future__ import print_function

# setup path
import os, sys
DR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(DR_ROOT, "src", "lib"))
sys.path.append(os.path.join(DR_ROOT, "src", "dist"))

# local modules
from DrawingRecorder import Data

# system modules
import argparse
import datetime


# utilities
def extra_set(record, key, value):
    if key not in record.extra_data:
        record.extra_data[key] = value


# commands
class CmdPatType(object):
    narg = 1
    help = 'Set patient type (1 arg: ID)'

    @classmethod
    def handler(cls, record, args):
        extra_set(record, 'orig_pat_type', record.pat_type)
        record.pat_type = args[0]


class CmdAddCmt(object):
    narg = 1
    help = 'Add/append comment text (1 arg: text)'

    @classmethod
    def handler(cls, record, args):
        stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cmt = '{}: {}'.format(stamp, args[0])
        if not record.comments:
            record.comments = cmt
        else:
            record.comments += "\n"
            record.comments += cmt


# command map
COMMANDS = {'addcmt': CmdAddCmt,
            'pattype': CmdPatType}


def __main__():
    # argument parser
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

    if not COMMANDS:
        cmd_help = argparse.SUPPRESS
    else:
        cmd_help = 'command (and arguments) to apply'
        ap.epilog = 'available commands:\n'
        for cmd, cls in COMMANDS.iteritems():
            ap.epilog += "  {}:\t\t{}\n".format(cmd, cls.help)
    ap.add_argument('-c', dest='cmds', metavar='command', help=cmd_help,
                    default=[], nargs='+', action='append')

    # validate
    args = ap.parse_args()
    for cmd in args.cmds:
        if cmd[0] not in COMMANDS:
            ap.error('invalid command {}'.format(cmd[0]))
        if len(cmd) - 1 != COMMANDS[cmd[0]].narg:
            ap.error('invalid number of arguments for command {}'.format(cmd[0]))

    # load
    record = Data.DrawingRecord.load(args.input, args.fast)
    extra_set(record, 'orig_version', record.extra_data['version'])
    extra_set(record, 'orig_format', record.extra_data['format'])

    # process
    if args.cmds:
        for cmd in args.cmds:
            COMMANDS[cmd[0]].handler(record, cmd[1:])
        record.ts_updated = datetime.datetime.now()

    # save
    if args.dump:
        Data.DrawingRecord.dump(record, args.output)
    elif args.text:
        Data.DrawingRecord.save_text(record, args.output)
    else:
        Data.DrawingRecord.save(record, args.output)


if __name__ == '__main__':
    __main__()
