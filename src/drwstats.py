#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing statistics generator"""

from __future__ import print_function

# local modules
import Analysis

# system modules
import time
import sys
import codecs
import argparse


def remap(vmap, value):
    if value not in vmap:
        return None
    return vmap[value]


def dtts(dt):
    return int(time.mktime(dt.timetuple()))


def recordStats(record):
    return {"PAT_ID": record.aid,
            "PAT_TYPE": remap(Analysis.PAT_TYPE, record.pat_type),
            "PAT_HANDEDNESS": remap(Analysis.PAT_HANDEDNESS, record.pat_hand),
            "PAT_HAND": remap(Analysis.PAT_HAND, record.pat_hand),
            "OPERATOR": record.extra_data.get('operator'),
            "BLOOD_DRAWN": record.extra_data.get('blood_drawn'),
            "DRW_ID": record.drawing.id,
            "DRW_DSC": record.drawing.str,
            "REC_DATE": record.recording.session_start,
            "REC_TS": dtts(record.recording.session_start),
            "REC_NO": record.extra_data['drawing_number'],
            "REC_TRIALS": record.recording.retries,
            "REC_EVENTS": len(record.recording.events),
            "REC_LEN": (record.recording.events[-1].stamp - record.recording.events[0].stamp).total_seconds(),
            "CAL_TID": record.calibration.tablet_id,
            "CAL_DATE": record.calibration.stamp,
            "CAL_TS": dtts(record.calibration.stamp),
            "CAL_AGE": record.calibration_age};


def __main__():
    # enforce output to be UTF-8 (due to file contents)
    sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)

    ap = argparse.ArgumentParser(description='Print drawing statistics in parseable format')
    ap.add_argument('file', help='drawing file')
    args = ap.parse_args()

    record = Analysis.DrawingRecord.load(args.file)
    stats = recordStats(record)

    print('\t'.join(map(unicode, stats.keys())))
    print('\t'.join(map(unicode, stats.values())))


if __name__ == '__main__':
    __main__()
