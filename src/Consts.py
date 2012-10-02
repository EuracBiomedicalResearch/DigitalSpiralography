# -*- coding: utf-8 -*-
"""Project-wide constants"""

# imports
from PyQt4 import QtGui, QtCore


# Basic versioning
APP_ORG         = "EURAC"               # application organization
APP_NAME        = "DrawingRecorder"     # application name
APP_VERSION     = "1.1"                 # application version
FORMAT_VERSION  = "1.0"                 # file format version
APP_DELAY       = 1. / 20.              # general refresh delay for lengthy operations

# Drawing parameters
POINT_LEN       = 0.05                  # diameter of calibration points (in normalized drawing units)
BAR_LEN         = 2.                    # extension of the calibration bars (in normalized drawing units)
CURSOR_LEN      = 25.                   # cursor extension (in pixels)
MAIN_TEXT_SIZE  = 20                    # size of main text (in points)
REFRESH_DELAY   = 100                   # timerEvent delay in ms
PEN_MAXWIDTH    = 10                    # max pen width in pixels (minimum is always 1)

# Drawing colors
CURSOR_ACTIVE   = QtCore.Qt.cyan        # pen in proximity
CURSOR_INACTIVE = QtCore.Qt.gray        # pen not in proximity
DRAWING_COLOR   = QtCore.Qt.white       # main drawing color
RECORDING_COLOR = QtCore.Qt.green       # recorded trace color
FAST_COLOR      = QtCore.Qt.cyan        # recorded fast trace color
FAST_SPEED      = 1000                  # recorded fast trace speed (px/sec)
