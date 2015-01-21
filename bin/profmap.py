#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stylus profile evolution map"""

from __future__ import print_function

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Data
from DrawingRecorder import Profile

# system modules
import argparse
import datetime
import numpy as np
import sys
import time

# matplotlib
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt


def date(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")

def __main__():
    ap = argparse.ArgumentParser(description='Plot the stylus profile evolution map')
    ap.add_argument('-o', dest='output', help='Output image file', required=True)
    ap.add_argument('-s', dest='sid', help='Stylus ID to plot')
    ap.add_argument('-m', dest='max', help='Maximum weight (default to auto)')
    ap.add_argument('-S', dest='start', type=date,
                    help='Starting time range (YYYY-MM-DD, default to first measurement)')
    ap.add_argument('-E', dest='end', type=date,
                    help='Ending time range (YYYY-MM-DD, default to last measurement)')
    ap.add_argument('files', nargs='+', help='Stylus profiles')
    args = ap.parse_args()

    pmap = Profile.ProfileMapper(args.files)
    sids = pmap.sids()
    if args.sid is not None and args.sid not in sids:
        ap.error("stylus {sid} not available (loaded: {sids})".format(
            sid=args.sid, sids=', '.join(sids)))
    elif len(sids) > 1 and args.sid is None:
        ap.error("more than one stylus ID was loaded ({sids}), sid required".format(
            sids=', '.join(sids)))
    elif args.sid is None:
        args.sid = sids[0]

    # adjust displayed ranges
    sm = pmap.sid_map(args.sid)
    wr = list(sm.weight_range())
    tr = list(sm.time_range())

    if args.max is not None:
        wr[1] = int(args.max)
    else:
        wr[1] = wr[1] * 1.1

    trd = (tr[1] - tr[0]) / 10
    if args.start is not None:
        tr[0] = args.start
    else:
        tr[0] = tr[0] - trd
    if args.end is not None:
        tr[1] = args.end
    else:
        tr[1] = tr[1] + trd

    # calculate the response field
    nx = max(100, int((tr[1] - tr[0]).total_seconds() / 86400.))
    ny = max(100, int(wr[1]))
    xi, yi = np.meshgrid(np.linspace(0, (tr[1] - tr[0]).total_seconds(), nx),
                         np.linspace(0, 1, ny))
    z = np.empty([ny, nx])
    for x in range(nx):
        t = datetime.datetime.fromtimestamp(time.mktime(tr[0].timetuple()) + xi[0,x])
        curve = sm.map_at_time(t)
        for y in range(ny):
            v = yi[y, x]
            z[y, x] = curve(v)
    plt.pcolor(xi, z, yi, cmap='cool_r')

    # isolines
    istep = 50. / sm.weight_range()[1]
    for y in [1.] + list(np.arange(0, 1, istep)):
        yt = []
        for x in range(nx):
            t = datetime.datetime.fromtimestamp(time.mktime(tr[0].timetuple()) + xi[0,x])
            curve = sm.map_at_time(t)
            yt.append(curve(y))
        plt.plot(xi[0], yt, color='k', alpha=0.1)

    # plot the individual measurements
    for i in range(len(sm.profs)):
        prof = sm.profs[i]
        curve = sm.curves[i]
        x = [(prof.ts_created - tr[0]).total_seconds()] * len(prof.data)
        y = np.array(map(lambda x: x.weight, prof.data))
        z = np.array(map(lambda x: x.pressure, prof.data))
        plt.scatter(x, y, c=z, cmap='jet')

    # place xticks at the measurement dates
    xlocs = [(t - tr[0]).total_seconds() for t in sm.times]
    xlabels = []
    for x in xlocs:
        t = datetime.datetime.fromtimestamp(time.mktime(tr[0].timetuple()) + x)
        xlabels.append(t.strftime("%Y-%m-%d"))
    plt.xticks(xlocs, xlabels, rotation=45, horizontalalignment='right')

    plt.title('{sid} profile map'.format(sid=args.sid))
    plt.ylabel('Weight (g)')
    plt.margins(0.05)
    plt.ylim(0, wr[1])
    plt.grid()
    plt.tick_params(right=True, labelright=True)
    plt.savefig(args.output, bbox_inches='tight')

if __name__ == '__main__':
    __main__()
