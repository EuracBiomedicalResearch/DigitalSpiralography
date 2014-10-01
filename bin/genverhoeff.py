#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple wrapper over the Verhoeff module"""

from __future__ import print_function

# setup path
import os, sys
DR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(DR_ROOT, "src", "lib"))
sys.path.append(os.path.join(DR_ROOT, "src", "dist"))

# local modules
from DrawingRecorder import Verhoeff

# system modules
import argparse
import sys


def __main__():
    ap = argparse.ArgumentParser(description='Batch drawing stack renderer')
    ap.add_argument('-q', dest='quiet', action='store_true', help='no output when checking')
    ap.add_argument('-p', dest='prefix', default='', help='add/strip string prefix')
    ap.add_argument('-s', dest='suffix', default='', help='add/strip string suffix')
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('-g', dest='generate', action='store_true',
                       help='generate a Verhoeff (adds prefix/suffix + check digit)')
    group.add_argument('-c', dest='check', action='store_true',
                       help='check a Verhoeff (strips prefix/suffix)')
    ap.add_argument('string', help='number/string to process')
    args = ap.parse_args()

    if args.generate:
        if not args.string.isdigit():
            print("invalid numeric code", file=sys.stderr)
            sys.exit(1)

        buf = args.prefix
        buf += Verhoeff.generate(args.string)
        buf += args.suffix
        print(buf)
    else:
        buf = args.string

        # strip prefix if matches
        if buf[0:len(args.prefix)] == args.prefix:
            buf = buf[len(args.prefix):]
        elif not args.quiet:
            print("couldn't strip prefix")

        # strip suffix if matches
        if buf[-len(args.suffix):] == args.suffix:
            buf = buf[0:-len(args.suffix)]
        elif not args.quiet:
            print("couldn't strip suffix")

        if not buf.isdigit():
            print("invalid numeric code", file=sys.stderr)
            sys.exit(1)

        res = Verhoeff.validate(buf)
        if not args.quiet:
            print("ok" if res else "checksum error")
        sys.exit(not res)


if __name__ == '__main__':
    __main__()
