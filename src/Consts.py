# -*- coding: utf-8 -*-
"""Project-wide constants"""

# imports
from PyQt4 import QtGui, QtCore


# Basic versioning
APP_ORG         = "EURAC"               # application organization
APP_NAME        = "DrawingRecorder"     # application name
APP_VERSION     = "1.1"                 # application version
FORMAT_VERSION  = "1.1"                 # file format version
APP_DELAY       = 1. / 20.              # general refresh delay for lengthy operations

# Drawing parameters
POINT_LEN       = 0.05                  # diameter of calibration points (in normalized drawing units)
BAR_LEN         = 2.                    # extension of the calibration bars (in normalized drawing units)
CURSOR_LEN      = 25.                   # cursor extension (in pixels)
MAIN_TEXT_SIZE  = 20                    # size of main text (in points)
REFRESH_DELAY   = 100                   # timerEvent delay in ms
PEN_MAXWIDTH    = 10                    # max pen width in pixels (minimum is always 1)
TILT_MAXLEN     = 1./60. * 20.          # max tilt vectors length in 1/60th of pixels

# Drawing colors
CURSOR_ACTIVE   = QtCore.Qt.cyan        # pen in proximity
CURSOR_INACTIVE = QtCore.Qt.gray        # pen not in proximity
DRAWING_COLOR   = QtCore.Qt.white       # main drawing color
RECORDING_COLOR = QtCore.Qt.green       # recorded trace color
FAST_COLOR      = QtCore.Qt.cyan        # recorded fast trace color
FAST_SPEED      = 1000                  # recorded fast trace speed (px/sec)
TILT_COLOR      = QtCore.Qt.yellow      # tilt vectors

# File format event/code maps
EVENT_MAP = {QtCore.QEvent.TabletMove: 'move',
             QtCore.QEvent.TabletPress: 'press',
             QtCore.QEvent.TabletRelease: 'release',
             QtCore.QEvent.TabletEnterProximity: 'enter',
             QtCore.QEvent.TabletLeaveProximity: 'leave'}

REV_EVENT_MAP = {v:k for k, v in EVENT_MAP.items()}
