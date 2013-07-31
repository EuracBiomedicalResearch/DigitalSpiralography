# -*- coding: utf-8 -*-
"""Drawing structures/analysis"""

# local modules
import Consts
import Drawing
from Intl import translate

# system modules
import datetime
import yaml
import gzip
from PyQt4 import QtCore
import cPickle


# types
class PatType:
    case, control = range(2)


class PatHandedness:
    left, right, ambidextrous = range(3)


class PatHand:
    left, right = range(2)


class CalibrationData:
    def __init__(self, tablet_id, cpoints, stamp=None):
        self.tablet_id = tablet_id
        self.cpoints = cpoints
        self.stamp = stamp if stamp is not None else datetime.datetime.now()


class RecordingEvent:
    def __init__(self, typ, coords_drawing, coords_trans, pressure,
                 tilt_drawing, tilt_trans, stamp=None):
        self.typ = typ
        self.coords_drawing = coords_drawing
        self.coords_trans = coords_trans
        self.pressure = pressure
        self.tilt_drawing = tilt_drawing
        self.tilt_trans = tilt_trans
        self.stamp = stamp if stamp is not None else datetime.datetime.now()


class RecordingData:
    def __init__(self, session_start=None, rect_size=None, rect_drawing=None,
                 rect_trans=None, events=None, retries=0, strokes=0):
        self.session_start = session_start if session_start is not None else datetime.datetime.now()
        self.rect_size = rect_size
        self.rect_drawing = rect_drawing
        self.rect_trans = rect_trans
        self.events = events
        self.retries = retries
        self.strokes = strokes

    def clear(self):
        self.events = None
        self.retries += 1
        self.strokes = 0

    def append(self, event):
        self.events.append(event)
        if event.typ == QtCore.QEvent.TabletRelease:
            self.strokes += 1



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

PAT_TYPE = {PatType.case: 'Case',
            PatType.control: 'Control'}

PAT_TYPE_DSC = {PatType.case: translate('types', 'Case'),
                PatType.control: translate('types', 'Control')}

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


# implementation
class DrawingRecord:
    def __init__(self, aid, drawing, calibration, calibration_age,
                 recording, pat_type, pat_handedness, pat_hand,
                 extra_data={}, comments=None):
        self.aid = aid
        self.drawing = drawing
        self.calibration = calibration
        self.calibration_age = calibration_age
        self.recording = recording
        self.pat_type = pat_type
        self.pat_handedness = pat_handedness
        self.pat_hand = pat_hand
        self.extra_data = extra_data
        self.comments = comments


    def check_warnings(self):
        ret = []

        if self.recording.strokes > 1:
            ret.append(translate("analysis", "Multiple strokes"))

        if not self.recording.events:
            ret.append(translate("analysis", "No data!"))
        else:
            length = (self.recording.events[-1].stamp -
                      self.recording.events[0].stamp)
            if length < datetime.timedelta(seconds=1) or \
              len(self.recording.events) < 100:
                ret.append(translate("analysis", "Short recording"))

        stamp = datetime.datetime.now()
        if (stamp - self.calibration.stamp) > datetime.timedelta(hours=8) or \
          self.calibration_age > 50:
            ret.append(translate("analysis", "Old calibration data"))

        return ret


    @classmethod
    def dump(cls, record, path):
        with open(path, 'wb') as fd:
            cPickle.dump(record, fd, cPickle.HIGHEST_PROTOCOL)


    @classmethod
    def save(cls, record, path):
        # translate the event stream
        events = []
        for event in record.recording.events:
            buf = {'stamp': event.stamp,
                   'type': _from_type(EVENT_MAP, event.typ),
                   'cdraw': list(event.coords_drawing),
                   'ctrans': list(event.coords_trans),
                   'press': event.pressure,
                   'tdraw': list(event.tilt_drawing),
                   'ttrans': list(event.tilt_trans)}
            events.append(buf)

        # basic data to save
        data = {"format": Consts.FORMAT_VERSION,
                "version": Consts.APP_VERSION,
                "aid": record.aid,
                "drawing": {
                    "id": record.drawing.id,
                    "str": record.drawing.str,
                    "points": map(list, record.drawing.points),
                    "cpoints": map(list, record.drawing.cpoints)},
                "calibration": {
                    "tablet_id": record.calibration.tablet_id,
                    "stamp": record.calibration.stamp,
                    "cpoints": map(list, record.calibration.cpoints)},
                "calibration_age": record.calibration_age,
                "recording": {
                    "session_start": record.recording.session_start,
                    "rect_size": list(record.recording.rect_size),
                    "rect_drawing": map(list, record.recording.rect_drawing),
                    "rect_trans": map(list, record.recording.rect_trans),
                    "events": events,
                    "retries": record.recording.retries,
                    "strokes": record.recording.strokes},
                "extra_data": record.extra_data,
                "pat_type": _from_type(PAT_TYPE, record.pat_type),
                "pat_handedness": _from_type(PAT_HANDEDNESS, record.pat_handedness),
                "pat_hand": _from_type(PAT_HAND, record.pat_hand),
                "comments": record.comments}

        # avoid saving unicode in the FNAME header
        fd = gzip.GzipFile(record.aid, 'wb', fileobj=open(path, 'wb', 0))

        # dump
        yaml.safe_dump(data, fd, default_flow_style=False,
                       allow_unicode=True, encoding='utf-8')


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
        except:
            pass

        # check version info
        if not data or 'format' not in data or \
          type(data['format']) != str or \
          int(float(data['format'])) != 1:
            msg = translate("analysis", 'Invalid or unsupported file format')
            raise Exception(msg, path)

        # recover extra data
        extra_data = data['extra_data']
        extra_data['format'] = data['format']
        extra_data['version'] = data['version']

        # drawing
        drawing = Drawing.Drawing(data['drawing']['id'],
                                  data['drawing']['str'],
                                  map(tuple, data['drawing']['points']),
                                  map(tuple, data['drawing']['cpoints']))

        # calibration
        calibration = CalibrationData(data['calibration']['tablet_id'],
                                      map(tuple, data['calibration']['cpoints']),
                                      data['calibration']['stamp'])

        # event stream
        events = []
        for event in data['recording']['events']:
            # optional elements (format 1.1)
            tilt_drawing = event.get('tdraw')
            tilt_trans = event.get('ttrans')
            if tilt_drawing is not None:
                tilt_drawing = tuple(tilt_drawing)
                tilt_trans = tuple(tilt_trans)

            # everything else
            events.append(RecordingEvent(_to_type(EVENT_MAP, event['type']),
                                         tuple(event['cdraw']), tuple(event['ctrans']),
                                         event['press'], tilt_drawing, tilt_trans, event['stamp']))

        # recording
        recording = RecordingData(data['recording']['session_start'],
                                  tuple(data['recording']['rect_size']),
                                  map(tuple, data['recording']['rect_drawing']),
                                  map(tuple, data['recording']['rect_trans']),
                                  events,
                                  data['recording']['retries'],
                                  data['recording']['strokes'])

        # final object
        return DrawingRecord(data['aid'], drawing, calibration,
                             data['calibration_age'], recording,
                             _to_type(PAT_TYPE, data['pat_type']),
                             _to_type(PAT_HANDEDNESS, data['pat_handedness']),
                             _to_type(PAT_HAND, data['pat_hand']),
                             extra_data, data['comments'])
