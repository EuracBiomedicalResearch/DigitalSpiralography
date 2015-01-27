# -*- coding: utf-8 -*-
"""Stylus profile correction/interpolators"""

from __future__ import print_function

# local modules
import Data

# system modules
import collections
import bisect
import numpy as np
import scipy.optimize


def resp_curve(x, n, m, a, b):
    if n <= 0 or m <= 0 or a < 0 or b < 0:
        return np.nan
    return x ** n * a + x ** m * b


class ProfileCurve(object):
    def __init__(self, prof):
        assert(len(prof.data) > 5)
        x = np.array(map(lambda x: x.pressure, prof.data))
        y = np.array(map(lambda x: x.weight, prof.data))
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
    def __init__(self, sid, profs):
        self.profs = sorted(profs, key=lambda p: p.ts_created)
        self.times = [p.ts_created for p in self.profs]
        self.curves = map(ProfileCurve, self.profs)

    def weight_range(self):
        ws = [c(1.) for c in self.curves]
        return (reduce(min, ws, ws[0]),
                reduce(max, ws, ws[0]))

    def time_range(self):
        return self.times[0], self.times[-1]

    def map_at_time(self, t):
        # TODO: switch either to NURBS or bicubic interpolation
        if len(self.times) < 2:
            return self.curves[0]

        i1 = bisect.bisect_right(self.times, t) - 1
        i1 = max(0, min(i1, len(self.times) - 2))
        i2 = i1 + 1

        # linear interpolation in the reported range
        t1 = self.times[i1]
        t2 = self.times[i2]
        v = 1. - (t2 - t).total_seconds() / (t2 - t1).total_seconds()
        return ProfileCurve2(self.curves[i1], self.curves[i2], v)


class ProfileMapper(object):
    def __init__(self, files):
        # load data
        self.profs = collections.defaultdict(list)
        for file in files:
            prof = Data.StylusProfile.load(file)
            self.profs[prof.sid].append(prof)

        # initialize each sid independently
        for sid, profs in self.profs.iteritems():
            self.profs[sid] = ProfileMap(sid, profs)

    def sids(self):
        """Return the list of available stylus IDs"""
        return self.profs.keys()

    def sid_map(self, sid):
        return self.profs[sid]

    def map_at_time(self, sid, time):
        return self.profs[sid].map_at_time(time)
