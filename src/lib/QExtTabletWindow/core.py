# -*- coding: utf-8 -*-
from __future__ import print_function
from PyQt4 import QtCore

EVENT_TYPE = QtCore.QEvent.registerEventType()

class EventSubtypes(object):
    MOVE, PRESS, RELEASE, ENTER, LEAVE = range(5)

class QExtTabletEvent(QtCore.QEvent):
    def __init__(self, subtype, pressure):
        super(QExtTabletEvent, self).__init__(EVENT_TYPE)
        self.subtype = subtype
        self.pressure = pressure
