# -*- coding: utf-8 -*-
"""Data structures/serialization support"""

from __future__ import print_function

# local modules
from . import Consts
from . import Drawing
from . import RxUtil
from . import Tab
from .Shared import dtts, tsdt, strdt
from .UI import translate

# system modules
from PyQt4 import QtCore
from copy import copy
import cPickle
import collections
import datetime
import gzip
import json
import numpy as np
import time
import yaml


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

def _ts_loads(obj_or_str):
    if obj_or_str is None or isinstance(obj_or_str, datetime.datetime):
        return obj_or_str
    return datetime.datetime.strptime(obj_or_str, "%Y-%m-%d %H:%M:%S.%f")

def _ts_dumps(obj):
    if obj is None: return None
    return obj.strftime("%Y-%m-%d %H:%M:%S.%f")


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


# Configuration
class Config(object):
    def __init__(self, project_id=None, project_name=None, pat_types=None,
                 allow_no_pat_type=True, require_change_comments=True, cycle_count=3):
        self.project_id = project_id
        self.project_name = project_name
        self.pat_types = pat_types if pat_types is not None else {}
        self.allow_no_pat_type = allow_no_pat_type
        self.require_change_comments = require_change_comments
        self.cycle_count = cycle_count

    @classmethod
    def serialize(cls, data):
        return {'project_id': data.project_id,
                'project_name': data.project_name,
                'pat_types': data.pat_types,
                'allow_no_pat_type': data.allow_no_pat_type,
                'require_change_comments': data.require_change_comments,
                'cycle_count': data.cycle_count}

    @classmethod
    def deserialize(cls, data):
        return Config(data['project_id'], data['project_name'], data['pat_types'],
                      data['allow_no_pat_type'], data.get('require_change_comments', False),
                      data['cycle_count'])

    @classmethod
    def load(cls, path):
        obj = Config()
        data = RxUtil.load_yaml('config', path)
        if data is None:
            msg = translate('data', 'Malformed configuration file')
            raise Exception(msg, path)

        types = data['PAT_TYPES']
        if isinstance(types, dict):
            obj.pat_types = types
        else:
            obj.pat_types = dict(zip(types, types))

        obj.project_id = data['PROJECT_ID']
        obj.project_name = data['PROJECT_NAME']
        obj.allow_no_pat_type = data['ALLOW_NO_PAT_TYPE']
        obj.require_change_comments = data['REQUIRE_CHANGE_COMMENTS']
        obj.cycle_count = data['CYCLE_COUNT']
        return obj


# Calibration/Recording data
class CalibrationData(object):
    def __init__(self, oid, tablet_id, stylus_id, cpoints, ctilts, stamp=None):
        self.oid = oid
        self.tablet_id = tablet_id
        self.stylus_id = stylus_id
        self.cpoints = cpoints
        self.ctilts = ctilts
        self.stamp = stamp if stamp is not None else datetime.datetime.now()


class RecordingEvent(object):
    def __init__(self, typ, coords_drawing, coords_trans, pressure,
                 tilt_drawing, tilt_trans, stamp):
        self.typ = typ
        self.coords_drawing = coords_drawing
        self.coords_trans = coords_trans
        self.pressure = pressure
        self.tilt_drawing = tilt_drawing
        self.tilt_trans = tilt_trans
        self.stamp = stamp


    @classmethod
    def serialize(cls, event):
        data =  {'stamp': _ts_dumps(event.stamp),
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
        stamp = _ts_loads(event['stamp'])

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
    def __init__(self, config, oid, aid, drawing, calibration, calibration_age, recording,
                 cycle, pat_type, pat_hand_cnt, pat_handedness, pat_hand, extra_data=None,
                 comments=None, ts_created=None, ts_updated=None, tz=None):
        self.config = config
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
        self.ts_updated = ts_updated if ts_created is not None else copy(self.ts_created)
        self.tz = tz if ts_created is not None else -time.timezone


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
            record._type = Consts.FF_RECORDING
            record._format = Consts.FORMAT_VERSION
            record._version = Consts.APP_VERSION
            cPickle.dump(record, fd, cPickle.HIGHEST_PROTOCOL)


    @classmethod
    def save(cls, record, path):
        # original format/version
        for k in ['format', 'version']:
            if k in record.extra_data:
                if 'orig' not in record.extra_data:
                    record.extra_data['orig'] = {}
                if k not in record.extra_data['orig']:
                    record.extra_data['orig'][k] = record.extra_data[k]
                del record.extra_data[k]

        # basic data to save
        data = {"format": Consts.FORMAT_VERSION,
                "type": Consts.FF_RECORDING,
                "version": Consts.APP_VERSION,
                "config": Config.serialize(record.config),
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
                    "stamp": _ts_dumps(record.calibration.stamp),
                    "cpoints": map(list, record.calibration.cpoints),
                    "ctilts": map(list, record.calibration.ctilts)},
                "calibration_age": record.calibration_age,
                "recording": {
                    "session_start": _ts_dumps(record.recording.session_start),
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
                "ts_created": _ts_dumps(record.ts_created),
                "ts_updated": _ts_dumps(record.ts_updated),
                "tz": record.tz}

        # avoid saving unicode in the FNAME header
        fd = gzip.GzipFile(record.aid, 'wb', fileobj=open(path, 'wb', 0))
        buf = json.dumps(data, ensure_ascii=False, check_circular=False)
        fd.write(buf.encode('utf-8'))


    @classmethod
    def save_text(cls, record, path):
        fd = Tab.TabWriter(path, ["TIME", "X", "Y", "Z", "W", "T"])
        start = record.recording.events[0].stamp
        for event in record.recording.events:
            fd.write({'TIME': (event.stamp - start).total_seconds() * 1000.,
                      'X': event.coords_drawing[0],
                      'Y': event.coords_drawing[1],
                      'Z': event.pressure,
                      'W': event.tilt_drawing[0] if event.tilt_drawing else None,
                      'T': event.tilt_drawing[1] if event.tilt_drawing else None})


    @classmethod
    def load(cls, path, fast=False):
        # fast loading
        if fast:
            with open(path, "rb") as fd:
                try:
                    data = cPickle.load(fd)
                    if data._type != Consts.FF_RECORDING or \
                       data._format != Consts.FORMAT_VERSION or \
                       data._version != Consts.APP_VERSION:
                        raise Exception('Cannot load dump file produced by a different software version)', path)
                    return data
                except cPickle.UnpicklingError:
                    pass

        # normal (safe) fallback
        data = None
        try:
            fd = gzip.GzipFile(path, 'rb')
            # JSON (DR 1.6)
            hdr = fd.read(1)
            fd.seek(0)
            buf = fd.read().decode('utf-8')
            data = json.loads(buf) if hdr == '{' else yaml.safe_load(buf)
        except IOError:
            raise
        except:
            pass

        # check version info
        if not data or 'format' not in data or \
          not isinstance(data['format'], basestring) or \
          int(float(data['format'])) != 1 or \
          data.get('type', Consts.FF_RECORDING) != Consts.FF_RECORDING:
            msg = translate("data", 'Unsupported file format')
            raise Exception(msg, path)

        # recover extra data
        extra_data = data['extra_data']
        extra_data['format'] = data['format']
        extra_data['version'] = data['version']

        # original data (optional, moved in fmt 1.4)
        for old_k, new_k in [('orig_format', 'format'),
                             ('orig_version', 'version'),
                             ('pat_type', 'pat_type_id')]:
            if old_k in extra_data:
                if 'orig' not in extra_data:
                    extra_data['orig'] = {}
                old_v = extra_data.pop(old_k)
                if new_k not in extra_data['orig']:
                    extra_data['orig'][new_k] = old_v

        # drawing
        drawing = Drawing.Drawing(data['drawing']['id'],
                                  data['drawing']['str'],
                                  map(tuple, data['drawing']['points']),
                                  map(tuple, data['drawing']['cpoints']))

        # calibration
        cpoints = map(tuple, data['calibration']['cpoints'])
        ctilts = data['calibration'].get('ctilts') # optional (fmt 1.3)
        if ctilts is None:
            ctilts = [(0, 0)] * len(cpoints)
        else:
            ctilts = map(tuple, ctilts)

        calibration = CalibrationData(data['calibration'].get('operator'), # optional (fmt 1.2)
                                      data['calibration']['tablet_id'],
                                      data['calibration'].get('stylus_id'), # optional (fmt 1.2)
                                      cpoints, ctilts, _ts_loads(data['calibration']['stamp']))

        # past retries (optional, fmt 1.2)
        retries_events = data['recording'].get('retries_events')
        if retries_events is None:
            retries_events = [[]] * (data['recording']['retries'] - 1)
        else:
            retries_events = [map(RecordingEvent.deserialize, el) for el in retries_events]

        # recording
        recording = RecordingData(_ts_loads(data['recording']['session_start']),
                                  tuple(data['recording']['rect_size']),
                                  map(tuple, data['recording']['rect_drawing']),
                                  map(tuple, data['recording']['rect_trans']),
                                  map(RecordingEvent.deserialize, data['recording']['events']),
                                  retries_events, data['recording']['strokes'])

        # timestamps (optional, fmt 1.3)
        ts_created = _ts_loads(data.get('ts_created'))
        if ts_created is None:
            ts_created = copy(recording.events[-1].stamp) if recording.events else copy(calibration.stamp)
        ts_updated = _ts_loads(data.get('ts_updated'))
        if ts_updated is None:
            ts_updated = copy(ts_created)

        # timezone (optional, fmt 1.4)
        tz = data.get('tz')

        # operator (moved, fmt 1.3)
        oid = data.get('operator')
        if oid is None and 'operator' in extra_data:
            oid = extra_data.pop('operator')

        # project configuration (optional, fmt 1.3)
        config = data.get('config')
        if config is not None:
            config = Config.deserialize(config)
        else:
            config = Config()

        # final object
        return DrawingRecord(config, oid, data['aid'], drawing, calibration,
                             data['calibration_age'], recording,
                             data.get('cycle', 1), # optional (fmt 1.2)
                             data['pat_type'],
                             data.get('pat_hand_cnt'), # optional (fmt 1.2)
                             _to_type(PAT_HANDEDNESS, data['pat_handedness']),
                             _to_type(PAT_HAND, data['pat_hand']),
                             extra_data, data['comments'],
                             ts_created, ts_updated, tz)



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
                 data=None, fit=None, extra_data=None, tz=None):
        self.ts_created = ts_created if ts_created is not None else datetime.datetime.now()
        self.ts_updated = ts_updated if ts_created is not None else copy(self.ts_created)
        self.oid = oid
        self.sid = sid
        self.tid = tid
        self.data = data if data is not None else []
        self.fit = fit if fit is not None else []
        self.extra_data = extra_data if extra_data is not None else {}
        self.tz = tz if ts_created is not None else -time.timezone


    @classmethod
    def save(cls, profile, path):
        # basic data to save
        data = {"format": Consts.FORMAT_VERSION,
                "type": Consts.FF_PROFILE,
                "version": Consts.APP_VERSION,
                "ts_created": _ts_dumps(profile.ts_created),
                "ts_updated": _ts_dumps(profile.ts_updated),
                "operator": profile.oid,
                "stylus_id": profile.sid,
                "tablet_id": profile.tid,
                "data": map(StylusResponseData.serialize, profile.data),
                "fit": profile.fit[0].tolist() if profile.fit is not None else None,
                "extra_data": profile.extra_data,
                "tz": profile.tz}

        # avoid saving unicode in the FNAME header
        fd = gzip.GzipFile(profile.sid, 'wb', fileobj=open(path, 'wb', 0))
        buf = json.dumps(data, ensure_ascii=False, check_circular=False)
        fd.write(buf.encode('utf-8'))


    @classmethod
    def save_text(cls, profile, path):
        fd = Tab.TabWriter(path, ["P", "W"])
        for point in profile.data:
            fd.write({'P': point.pressure,
                      'W': point.weight})


    @classmethod
    def load(cls, path):
        data = None
        try:
            fd = gzip.GzipFile(path, 'rb')
            # JSON (DR 1.6)
            hdr = fd.read(1)
            fd.seek(0)
            buf = fd.read().decode('utf-8')
            data = json.loads(buf) if hdr == '{' else yaml.safe_load(buf)
        except IOError:
            raise
        except:
            pass

        # check version info
        if not data or 'format' not in data or \
          not isinstance(data['format'], basestring) or \
          int(float(data['format'])) != 1 or \
          data.get('type', Consts.FF_PROFILE) != Consts.FF_PROFILE:
            msg = translate("data", 'Unsupported file format')
            raise Exception(msg, path)

        # recover extra data
        extra_data = data['extra_data']
        extra_data['format'] = data['format']
        extra_data['version'] = data['version']

        # timezone (optional, fmt 1.4)
        tz = data.get('tz')

        # response fit (without residuals)
        fit = [np.asarray(data['fit']), None]

        # final object
        return StylusProfile(_ts_loads(data['ts_created']), _ts_loads(data['ts_updated']),
                             data['operator'], data['stylus_id'], data['tablet_id'],
                             map(StylusResponseData.deserialize, data['data']),
                             fit, extra_data, tz)



# Stylus usage data
class StylusUsageMark(object):
    def __init__(self, stamp, count):
        self.stamp = stamp
        self.count = count


class StylusUsageReport(object):
    def __init__(self, sur):
        self.sur = sur

    def get(self, sid):
        return self.sur.get(sid)

    @classmethod
    def save(cls, data, path):
        fd = Tab.TabWriter(path, ['SID', 'DATE', 'COUNT'])
        for sid, marks in data.sur.iteritems():
            for mark in marks:
                fd.write({'SID': sid,
                          'DATE': mark.stamp,
                          'COUNT': mark.count})

    @classmethod
    def load(cls, path):
        fd = Tab.TabReader(path, ['SID', 'DATE', 'COUNT'],
                           types={'DATE': strdt, 'COUNT': int})
        sur = collections.defaultdict(list)
        for row in fd:
            mark = StylusUsageMark(row['DATE'], row['COUNT'])
            sur[row['SID']].append(mark)

        return StylusUsageReport(sur)
