# -*- coding: utf-8 -*-
"""Project-wide constants"""

# imports
from PyQt4 import QtCore


# Basic versioning
APP_ORG         = "EURAC"               # application organization
APP_NAME        = "DrawingRecorder"     # application name
APP_VERSION     = "1.8"                 # application version
APP_DELAY       = 1. / 20.              # general refresh delay for lengthy operations

# File formats
FORMAT_VERSION  = "1.5"                 # file format version
FF_RECORDING    = "rec"                 # recording type
FF_PROFILE      = "prof"                # profiling type

# File names
PROJ_CONFIG     = "config.yaml"         # project configuration file name

# Calibration
CAL_POINT_LEN   = 0.05                  # diameter of calibration points (in normalized drawing units)
CAL_MAX_TILT    = 5.                    # maximum tilt (degrees) during stylus calibration
CAL_DONE_COL    = QtCore.Qt.green       # filling color of previous points
CAL_OK_COL      = QtCore.Qt.yellow      # filling color of current calibration point
CAL_NEXT_COL    = QtCore.Qt.red         # filling color of uncalibrated/bad next point

# Drawing parameters
BAR_LEN         = 2.                    # extension of the calibration bars (in normalized drawing units)
CURSOR_LEN      = 25.                   # cursor extension (in pixels)
REFRESH_DELAY   = 100                   # timerEvent delay in ms
PEN_MAXWIDTH    = 20                    # max pen width in pixels (minimum is always 1)
TILT_MAXLEN     = 1./60. * 20.          # max tilt vectors length in 1/60th of pixels
LIFT_PEN_WIDTH  = 3                     # stroke/lift circle pen width
LIFT_RADIUS     = PEN_MAXWIDTH * 2      # stroke/lift circle radius

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
FAST_COLOR      = QtCore.Qt.red         # recorded fast trace color
FAST_SPEED      = 2                     # recorded fast trace speed (unit/sec)
TILT_COLOR      = QtCore.Qt.cyan        # tilt vectors
LIFT_COLOR      = QtCore.Qt.yellow      # stroke/lift circle color
