# -*- coding: utf-8 -*-
"""Shared functions between Recorder/Visualizer"""

# local modules
from . import Consts

# system modules
import datetime
import dateutil.parser
import time
import threading
import math
from PyQt4 import QtCore, QtGui


# Geometry support functions
def poly2qpoly(poly):
    ret = QtGui.QPolygonF()
    for v in poly:
        ret.append(QtCore.QPointF(v[0], v[1]))
    return ret


def size2qpoly(w, h):
    return poly2qpoly([(0, 0), (w, 0), (w, h), (0, h)])


# General QT functions
def background_op(message, func, parent=None):
    pd = QtGui.QProgressDialog(message, "", 0, 0, parent)
    pd.setWindowTitle(Consts.APP_NAME)
    pd.setWindowModality(QtCore.Qt.ApplicationModal)
    pd.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)

    def background_fn(ret, func):
        try:
            ret['ret'] = func()
        except Exception as e:
            ret['exception'] = e

    ret = {}
    th = threading.Thread(target=lambda: background_fn(ret, func))
    th.start()
    while th.is_alive():
        QtGui.QApplication.processEvents()
        if not th.join(Consts.APP_DELAY):
            pd.show()

    pd.close()
    pd.deleteLater()

    if 'exception' in ret:
        raise ret['exception']
    return ret['ret']


# Timestamp handling
def timedelta_min_sec(td):
    total_seconds = td.total_seconds()
    isec = int(total_seconds)
    msec = int((total_seconds - isec) * 10)
    mins = isec / 60
    secs = isec % 60
    return "{:02d}:{:02d}.{:01d}".format(mins, secs, msec)

def dtts(dt):
    """Datetime to UTC timestamp"""
    return int(time.mktime(dt.timetuple()))

def tsdt(ts, tzoffset=None):
    """Parse an UTC timestamp to (localized) datetime"""
    if tzoffset is not None and math.isfinite(tzoffset):
        tzinfo = dateutil.tz.tzoffset(None, tzoffset)
    else:
        tzinfo = None
    return datetime.datetime.fromtimestamp(float(ts), tzinfo)

def strdt(s, tzoffset=None):
    """String to (localized) datetime"""
    date = dateutil.parser.parse(s)
    if date.tzinfo is None and tzoffset is not None:
        tzinfo = dateutil.tz.tzoffset(None, tzoffset)
        date = tzinfo.fromutc(date.replace(tzinfo=tzinfo))
    return date
