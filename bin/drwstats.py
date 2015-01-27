#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing statistics generator"""

from __future__ import print_function

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Data
from DrawingRecorder import Consts
from DrawingRecorder.Shared import dtts

# system modules
import argparse
import codecs
import re
import sys
import time


def recordStats(record, cmts):
    rec_secs = None
    if record.recording.events:
        rec_secs = (record.recording.events[-1].stamp - record.recording.events[0].stamp).total_seconds()

    rec_data_cnt = 0
    for events in [record.recording.events] + record.recording.retries:
        if len(events):
            rec_data_cnt += 1

    data = {"PAT_ID": record.aid,
            "PAT_TYPE": record.config.pat_types.get(record.pat_type, record.pat_type),
            "PAT_HANDEDNESS": Data.PAT_HANDEDNESS.get(record.pat_handedness, record.pat_handedness),
            "PAT_HAND": Data.PAT_HAND.get(record.pat_hand, record.pat_hand),
            "PAT_HAND_CNT": record.pat_hand_cnt,
            "OPERATOR": record.oid,
            "BLOOD_DRAWN": record.extra_data.get('blood_drawn'),
            "DRW_ID": record.drawing.id,
            "DRW_DSC": record.drawing.str,
            "CREATED_DATE": record.ts_created,
            "CREATED_TS": dtts(record.ts_created),
            "UPDATED_DATE": record.ts_updated,
            "UPDATED_TS": dtts(record.ts_updated),
            "REC_DATE": record.recording.session_start,
            "REC_NO": record.extra_data['drawing_number'],
            "REC_TS": dtts(record.recording.session_start),
            "REC_CYCLE": record.cycle,
            "REC_RETRIES": len(record.recording.retries) + 1,
            "REC_DATA_CNT": rec_data_cnt,
            "REC_STROKES": record.recording.strokes,
            "REC_EVENTS": len(record.recording.events),
            "REC_SECS": rec_secs,
            "CAL_OPERATOR": record.calibration.oid,
            "CAL_TID": record.calibration.tablet_id,
            "CAL_SID": record.calibration.stylus_id,
            "CAL_DATE": record.calibration.stamp,
            "CAL_TS": dtts(record.calibration.stamp),
            "CAL_AGE": record.calibration_age,
            "SCR_WIDTH": record.recording.rect_size[0],
            "SCR_HEIGHT": record.recording.rect_size[1],
            "PROG_VER": record.extra_data['version'],
            "PROG_FMT": record.extra_data['format'],
            "PROG_ORIG_VER": record.extra_data.get('orig_version'),
            "PROG_ORIG_FMT": record.extra_data.get('orig_format'),
            "INST_UUID": record.extra_data['installation_uuid'],
            "INST_DATE": record.extra_data['installation_stamp'],
            "INST_RECNO": record.extra_data['total_recordings']}

    if cmts:
        comments = re.sub(r'[\t\n ]+', ' ', record.comments)
        data['COMMENTS'] = comments.strip()

    return data


def __main__():
    # enforce output to be UTF-8 (due to file contents)
    sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)

    ap = argparse.ArgumentParser(description='Print drawing statistics in parseable format')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('-x', dest='xtra', action='store_true',
                    help='Include extra FILE attribute to the output')
    ap.add_argument('-c', dest='cmts', action='store_true',
                    help='Include extra COMMENTS attribute to the output')
    ap.add_argument('files', nargs='+', help='drawing file/s')
    args = ap.parse_args()

    hdr = True
    for file in args.files:
        # drawing record
        record = Data.DrawingRecord.load(file, args.fast)
        stats = recordStats(record, args.cmts)
        if args.xtra:
            stats['FILE'] = file

        # header
        if hdr:
            print('\t'.join(stats.keys()))
            hdr = False

        # data
        print('\t'.join(map(unicode, stats.values())))


if __name__ == '__main__':
    __main__()
