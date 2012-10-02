# -*- coding: utf-8 -*-
"""Drawing record/analysis"""

import datetime
import yaml
import gzip
from PyQt4 import QtCore


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
                 recording, extra_data={}, comments=None):
        self.aid = aid
        self.drawing = drawing
        self.calibration = calibration
        self.calibration_age = calibration_age
        self.recording = recording
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


    def save(self, path):
        # translate the event stream
        events = []
        for event in self.recording.events:
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
        data = {"aid": self.aid,
                "drawing": {
                    "str": self.drawing.describe(),
                    "points": map(list, self.drawing.points),
                    "cpoints": map(list, self.drawing.cpoints)},
                "calibration": {
                    "stamp": self.calibration.stamp,
                    "cpoints": map(list, self.calibration.cpoints)},
                "calibration_age": self.calibration_age,
                "recording": {
                    "session_start": self.recording.session_start,
                    "events": events,
                    "retries": self.recording.retries,
                    "strokes": self.recording.strokes},
                "extra_data": self.extra_data,
                "comments": self.comments}

        # dump
        fd = gzip.GzipFile(path, 'wb')
        yaml.dump(data, fd, default_flow_style=False)
