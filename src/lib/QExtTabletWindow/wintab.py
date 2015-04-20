# -*- coding: utf-8 -*-
from __future__ import print_function
from PyQt4 import QtCore, QtGui

import math
from math import sin, cos, tan, atan

import HiResTime
from .core import EventSubtypes, QExtTabletException, QExtTabletEvent

import libwintab, ctypes
from libwintab import lib, wtinfo


# Constants
WT_PACKET = libwintab.WT_DEFBASE + libwintab.WT_PACKET
WT_CSRCHANGE = libwintab.WT_DEFBASE + libwintab.WT_CSRCHANGE
WT_PROXIMITY = libwintab.WT_DEFBASE + libwintab.WT_PROXIMITY

CSR_TYPE_MAP = {
    libwintab.CSR_TYPE_STYLUS: QtGui.QTabletEvent.Stylus,
    libwintab.CSR_TYPE_AIRBRUSH: QtGui.QTabletEvent.Airbrush,
    libwintab.CSR_TYPE_ARTPEN: QtGui.QTabletEvent.RotationStylus,
    libwintab.CSR_TYPE_4DMOUSE: QtGui.QTabletEvent.FourDMouse,
    libwintab.CSR_TYPE_PUCK: QtGui.QTabletEvent.Puck,
}

CSR_POINTER_MAP = {
    0: QtGui.QTabletEvent.Cursor,
    1: QtGui.QTabletEvent.Pen,
    2: QtGui.QTabletEvent.Eraser,
}


# Ensure WINTAB is installed/available/recent-enough
spec = wtinfo(libwintab.WTI_INTERFACE, libwintab.IFC_SPECVERSION, libwintab.WORD())
if spec < 0x102:
    raise QExtTabletException("WINTAB < 1.2")


# Low-level handler
class QExtTabletManager(QtCore.QObject):
    _instance = None
    _ctxs = None

    def __init__(self):
        super(QExtTabletManager, self).__init__()
        self._ctxs = {}
        QtCore.QAbstractEventDispatcher.instance().setEventFilter(lambda x: self.eventFilter(x))

    def eventFilter(self, msg):
        if msg.message == WT_PACKET or \
           msg.message == WT_CSRCHANGE or \
            msg.message == WT_PROXIMITY:
            ctx = msg.lParam if msg.message != WT_PROXIMITY else msg.wParam
            if ctx in self._ctxs:
                self._ctxs[ctx].handleMsg(msg)
                return True
        return False

    @classmethod
    def register(cls, ctx):
        if cls._instance is None:
            cls._instance = QExtTabletManager()
        cls._instance._register(ctx)

    def _register(self, ctx):
        self._ctxs[ctx.ctx] = ctx

    @classmethod
    def unregister(cls, ctx):
        del cls._instance._ctxs[ctx.ctx]


class QExtCursorData(object):
    def __init__(self, device_idx, cursor_n):
        self.device_idx = device_idx
        self.cursor_idx = libwintab.WTI_CURSORS + cursor_n
        self.name = wtinfo(self.cursor_idx, libwintab.CSR_NAME, unicode)
        self.active = wtinfo(self.cursor_idx, libwintab.CSR_ACTIVE, libwintab.BOOL())
        self.pktdata = wtinfo(self.cursor_idx, libwintab.CSR_PKTDATA, libwintab.WTPKT())
        csr_type = wtinfo(self.cursor_idx, libwintab.CSR_TYPE, libwintab.UINT())
        csr_physid = wtinfo(self.cursor_idx, libwintab.CSR_PHYSID, libwintab.DWORD())

        # cursor_uid is unique to the cursor (which differentiates between pen/eraser/color)
        self.cursor_uid = (csr_type << 32) | csr_physid

        # type_uid is the physical device type only (does not differentiate
        # color or pointer) and is the same as QT's "uniqueId".
        self.type_uid = ((csr_type & 0xFF6) << 32) | csr_physid

        csr_masked = csr_type & libwintab.CSR_TYPE_MASK
        if (csr_type & 0x0006) == 0x0002 and csr_masked != 0x0902:
            self.type = QtGui.QTabletEvent.Stylus
        else:
            self.type = CSR_TYPE_MAP.get(csr_masked, QtGui.QTabletEvent.NoDevice)
        self.pointer = CSR_POINTER_MAP.get(cursor_n % 3, QtGui.QTabletEvent.UnknownPointer)


class QExtTabletContext(object):
    def __init__(self, window, device_n):
        self.window = window
        self._app = QtCore.QCoreApplication.instance()
        self.cursors = {}

        # Initialize a new wintab context
        devices = wtinfo(libwintab.WTI_INTERFACE, libwintab.IFC_NDEVICES, libwintab.UINT())
        if devices <= device_n:
            raise QExtTabletException("Invalid tablet device: {}".format(device_n))

        # Device ID
        self.device_idx = libwintab.WTI_DEVICES + device_n
        self.device_name = wtinfo(self.device_idx, libwintab.DVC_NAME, unicode)
        self.device_uid = wtinfo(self.device_idx, libwintab.DVC_PNPID, unicode)

        # Axis
        self.np_axis = wtinfo(self.device_idx, libwintab.DVC_NPRESSURE, libwintab.AXIS())
        self.or_axis = wtinfo(self.device_idx, libwintab.DVC_ORIENTATION, (libwintab.AXIS * 3)())
        self.x_axis = wtinfo(self.device_idx, libwintab.DVC_X, libwintab.AXIS())
        self.y_axis = wtinfo(self.device_idx, libwintab.DVC_Y, libwintab.AXIS())

        # Create context
        self.ctx_data = libwintab.LOGCONTEXT()
        wtinfo(libwintab.WTI_DEFCONTEXT, 0, self.ctx_data)
        self.ctx_data.lcMsgBase = libwintab.WT_DEFBASE
        self.ctx_data.lcOptions |= libwintab.CXO_MESSAGES | libwintab.CXO_CSRMESSAGES
        self.ctx_data.lcPktData = libwintab.PKT_FIELDS
        self.ctx_data.lcPktMode = 0
        self.ctx_data.lcMoveMask = libwintab.PKT_FIELDS
        self.ctx_data.lcOutOrgX = self.ctx_data.lcOutOrgY = self.ctx_data.lcOutOrgZ = 0
        self.ctx_data.lcOutExtX = self.ctx_data.lcInExtX
        self.ctx_data.lcOutExtY = self.ctx_data.lcInExtY
        self.ctx_data.lcOutExtZ = self.ctx_data.lcInExtZ

        self.ctx = lib.WTOpenW(int(window.winId()), ctypes.byref(self.ctx_data), True)
        if not self.ctx:
            raise QExtTabletException("Couldn't open tablet context")


    def activate(self):
        lib.WTEnable(self.ctx, True)
        lib.WTOverlap(self.ctx, True)

    def __del__(self):
        lib.WTClose(self.ctx)


    def handleMsg(self, msg):
        now = HiResTime.now()

        if msg.message == WT_PROXIMITY:
            subtype = EventSubtypes.ENTER if (msg.lParam & 0xFF) else EventSubtypes.LEAVE
            ev = QExtTabletEvent(subtype, now, None, None, 0., QtCore.QPointF(), (0., 0.))
            self.window.event(ev)

        # process any available packet, irregardless of the message type
        geometry = self._app.desktop().geometry()
        packet = libwintab.PACKET()
        while lib.WTPacket(self.ctx, msg.wParam, ctypes.byref(packet)) > 0:
            # fetch current cursor
            if (msg.message == WT_CSRCHANGE and msg.wParam == packet.pkSerialNumber) or \
               packet.pkCursor not in self.cursors:
                # a cursor update is required
                cursor = QExtCursorData(self.device_idx, packet.pkCursor)
                self.cursors[packet.pkCursor] = cursor
            cursor = self.cursors[packet.pkCursor]

            # We copy QT's formulas verbatim here to be result-compatible, even though
            # we undo most of them later. Note that press also lacks bias adjustment(!)
            press = float(packet.pkNormalPressure) / float(self.np_axis.axMax - self.np_axis.axMin)

            pos_x = float(packet.pkX - self.x_axis.axMin) / float(self.x_axis.axMax - self.x_axis.axMin)
            pos_y = float(packet.pkY - self.y_axis.axMin) / float(self.y_axis.axMax - self.y_axis.axMin)
            pos = QtCore.QPointF(geometry.left() + pos_x * geometry.width(),
                                 geometry.top() + (1. - pos_y) * geometry.height())

            rad_azim = (packet.pkOrientation.orAzimuth / 10.) * (math.pi / 180.)
            tan_alt = tan((abs(packet.pkOrientation.orAltitude / 10.)) * (math.pi / 180.))
            deg_x = atan(sin(rad_azim) / tan_alt)
            deg_y = atan(cos(rad_azim) / tan_alt)
            tilt_x = int(deg_x * (180. / math.pi))
            tilt_y = int(-deg_y * (180. / math.pi))

            # use the primary button state to determine press/release events
            if not (packet.pkChanged & libwintab.PK_BUTTONS):
                subtype = EventSubtypes.MOVE
            else:
                btn = (packet.pkButtons >> 16) & 0xFF
                state = packet.pkButtons & 0xFF
                if btn != 0:
                    subtype = EventSubtypes.MOVE
                elif state != libwintab.TBN_NONE:
                    subtype = EventSubtypes.PRESS
                else:
                    subtype = EventSubtypes.RELEASE

            ev = QExtTabletEvent(subtype, now, packet.pkTime, packet.pkSerialNumber,
                                 press, pos, (tilt_x, tilt_y))
            self.window.event(ev)


class QExtTabletWindow(QtGui.QMainWindow):
    def __init__(self, device=0):
        super(QExtTabletWindow, self).__init__()
        self.tablet = QExtTabletContext(self, device)
        QExtTabletManager.register(self.tablet)

    def __del__(self):
        QExtTabletManager.unregister(self.tablet)
        del self.tablet
        super(QExtTabletWindow, self).__del__()

    def event(self, ev):
        if ev.type() == QtCore.QEvent.ActivationChange and self.isActiveWindow():
            # this forces our context to be above QT's and receive events
            self.tablet.activate()
        return super(QExtTabletWindow, self).event(ev)
