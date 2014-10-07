#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stylus profile file converter/batch manipulator"""

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
def extra_set(profile, key, value):
    if key not in profile.extra_data:
        profile.extra_data[key] = value


# command map
COMMANDS = {}


def __main__():
    # argument parser
    ap = argparse.ArgumentParser(description='Stylus profile file batch converter/manipulator',
                                 formatter_class=argparse.RawTextHelpFormatter)

    ap.add_argument('-t', dest='text', action='store_true',
                    help='Write a simple text file for inspection')
    ap.add_argument('-i', '--input', required=True, help='profile file')
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
    profile = Data.StylusProfile.load(args.input)
    extra_set(profile, 'orig_version', profile.extra_data['version'])
    extra_set(profile, 'orig_format', profile.extra_data['format'])

    # process
    if args.cmds:
        for cmd in args.cmds:
            COMMANDS[cmd[0]].handler(profile, cmd[1:])
        profile.ts_updated = datetime.datetime.now()

    # save
    if args.text:
        Data.StylusProfile.save_text(profile, args.output)
    else:
        Data.StylusProfile.save(profile, args.output)


if __name__ == '__main__':
    __main__()
