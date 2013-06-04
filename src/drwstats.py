#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing statistics generator"""

from __future__ import print_function

# local modules
import Analysis

# Qt
from PyQt4 import QtCore

# system modules
import time
import sys
import codecs
import argparse
import math


def remap(vmap, value):
    if value not in vmap:
        return None
    return vmap[value]


def dtts(dt):
    return int(time.mktime(dt.timetuple()))


def spiralLength(record):
    total_len = 0
    total_secs = 0

    # track drawing status to recover actual tracing length/time
    old_pos = None
    old_stamp = None
    drawing = False
    for event in record.recording.events:
        stamp = event.stamp
        pos = event.coords_drawing

        # set drawing status
        if event.typ == QtCore.QEvent.TabletPress:
            drawing = True
        elif event.typ == QtCore.QEvent.TabletRelease:
            drawing = False
        elif event.typ == QtCore.QEvent.TabletEnterProximity or \
          event.typ == QtCore.QEvent.TabletLeaveProximity:
            drawing = False
            pos = None

        if old_pos:
            if drawing:
                total_len += math.hypot(old_pos[0] - pos[0], old_pos[1] - pos[1])
                total_secs += (stamp - old_stamp).total_seconds()

        # save old status
        old_pos = pos
        old_stamp = stamp

    return (total_len, total_secs)


def recordStats(record):
    spr_len, spr_secs = spiralLength(record)

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
            "REC_SECS": (record.recording.events[-1].stamp - record.recording.events[0].stamp).total_seconds(),
            "CAL_TID": record.calibration.tablet_id,
            "CAL_DATE": record.calibration.stamp,
            "CAL_TS": dtts(record.calibration.stamp),
            "CAL_AGE": record.calibration_age,
            "SPR_LEN": spr_len,
            "SPR_SECS": spr_secs};


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
