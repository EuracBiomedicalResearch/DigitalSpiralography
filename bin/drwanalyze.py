#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drawing analyzer"""

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Analysis
from DrawingRecorder import Data
from DrawingRecorder import DrawingStats
from DrawingRecorder import Profile
from DrawingRecorder import Tab

# system modules
import argparse
import logging
import os.path
import sys


def __main__():
    ap = argparse.ArgumentParser(description='Drawing analyzer')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('-c', dest='config', required=True,
                    help='Analysis configuration file')
    ap.add_argument('-o', dest='ovr_only', action='store_true',
                    help='Analyze only the files supplied in the override list')
    ap.add_argument('-m', dest='ovr_merge', action='store_true',
                    help='Merge override data into the output')
    ap.add_argument('-v', default=0, action='count', help='Increase verbosity')
    ap.add_argument('files', nargs='*', help='drawing file/s')
    args = ap.parse_args()

    # logging configuration
    lvl = logging.WARNING
    if args.v > 1: lvl = logging.DEBUG
    elif args.v > 0: lvl = logging.INFO
    logging.basicConfig(level=lvl, format='%(levelname)s: %(message)s')

    # load/initialize the configuration data
    root = os.path.dirname(args.config)
    cfg = Data.AnalysisCfg.load(args.config, root)
    pmap = Profile.ProfileMapper(cfg.profiles, cfg.sur)
    if not pmap.sids() and cfg.sur:
        logging.error('An usage report was supplied, but no profiles were provided')
        sys.exit(1)

    # load stats
    stats = {}
    if cfg.stats:
        fd = Tab.TabReader(cfg.stats, ['FILE'])
        for row in fd:
            fn = os.path.join(root, row.pop('FILE'))
            stats[fn] = row
    elif args.ovr_only:
        logging.error('Override was requested, but no override file was provided')
        sys.exit(1)
    if args.ovr_only and not args.files:
        args.files = stats.keys()
    if not args.files:
        logging.error('No files to analyze')
        sys.exit(1)

    fd = None
    for fn in args.files:
        try:
            # load record
            record = Data.DrawingRecord.load(fn, args.fast)
            ovr_stats = stats.get(fn)
            if ovr_stats:
                DrawingStats.set(record, ovr_stats)
            elif cfg.stats:
                if args.ovr_only:
                    continue
                else:
                    logging.warning('{} was not found in {}'.format(fn, cfg.stats))

            # analyze
            sm = pmap.map_at_time(record.calibration.stylus_id, record.calibration.stamp)
            res = Analysis.analyze(record, cfg, sm).info()
            res['FILE'] = fn

            # merge with overrides
            if args.ovr_merge and ovr_stats:
                for k, v in ovr_stats.items():
                    while k in res:
                        k += "_"
                    res[k] = v

            # output data
            if fd is None:
                fd = Tab.TabWriter(sys.stdout, sorted(res.keys()))
            fd.write(res)

        except:
            logging.critical('uncaught exception while analyzing {fn}'.format(fn=fn))
            raise


if __name__ == '__main__':
    __main__()
