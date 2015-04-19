# -*- coding: utf-8 -*-
from __future__ import print_function
from PyQt4 import QtCore, QtGui

import HiResTime
from .core import EventSubtypes, QExtTabletEvent


class QExtTabletManager(QtCore.QObject):
    _instance = None
    _app = None
    _events = set([QtCore.QEvent.TabletEnterProximity,
                   QtCore.QEvent.TabletLeaveProximity,
                   QtCore.QEvent.TabletMove,
                   QtCore.QEvent.TabletPress,
                   QtCore.QEvent.TabletRelease])

    def __init__(self):
        super(QExtTabletManager, self).__init__()
        self._windows = set()
        self._app = QtCore.QCoreApplication.instance()
        self._app.installEventFilter(self)

    def eventFilter(self, receiver, event):
        if event.type() in self._events:
            event.accept()
            self.handleEvent(receiver, event)
            return True
        return False

    def translateEvent(self, event):
        return QExtTabletEvent(event.type(), HiResTime.now(), event.pressure(),
                               event.hiResGlobalPos(), (event.xTilt(), event.yTilt()))

    def handleEvent(self, receiver, event):
        win = self._app.activeWindow()
        if win and win in self._windows:
            ev = self.translateEvent(event)
            self._app.sendEvent(win, ev)

    @classmethod
    def register(cls, window):
        if cls._instance is None:
            cls._instance = QExtTabletManager()
        cls._instance._register(window)

    def _register(self, window):
        self._windows.add(window)


class QExtTabletWindow(QtGui.QMainWindow):
    def __init__(self):
        super(QExtTabletWindow, self).__init__()
        QExtTabletManager.register(self)
