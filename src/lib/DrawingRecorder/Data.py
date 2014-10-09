# -*- coding: utf-8 -*-
"""Drawing structures/analysis"""

from __future__ import print_function

# local modules
import Consts
import Drawing
from UI import translate

# system modules
import datetime
import yaml
from copy import copy
import gzip
from PyQt4 import QtCore
import numpy as np
import cPickle


# basic types
class PatHandedness(object):
    left, right, ambidextrous = range(3)

class PatHand(object):
    left, right = range(2)


# helpers
def _from_type(type_map, value):
    if value in type_map:
        return type_map[value]
    return value


def _to_type(type_map, value):
    for k, v in type_map.iteritems():
        if value == v:
            return k
    return value


# File format event/code maps
EVENT_MAP = {QtCore.QEvent.TabletMove: 'move',
             QtCore.QEvent.TabletPress: 'press',
             QtCore.QEvent.TabletRelease: 'release',
             QtCore.QEvent.TabletEnterProximity: 'enter',
             QtCore.QEvent.TabletLeaveProximity: 'leave'}

PAT_HANDEDNESS = {PatHandedness.left: 'Left-handed',
                  PatHandedness.right: 'Right-handed',
                  PatHandedness.ambidextrous: 'Ambidextrous'}

PAT_HANDEDNESS_DSC = {PatHandedness.left: translate('types', 'Left-handed'),
                      PatHandedness.right: translate('types', 'Right-handed'),
                      PatHandedness.ambidextrous: translate('types', 'Ambidextrous')}

PAT_HAND = {PatHand.left: 'Left',
            PatHand.right: 'Right'}

PAT_HAND_DSC = {PatHand.left: translate('types', 'Left'),
                PatHand.right: translate('types', 'Right')}

BOOL_MAP_DSC = {True: translate('types', 'Yes'),
                False: translate('types', 'No')}


# Calibration/Recording data
class CalibrationData(object):
    def __init__(self, oid, tablet_id, stylus_id, cpoints, stamp=None):
        self.oid = oid
        self.tablet_id = tablet_id
        self.stylus_id = stylus_id
        self.cpoints = cpoints
        self.stamp = stamp if stamp is not None else datetime.datetime.now()


class RecordingEvent(object):
    def __init__(self, typ, coords_drawing, coords_trans, pressure,
                 tilt_drawing, tilt_trans, stamp=None):
        self.typ = typ
        self.coords_drawing = coords_drawing
        self.coords_trans = coords_trans
        self.pressure = pressure
        self.tilt_drawing = tilt_drawing
        self.tilt_trans = tilt_trans
        self.stamp = stamp if stamp is not None else datetime.datetime.now()


    @classmethod
    def serialize(cls, event):
        data =  {'stamp': event.stamp,
                 'type': _from_type(EVENT_MAP, event.typ),
                 'cdraw': list(event.coords_drawing),
                 'ctrans': list(event.coords_trans),
                 'press': event.pressure}

        # optional (fmt 1.1)
        if event.tilt_drawing is not None:
            data['tdraw'] = list(event.tilt_drawing)
            data['ttrans'] = list(event.tilt_trans)

        return data


    @classmethod
    def deserialize(cls, event):
        typ = _to_type(EVENT_MAP, event['type'])
        coords_drawing = tuple(event['cdraw'])
        coords_trans = tuple(event['ctrans'])
        pressure = event['press']
        stamp = event['stamp']

        # optional elements (format 1.1)
        tilt_drawing = event.get('tdraw')
        tilt_trans = event.get('ttrans')
        if tilt_drawing is not None:
            tilt_drawing = tuple(tilt_drawing)
            tilt_trans = tuple(tilt_trans)

        return RecordingEvent(typ, coords_drawing, coords_trans, pressure,
                              tilt_drawing, tilt_trans, stamp)



class RecordingData(object):
    def __init__(self, session_start=None, rect_size=None, rect_drawing=None,
                 rect_trans=None, events=None, retries=None, strokes=0):
        self.session_start = session_start if session_start is not None else datetime.datetime.now()
        self.rect_size = rect_size
        self.rect_drawing = rect_drawing
        self.rect_trans = rect_trans
        self.events = events if events is not None else []
        self.retries = retries if retries is not None else []
        self.strokes = strokes

    def clear(self):
        if self.events:
            self.retries.append(self.events)
        self.events = []
        self.strokes = 0

    def append(self, event):
        self.events.append(event)
        if event.typ == QtCore.QEvent.TabletRelease:
            self.strokes += 1


class DrawingRecord(object):
    def __init__(self, oid, aid, drawing, calibration, calibration_age, recording, cycle,
                 pat_type, pat_hand_cnt, pat_handedness, pat_hand,
                 extra_data=None, comments=None, ts_created=None, ts_updated=None):
        self.oid = oid
        self.aid = aid
        self.drawing = drawing
        self.calibration = calibration
        self.calibration_age = calibration_age
        self.recording = recording
        self.cycle = cycle
        self.pat_type = pat_type
        self.pat_hand_cnt = pat_hand_cnt
        self.pat_handedness = pat_handedness
        self.pat_hand = pat_hand
        self.extra_data = extra_data if extra_data is not None else {}
        self.comments = comments
        self.ts_created = ts_created if ts_created is not None else datetime.datetime.now()
        self.ts_updated = ts_updated if ts_updated is not None else copy(self.ts_created)


    def check_warnings(self):
        ret = []

        if self.recording.strokes > 1:
            ret.append(translate("data", "Multiple strokes"))

        if not self.recording.events:
            ret.append(translate("data", "No data!"))
        else:
            length = (self.recording.events[-1].stamp -
                      self.recording.events[0].stamp)
            if length < datetime.timedelta(seconds=1) or \
              len(self.recording.events) < 100:
                ret.append(translate("data", "Short recording"))

        stamp = datetime.datetime.now()
        if (stamp - self.calibration.stamp) > datetime.timedelta(hours=8) or \
          self.calibration_age > 50:
            ret.append(translate("data", "Old calibration data"))

        return ret


    @classmethod
    def dump(cls, record, path):
        with open(path, 'wb') as fd:
            cPickle.dump(record, fd, cPickle.HIGHEST_PROTOCOL)


    @classmethod
    def save(cls, record, path):
        # basic data to save
        data = {"format": Consts.FORMAT_VERSION,
                "type": Consts.FF_RECORDING,
                "version": Consts.APP_VERSION,
                "operator": record.oid,
                "aid": record.aid,
                "drawing": {
                    "id": record.drawing.id,
                    "str": record.drawing.str,
                    "points": map(list, record.drawing.points),
                    "cpoints": map(list, record.drawing.cpoints)},
                "calibration": {
                    "operator": record.calibration.oid,
                    "tablet_id": record.calibration.tablet_id,
                    "stylus_id": record.calibration.stylus_id,
                    "stamp": record.calibration.stamp,
                    "cpoints": map(list, record.calibration.cpoints)},
                "calibration_age": record.calibration_age,
                "recording": {
                    "session_start": record.recording.session_start,
                    "rect_size": list(record.recording.rect_size),
                    "rect_drawing": map(list, record.recording.rect_drawing),
                    "rect_trans": map(list, record.recording.rect_trans),
                    "events": map(RecordingEvent.serialize, record.recording.events),
                    "retries": len(record.recording.retries) + 1,
                    "retries_events": [map(RecordingEvent.serialize, el) for el in record.recording.retries],
                    "strokes": record.recording.strokes},
                "cycle": record.cycle,
                "pat_type": record.pat_type,
                "pat_hand_cnt": record.pat_hand_cnt,
                "pat_handedness": _from_type(PAT_HANDEDNESS, record.pat_handedness),
                "pat_hand": _from_type(PAT_HAND, record.pat_hand),
                "extra_data": record.extra_data,
                "comments": record.comments,
                "ts_created": record.ts_created,
                "ts_updated": record.ts_updated}

        # avoid saving unicode in the FNAME header
        fd = gzip.GzipFile(record.aid, 'wb', fileobj=open(path, 'wb', 0))

        # dump
        yaml.safe_dump(data, fd, allow_unicode=True, encoding='utf-8')


    @classmethod
    def save_text(cls, record, path):
        with open(path, "w") as fd:
            print('\t'.join(["#TIME", "X", "Y", "Z", "W", "T"]), file=fd)
            start = record.recording.events[0].stamp
            for event in record.recording.events:
                time = (event.stamp - start).total_seconds() * 1000.;
                x = event.coords_drawing[0]
                y = event.coords_drawing[1]
                z = event.pressure if pressure != 0 else ""
                w = event.tilt_drawing[0] if event.tilt_drawing else ""
                t = event.tilt_drawing[1] if event.tilt_drawing else ""
                print('\t'.join(map(str, [time, x, y, z, w, t])), file=fd)


    @classmethod
    def load(cls, path, fast=False):
        # fast loading
        if fast:
            with open(path, "rb") as fd:
                try:
                    return cPickle.load(fd)
                except cPickle.UnpicklingError:
                    pass

        # normal (safe) fallback
        data = None
        try:
            fd = gzip.GzipFile(path, 'rb')
            data = yaml.safe_load(fd)
        except IOError:
            raise
        except:
            pass

        # check version info
        if not data or 'format' not in data or \
          type(data['format']) != str or \
          int(float(data['format'])) != 1 or \
          data.get('type', Consts.FF_RECORDING) != Consts.FF_RECORDING:
            msg = translate("data", 'Unsupported file format')
            raise Exception(msg, path)

        # recover extra data
        extra_data = data['extra_data']
        extra_data['format'] = data['format']
        extra_data['version'] = data['version']
        extra_data['type'] = data.get('type') # optional (fmt 1.2)

        # drawing
        drawing = Drawing.Drawing(data['drawing']['id'],
                                  data['drawing']['str'],
                                  map(tuple, data['drawing']['points']),
                                  map(tuple, data['drawing']['cpoints']))

        # calibration
        calibration = CalibrationData(data['calibration'].get('operator'), # optional (fmt 1.2)
                                      data['calibration']['tablet_id'],
                                      data['calibration'].get('stylus_id'), # optional (fmt 1.2)
                                      map(tuple, data['calibration']['cpoints']),
                                      data['calibration']['stamp'])

        # past retries (optional, fmt 1.2)
        retries_events = data['recording'].get('retries_events')
        if retries_events is None:
            retries_events = [[]] * (data['recording']['retries'] - 1)
        else:
            retries_events = [map(RecordingEvent.deserialize, el) for el in retries_events]

        # recording
        recording = RecordingData(data['recording']['session_start'],
                                  tuple(data['recording']['rect_size']),
                                  map(tuple, data['recording']['rect_drawing']),
                                  map(tuple, data['recording']['rect_trans']),
                                  map(RecordingEvent.deserialize, data['recording']['events']),
                                  retries_events, data['recording']['strokes'])

        # timestamps (optional, fmt 1.3)
        ts_created = data.get('ts_created')
        if ts_created is None:
            ts_created = copy(recording.events[-1].stamp) if recording.events else copy(calibration.stamp)
        ts_updated = data.get('ts_updated')

        # operator (moved, fmt 1.3)
        oid = data['recording'].get('operator')
        if oid is None and 'operator' in extra_data:
            oid = extra_data['operator']
            del(extra_data['operator'])

        # final object
        return DrawingRecord(oid, data['aid'], drawing, calibration,
                             data['calibration_age'], recording,
                             data.get('cycle', 1), # optional (fmt 1.2)
                             data['pat_type'],
                             data.get('pat_hand_cnt'), # optional (fmt 1.2)
                             _to_type(PAT_HANDEDNESS, data['pat_handedness']),
                             _to_type(PAT_HAND, data['pat_hand']),
                             extra_data, data['comments'],
                             ts_created, ts_updated)


# Stylus profile data
class StylusResponseData(object):
    def __init__(self, pressure=None, weight=None):
        self.pressure = pressure
        self.weight = weight

    @classmethod
    def serialize(cls, data):
        return {'press': data.pressure, 'weight': data.weight}

    @classmethod
    def deserialize(cls, data):
        return StylusResponseData(data['press'], data['weight'])


class StylusProfile(object):
    def __init__(self, ts_created=None, ts_updated=None, oid=None, sid=None, tid=None,
                 data=None, fit=None, extra_data=None):
        self.ts_created = ts_created if ts_created is not None else datetime.datetime.now()
        self.ts_updated = ts_updated if ts_updated is not None else copy(self.ts_created)
        self.oid = oid
        self.sid = sid
        self.tid = tid
        self.data = data if data is not None else []
        self.fit = fit if fit is not None else []
        self.extra_data = extra_data if extra_data is not None else {}


    @classmethod
    def save(cls, profile, path):
        # basic data to save
        data = {"format": Consts.FORMAT_VERSION,
                "type": Consts.FF_PROFILE,
                "version": Consts.APP_VERSION,
                "ts_created": profile.ts_created,
                "ts_updated": profile.ts_updated,
                "operator": profile.oid,
                "stylus_id": profile.sid,
                "tablet_id": profile.tid,
                "data": map(StylusResponseData.serialize, profile.data),
                "fit": profile.fit[0].tolist(),
                "extra_data": profile.extra_data}

        # avoid saving unicode in the FNAME header
        fd = gzip.GzipFile(profile.sid, 'wb', fileobj=open(path, 'wb', 0))

        # dump
        yaml.safe_dump(data, fd, allow_unicode=True, encoding='utf-8')


    @classmethod
    def save_text(cls, profile, path):
        with open(path, "w") as fd:
            print('\t'.join(["#P", "W"]), file=fd)
            for point in profile.data:
                print('\t'.join(map(str, [point.pressure, point.weight])), file=fd)


    @classmethod
    def load(cls, path):
        data = None
        try:
            fd = gzip.GzipFile(path, 'rb')
            data = yaml.safe_load(fd)
        except IOError:
            raise
        except:
            pass

        # check version info
        if not data or 'format' not in data or \
          type(data['format']) != str or \
          int(float(data['format'])) != 1 or \
          data.get('type', Consts.FF_PROFILE) != Consts.FF_PROFILE:
            msg = translate("data", 'Unsupported file format')
            raise Exception(msg, path)

        # recover extra data
        extra_data = data['extra_data']
        extra_data['format'] = data['format']
        extra_data['version'] = data['version']
        extra_data['type'] = data['type']

        # final object
        return StylusProfile(data['ts_created'], data['ts_updated'],
                             data['operator'], data['stylus_id'], data['tablet_id'],
                             map(StylusResponseData.deserialize, data['data']),
                             (np.asarray(data['fit'])), extra_data)
