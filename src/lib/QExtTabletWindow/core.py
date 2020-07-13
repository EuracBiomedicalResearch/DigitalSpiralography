# -*- coding: utf-8 -*-
from __future__ import print_function
from PyQt5 import QtCore

EVENT_TYPE = QtCore.QEvent.registerEventType()

class EventSubtypes(object):
    MOVE = QtCore.QEvent.TabletMove
    PRESS = QtCore.QEvent.TabletPress
    RELEASE = QtCore.QEvent.TabletRelease
    ENTER = QtCore.QEvent.TabletEnterProximity
    LEAVE = QtCore.QEvent.TabletLeaveProximity

class QExtTabletException(Exception):
    def __init__(self, *args, **kwargs):
        super(QExtTabletException, self).__init__(*args, **kwargs)

class QExtTabletEvent(QtCore.QEvent):
    def __init__(self, subtype, os_stamp, dev_stamp, dev_serial,
                 pressure, position, tilt):
        super(QExtTabletEvent, self).__init__(EVENT_TYPE)
        self.subtype = subtype
        self.os_stamp = os_stamp
        self.dev_stamp = dev_stamp
        self.dev_serial = dev_serial
        self.pressure = pressure
        self.position = position
        self.tilt = tilt
