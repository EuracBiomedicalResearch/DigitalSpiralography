#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing statistics generator"""

from __future__ import print_function

# local modules
import Analysis
import Consts

# Qt
from PyQt4 import QtCore

# system modules
import time
import sys
import codecs
import argparse
import math
import numpy as np


def remap(vmap, value):
    if value not in vmap:
        return None
    return vmap[value]


def dtts(dt):
    return int(time.mktime(dt.timetuple()))


def spiralRepair(record):
    repairs = 0

    # track drawing status to recover actual tracing segments
    old_state = None
    drawing = False
    for i in xrange(len(record.recording.events)):
        event = record.recording.events[i]

        # set drawing status
        if event.typ == QtCore.QEvent.TabletPress:
            drawing = True
        elif event.typ == QtCore.QEvent.TabletRelease:
            drawing = False
        elif event.typ == QtCore.QEvent.TabletEnterProximity or \
          event.typ == QtCore.QEvent.TabletLeaveProximity:
            drawing = False

        # check if there are missing events
        if not drawing and event.pressure:
            event.typ = QtCore.QEvent.TabletPress
            drawing = True
            repairs += 1
        elif drawing and not event.pressure:
            event.typ = QtCore.QEvent.TabletRelease
            repairs += 1
            drawing = False

    return repairs


def spiralTraces(record):
    trace = []
    traces = []

    # track drawing status to recover actual tracing segments
    old_state = None
    drawing = False
    for event in record.recording.events:
        # set drawing status
        jump = True
        if event.typ == QtCore.QEvent.TabletPress:
            drawing = True
        elif event.typ == QtCore.QEvent.TabletRelease:
            drawing = False
        elif event.typ == QtCore.QEvent.TabletEnterProximity or \
          event.typ == QtCore.QEvent.TabletLeaveProximity:
            drawing = False
        else:
            jump = False

        # add to the current trace
        trace.append(event)

        # cycle traces on state changes
        if old_state != drawing or jump:
            if len(trace) > 1:
                air = len(traces) and old_state == False
                traces.append({'drawing': old_state, 'trace': trace, 'air': air})
            trace = []

        # save old status
        old_state = drawing

    # last trace
    if len(trace) > 1:
        traces.append({'drawing': old_state, 'trace': trace, 'air': False})

    return traces


def spiralLength(record, traces, func):
    total_len = 0
    total_secs = 0

    # cycle through drawing sections
    for trace in traces:
        if not func(trace):
            continue
        trace = trace['trace']

        # time
        total_secs += (trace[-1].stamp - trace[0].stamp).total_seconds()

        # length
        for i in range(1, len(trace) - 1):
            old_pos = trace[i - 1].coords_drawing
            pos = trace[i].coords_drawing
            total_len += math.hypot(old_pos[0] - pos[0], old_pos[1] - pos[1])

    return (total_len, total_secs)


def pressureCorrect(record, traces, prof):
    if prof:
        corr = np.poly1d(prof.fit)
    else:
        corr = lambda x: None

    for trace in traces:
        for event in trace['trace']:
            event.weight = corr(event.pressure)


def spiralPressure(record, traces, func):
    start = record.recording.events[0].stamp
    end = record.recording.events[-1].stamp
    pressures = []
    for trace in traces:
        if not func(trace):
            continue
        for event in trace['trace']:
            if ((event.stamp - start).total_seconds() >= 1 and (end - event.stamp).total_seconds() >= 1):
                pressures.append(event.pressure)

    return {'min': min(pressures),
            'med': sorted(pressures)[len(pressures) / 2],
            'avg': sum(pressures) / len(pressures),
            'max': max(pressures)}


def spiralWeight(record, traces, func):
    start = record.recording.events[0].stamp
    end = record.recording.events[-1].stamp
    weights = []
    for trace in traces:
        if not func(trace):
            continue
        for event in trace['trace']:
            if ((event.stamp - start).total_seconds() >= 1 and (end - event.stamp).total_seconds() >= 1):
                weights.append(event.weight)

    if not any(weights):
        return {'min': None, 'med': None, 'avg': None, 'max': None}

    return {'min': min(weights),
            'med': sorted(weights)[len(weights) / 2],
            'avg': sum(weights) / len(weights),
            'max': max(weights)}


def spiralSpeed(record, traces, window, func):
    speeds = []

    for trace in traces:
        if not func(trace):
            continue

        trace = trace['trace']
        start = trace[0].stamp
        end = trace[-1].stamp

        for event in trace:
            if ((event.stamp - start).total_seconds() <= window or (end - event.stamp).total_seconds() < window):
                continue

            w_events = []
            for w_event in trace:
                if abs((w_event.stamp - event.stamp).total_seconds()) < window:
                    w_events.append(w_event)

            w_secs = (w_events[-1].stamp - w_events[0].stamp).total_seconds()
            w_len = 0
            for i in range(1, len(w_events) - 1):
                old_pos = w_events[i - 1].coords_drawing
                pos = w_events[i].coords_drawing
                w_len += math.hypot(old_pos[0] - pos[0], old_pos[1] - pos[1])

            event.speed = w_len / w_secs
            speeds.append(event.speed)

    if not speeds:
        min_speed = -1
        med_speed = -1
        avg_speed = -1
        max_speed = -1
    else:
        min_speed = min(speeds)
        med_speed = sorted(speeds)[len(speeds) / 2]
        avg_speed = sum(speeds) / len(speeds)
        max_speed = max(speeds)

    return {'min': min_speed,
            'med': med_speed,
            'avg': avg_speed,
            'max': max_speed}


def recordStats(record, profs):
    repairs = spiralRepair(record)
    traces = spiralTraces(record)

    spr_drw_len, spr_drw_secs = spiralLength(record, traces, lambda x: x['drawing'])
    spr_air_len, spr_air_secs = spiralLength(record, traces, lambda x: x['air'])
    spr_len = spr_drw_len + spr_air_len
    spr_secs = spr_drw_secs + spr_air_secs
    spr_speed = -1 if spr_secs < 1 else spr_len / spr_secs

    prof = profs.get(record.calibration.stylus_id)
    pressureCorrect(record, traces, prof)

    pressures = spiralPressure(record, traces, lambda x: x['drawing'])
    weights = spiralWeight(record, traces, lambda x: x['drawing'])

    speedsW1 = spiralSpeed(record, traces, 1., lambda x: x['drawing'])
    speedsW01 = spiralSpeed(record, traces, 0.1, lambda x: x['drawing'])
    speedsW005 = spiralSpeed(record, traces, 0.05, lambda x: x['drawing'])

    return {"PAT_ID": record.aid,
            "PAT_TYPE": remap(Consts.PAT_TYPES, record.pat_type),
            "PAT_HANDEDNESS": remap(Analysis.PAT_HANDEDNESS, record.pat_handedness),
            "PAT_HAND": remap(Analysis.PAT_HAND, record.pat_hand),
            "OPERATOR": record.oid,
            "BLOOD_DRAWN": record.extra_data.get('blood_drawn'),
            "DRW_ID": record.drawing.id,
            "DRW_DSC": record.drawing.str,
            "REC_DATE": record.recording.session_start,
            "REC_TS": dtts(record.recording.session_start),
            "REC_NO": record.extra_data['drawing_number'],
            "REC_TRIALS": len(record.recording.retries) + 1,
            "REC_EVENTS": len(record.recording.events),
            "REC_SECS": (record.recording.events[-1].stamp - record.recording.events[0].stamp).total_seconds(),
            "CAL_TID": record.calibration.tablet_id,
            "CAL_SID": record.calibration.stylus_id,
            "CAL_DATE": record.calibration.stamp,
            "CAL_TS": dtts(record.calibration.stamp),
            "CAL_AGE": record.calibration_age,
            "SPR_REPAIRS": repairs,
            "SPR_LEN": spr_len,
            "SPR_SECS": spr_secs,
            "SPR_SPEED": spr_speed,
            "SPR_DRW_LEN": spr_drw_len,
            "SPR_DRW_SECS": spr_drw_secs,
            "SPR_DRW_MIN_PRESS_T1": pressures['min'],
            "SPR_DRW_MED_PRESS_T1": pressures['med'],
            "SPR_DRW_AVG_PRESS_T1": pressures['avg'],
            "SPR_DRW_MAX_PRESS_T1": pressures['max'],
            "SPR_DRW_MIN_WEIGHT_T1": weights['min'],
            "SPR_DRW_MED_WEIGHT_T1": weights['med'],
            "SPR_DRW_AVG_WEIGHT_T1": weights['avg'],
            "SPR_DRW_MAX_WEIGHT_T1": weights['max'],
            "SPR_DRW_MIN_SPEED_W1": speedsW1['min'],
            "SPR_DRW_MED_SPEED_W1": speedsW1['med'],
            "SPR_DRW_AVG_SPEED_W1": speedsW1['avg'],
            "SPR_DRW_MAX_SPEED_W1": speedsW1['max'],
            "SPR_DRW_MIN_SPEED_W01": speedsW01['min'],
            "SPR_DRW_MED_SPEED_W01": speedsW01['med'],
            "SPR_DRW_AVG_SPEED_W01": speedsW01['avg'],
            "SPR_DRW_MAX_SPEED_W01": speedsW01['max'],
            "SPR_DRW_MIN_SPEED_W005": speedsW005['min'],
            "SPR_DRW_MED_SPEED_W005": speedsW005['med'],
            "SPR_DRW_AVG_SPEED_W005": speedsW005['avg'],
            "SPR_DRW_MAX_SPEED_W005": speedsW005['max'],
            "SPR_AIR_LEN": spr_air_len,
            "SPR_AIR_SECS": spr_air_secs}


def __main__():
    # enforce output to be UTF-8 (due to file contents)
    sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)

    ap = argparse.ArgumentParser(description='Print drawing statistics in parseable format')
    ap.add_argument('-p', dest='prof', action='append', default=[],
                    help='Load stylus correction profile (repeat to load multiple profiles)')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('-x', dest='xtra', action='store_true',
                    help='Include extra FILE attribute to the output')
    ap.add_argument('file', help='drawing file')
    args = ap.parse_args()

    # load correction profiles
    profs = {}
    for path in args.prof:
        data = Analysis.StylusProfile.load(path)
        profs[data.sid] = data

    # drawing record
    record = Analysis.DrawingRecord.load(args.file, args.fast)

    # generate statistics
    stats = recordStats(record, profs)
    if args.xtra:
        stats['FILE'] = args.file

    print('\t'.join(map(unicode, stats.keys())))
    print('\t'.join(map(unicode, stats.values())))


if __name__ == '__main__':
    __main__()
