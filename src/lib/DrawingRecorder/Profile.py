# -*- coding: utf-8 -*-
"""Stylus profile correction/interpolators"""

from __future__ import print_function

# local modules
from . import Data

# system modules
import collections
import bisect
import datetime
import numpy as np
import scipy.optimize


def resp_curve(x, a, b, c):
    return x * a + x ** 2 * b + x ** 3 * c


def _closest_time_pair(times, t):
    i1 = bisect.bisect_right(times, t) - 1
    i1 = max(0, min(i1, len(times) - 2))
    i2 = i1 + 1
    t1 = times[i1]
    t2 = times[i2]
    v = 1. - (t2 - t).total_seconds() / (t2 - t1).total_seconds()
    return (i1, i2, v)


class ProfileCurve(object):
    def __init__(self, prof):
        assert(len(prof.data) > 5)
        data = sorted(prof.data, key=lambda x: x.pressure)
        x = np.array(map(lambda x: x.pressure, data))
        y = np.array(map(lambda x: x.weight, data))
        self.param, _ = scipy.optimize.curve_fit(resp_curve, x, y)

    def __call__(self, v):
        return resp_curve(v, *self.param)


class ProfileCurve2(object):
    def __init__(self, c1, c2, i):
        self.c1 = c1
        self.c2 = c2
        self.i = i

    def __call__(self, v):
        v1 = self.c1(v)
        v2 = self.c2(v)
        return v1 + (v2 - v1) * self.i


class ProfileMap(object):
    def __init__(self, sid, profs, marks):
        self.profs = sorted(profs, key=lambda p: p.ts_created)
        self.times = [p.ts_created for p in self.profs]
        self.curves = map(ProfileCurve, self.profs)

        if marks is not None:
            marks = sorted(marks, key=lambda m: m.stamp)
        else:
            # synthesize data
            marks = [Data.StylusUsageMark(self.times[0], 0),
                     Data.StylusUsageMark(self.times[-1], 1)]

        self.marks = [m.stamp for m in marks]
        self.counts = [float(m.count) for m in marks]


    def weight_range(self):
        ws = [c(1.) for c in self.curves]
        return (reduce(min, ws, ws[0]),
                reduce(max, ws, ws[0]))


    def time_range(self):
        return (min(self.times[0], self.marks[0]),
                max(self.times[-1], self.marks[-1]))


    def map_at_time(self, t):
        if len(self.times) < 2:
            return self.curves[0]

        i1, i2, iv = _closest_time_pair(self.times, t)

        m1, m2, mv = _closest_time_pair(self.marks, self.times[i1])
        c1 = self.counts[m1] + (self.counts[m2] - self.counts[m1]) * mv
        m1, m2, mv = _closest_time_pair(self.marks, self.times[i2])
        c2 = self.counts[m1] + (self.counts[m2] - self.counts[m1]) * mv

        tv = self.times[i1] + datetime.timedelta(
            seconds=(self.times[i2] - self.times[i1]).total_seconds() * iv)
        m1, m2, mv = _closest_time_pair(self.marks, tv)
        cv = self.counts[m1] + (self.counts[m2] - self.counts[m1]) * mv

        v = (cv - c1) / (c2 - c1)
        return ProfileCurve2(self.curves[i1], self.curves[i2], v)



class ProfileMapper(object):
    def __init__(self, profs, sur=None):
        # load data
        self.profs = collections.defaultdict(list)
        for fn in profs:
            prof = Data.StylusProfile.load(fn)
            self.profs[prof.sid].append(prof)

        # stylus usage report
        if sur is None:
            self.sur = None
        else:
            self.sur = Data.StylusUsageReport.load(sur)

        # initialize each sid independently
        for sid, profs in self.profs.iteritems():
            marks = self.sur.get(sid) if self.sur else None
            self.profs[sid] = ProfileMap(sid, profs, marks)

    def sids(self):
        """Return the list of available stylus IDs"""
        return self.profs.keys()

    def sid_map(self, sid):
        return self.profs[sid]

    def map_at_time(self, sid, time):
        return self.profs[sid].map_at_time(time)
