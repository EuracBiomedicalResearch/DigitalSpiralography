# -*- coding: utf-8 -*-
"""Shared functions between Recorder/Visualizer"""

# local modules
from . import Consts

# system modules
import datetime
import time
import threading
from PyQt4 import QtCore, QtGui


# support functions
def poly2qpoly(poly):
    ret = QtGui.QPolygonF()
    for v in poly:
        ret.append(QtCore.QPointF(v[0], v[1]))
    return ret


def size2qpoly(w, h):
    return poly2qpoly([(0, 0), (w, 0), (w, h), (0, h)])


def background_op(message, func, parent=None):
    pd = QtGui.QProgressDialog(message, QtCore.QString(), 0, 0, parent)
    pd.setWindowModality(QtCore.Qt.ApplicationModal)
    pd.show()

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
        th.join(Consts.APP_DELAY)

    pd.hide()

    if 'exception' in ret:
        raise ret['exception']
    return ret['ret']


def dtts(dt):
    return int(time.mktime(dt.timetuple()))


def tsdt(ts):
    return datetime.datetime.fromtimestamp(ts)
