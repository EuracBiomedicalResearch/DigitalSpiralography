# -*- coding: utf-8 -*-
"""Drawing structures/analysis"""

# local modules
import Consts

# system modules
import datetime
import yaml
import gzip
from PyQt4 import QtCore


# implementation
class CalibrationData:
    def __init__(self, cpoints, stamp=None):
        self.cpoints = cpoints
        self.stamp = stamp if stamp is not None else datetime.datetime.now()


class RecordingEvent:
    def __init__(self, typ, coords_drawing, coords_trans, pressure, stamp=None):
        self.typ = typ
        self.coords_drawing = coords_drawing
        self.coords_trans = coords_trans
        self.pressure = pressure
        self.stamp = stamp if stamp is not None else datetime.datetime.now()


class RecordingData:
    def __init__(self, session_start=None, events=None, retries=0, strokes=0):
        self.session_start = session_start if session_start is not None else datetime.datetime.now()
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
            ret.append("Multiple strokes")

        length = (self.recording.events[-1].stamp -
                  self.recording.events[0].stamp)
        if length < datetime.timedelta(seconds=1) or \
          len(self.recording.events) < 100:
            ret.append("Short recording")

        stamp = datetime.datetime.now()
        if (stamp - self.calibration.stamp) > datetime.timedelta(hours=8) or \
          self.calibration_age > 50:
            ret.append("Old calibration data")

        return ret


    def save(record, path):
        # translate the event stream
        events = []
        for event in record.recording.events:
            # event type
            if event.typ == QtCore.QEvent.TabletMove:
                typ = 'move'
            elif event.typ == QtCore.QEvent.TabletPress:
                typ = 'press'
            elif event.typ == QtCore.QEvent.TabletRelease:
                typ = 'release'
            elif event.typ == QtCore.QEvent.TabletEnterProximity:
                typ = 'enter'
            elif event.typ == QtCore.QEvent.TabletLeaveProximity:
                typ = 'leave'
            else:
                typ = event.typ

            # everything else
            buf = {'stamp': event.stamp,
                   'type': typ,
                   'cdraw': list(event.coords_drawing),
                   'ctrans': list(event.coords_trans),
                   'press': event.pressure}

            events.append(buf)

        # basic data to save
        data = {"format": Consts.FORMAT_VERSION,
                "version": Consts.APP_VERSION,
                "aid": record.aid,
                "drawing": {
                    "str": record.drawing.describe(),
                    "points": map(list, record.drawing.points),
                    "cpoints": map(list, record.drawing.cpoints)},
                "calibration": {
                    "stamp": record.calibration.stamp,
                    "cpoints": map(list, record.calibration.cpoints)},
                "calibration_age": record.calibration_age,
                "recording": {
                    "session_start": record.recording.session_start,
                    "events": events,
                    "retries": record.recording.retries,
                    "strokes": record.recording.strokes},
                "extra_data": record.extra_data,
                "pat_type": record.pat_type,
                "pat_handedness": record.pat_handedness,
                "pat_hand": record.pat_hand,
                "comments": record.comments}

        # dump
        fd = gzip.GzipFile(path, 'wb')
        yaml.dump(data, fd, default_flow_style=False)
