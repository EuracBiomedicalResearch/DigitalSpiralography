# -*- coding: utf-8 -*-
"""Project-wide constants"""

# imports
from PyQt4 import QtGui, QtCore


# Basic versioning
APP_ORG         = "EURAC"               # application organization
APP_NAME        = "DrawingRecorder"     # application name
APP_VERSION     = "1.2"                 # application version
FORMAT_VERSION  = "1.1"                 # file format version
APP_DELAY       = 1. / 20.              # general refresh delay for lengthy operations

# Drawing parameters
POINT_LEN       = 0.05                  # diameter of calibration points (in normalized drawing units)
BAR_LEN         = 2.                    # extension of the calibration bars (in normalized drawing units)
CURSOR_LEN      = 25.                   # cursor extension (in pixels)
REFRESH_DELAY   = 100                   # timerEvent delay in ms
PEN_MAXWIDTH    = 10                    # max pen width in pixels (minimum is always 1)
TILT_MAXLEN     = 1./60. * 20.          # max tilt vectors length in 1/60th of pixels

# Text parameters
MAIN_TEXT_SIZE  = 32                    # size of main text (in points)
NORM_TEXT_SIZE  = 16                    # size of normal text (in points)
WARN_TEXT_SIZE  = 24                    # size of warnings (in points)

# Drawing colors
CURSOR_ACTIVE   = QtCore.Qt.cyan        # pen in proximity
CURSOR_INACTIVE = QtCore.Qt.gray        # pen not in proximity
FILL_COLOR      = QtCore.Qt.black       # main fill color
DRAWING_COLOR   = QtCore.Qt.white       # main drawing color
RECORDING_COLOR = QtCore.Qt.green       # recorded trace color
FAST_COLOR      = QtCore.Qt.cyan        # recorded fast trace color
FAST_SPEED      = 1000                  # recorded fast trace speed (px/sec)
TILT_COLOR      = QtCore.Qt.yellow      # tilt vectors
