# -*- coding: utf-8 -*-
"""Drawing modules"""

# local modules
from Intl import translate

# system modules
import math
from PyQt4 import QtGui, QtCore


# implementation
class Drawing(object):
    def __init__(self, id, str, points, cpoints):
        self.id = id
        self.str = str
        self.points = points
        self.cpoints = cpoints



class SpiralParams(object):
    def __init__(self, diameter=None, turns=None, direction=None):
        self.diameter = diameter
        self.turns = turns
        self.direction = direction



class Spiral(Drawing):
    def __init__(self, id, params):
        self.params = params
        super(Spiral, self).__init__(id, self._describe(),
                                     self._generate(), self._cpoints())


    def _describe(self):
        return u"Ø{}mm {}T {}".format(
            self.params.diameter, self.params.turns, self.params.direction)


    def _generate(self, step=1.):
        buf = [(0, 0)]
        for x in xrange(1, int(self.params.turns * 360. / step) + 1):
            d = x * step
            r = 1. / (self.params.turns * 360.) * d
            a = math.radians(d)
            buf.append((r * math.cos(a), r * math.sin(a)))
        return buf


    def generate(self):
        buf = QtGui.QPainterPath()
        buf.moveTo(0, 0)
        for x, y in self.points[1:]:
            buf.lineTo(x, y)
        return QtGui.QGraphicsPathItem(buf)


    def calibrate(self, cpoints):
        transform = QtGui.QTransform()

        dx0 = cpoints[self._cpoint_maxx][0] - cpoints[self._cpoint_origin][0]
        dx1 = cpoints[self._cpoint_maxx][1] - cpoints[self._cpoint_origin][1]
        dy0 = cpoints[self._cpoint_maxy][0] - cpoints[self._cpoint_origin][0]
        dy1 = cpoints[self._cpoint_maxy][1] - cpoints[self._cpoint_origin][1]

        # check for straightness
        a = math.atan2(dx1, dx0)
        if abs(a) > math.pi / 16:
            return None, translate("drawing", "excessive rotation")

        # check for excessive deformations (the calibration points should have the same ratio,
        # but we need some breathing space for the different x/y DPI ratios of the device)
        pr = (math.hypot(self.cpoints[self._cpoint_maxx][0], self.cpoints[self._cpoint_maxx][1]) /
              math.hypot(self.cpoints[self._cpoint_maxy][0], self.cpoints[self._cpoint_maxy][1]))
        pr_ = math.hypot(dx0, dx1) / math.hypot(dy0, dy1)
        if abs(pr - pr_) > 0.25:
            return None, translate("drawing", "excessive deformation")

        # calibrate by calculating a simple affine matrix
        src = QtGui.QPolygonF()
        src.append(QtCore.QPointF(cpoints[self._cpoint_origin][0],
                                  cpoints[self._cpoint_origin][1]))
        src.append(QtCore.QPointF(cpoints[self._cpoint_maxy][0],
                                  cpoints[self._cpoint_maxy][1]))
        src.append(QtCore.QPointF(cpoints[self._cpoint_maxy][0] + dx0,
                                  cpoints[self._cpoint_maxy][1] + dx1))
        src.append(QtCore.QPointF(cpoints[self._cpoint_maxx][0],
                                  cpoints[self._cpoint_maxx][1]))

        dst = QtGui.QPolygonF()
        dst.append(QtCore.QPointF(self.cpoints[self._cpoint_origin][0],
                                  self.cpoints[self._cpoint_origin][1]))
        dst.append(QtCore.QPointF(self.cpoints[self._cpoint_maxy][0],
                                  self.cpoints[self._cpoint_maxy][1]))
        dst.append(QtCore.QPointF(self.cpoints[self._cpoint_maxx][0],
                                  self.cpoints[self._cpoint_maxy][1]))
        dst.append(QtCore.QPointF(self.cpoints[self._cpoint_maxx][0],
                                  self.cpoints[self._cpoint_maxx][1]))

        if not QtGui.QTransform.quadToQuad(src, dst, transform):
            return None, translate("drawing", "cannot remap coordinates")

        return transform, None


    def _cpoints(self):
        buf = [(0, 0)]
        self._cpoint_origin = len(buf) - 1

        # x increasing for all turns
        for x in xrange(1, int(self.params.turns) + 1):
            r = x / self.params.turns
            a = math.radians(0.)
            buf.append((r * math.cos(a), r * math.sin(a)))
        self._cpoint_maxx = len(buf) - 1

        # y increasing for all turns
        for x in xrange(1, int(self.params.turns) + 1):
            r = (x * 360. - 90.) / (self.params.turns * 360.)
            a = math.radians(-90.)
            buf.append((r * math.cos(a), r * math.sin(a)))
        self._cpoint_maxy = len(buf) - 1

        return buf
