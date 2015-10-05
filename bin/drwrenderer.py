#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing batch renderer"""

from __future__ import print_function, generators

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Data
from DrawingRecorder import DrawingFactory

# Qt
from PyQt4 import QtCore

# system modules
import argparse
import random
import math

# matplotlib
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.gridspec import GridSpec

# constants
MIN_LW = 0.1
SHA_LW = 0.5
MAX_LW = 4
PAP_LW = 1
EXP_LEVEL = 2


def flip_y(vert):
    return (vert[0], -vert[1])


def remap(vmap, value):
    if value not in vmap:
        return "N/A"
    return vmap[value]


def renderPaper(record):
    fig = plt.figure()
    fig.set_size_inches((7,7))

    ax = fig.gca()
    ax.grid(False)
    ax.axis('off')
    ax.set_xlim(-1.0, 1.2)
    ax.set_ylim(-1.0, 1.2)

    # track drawing status to recover actual tracing length/time
    codes = [Path.MOVETO, Path.LINETO]
    old_pos = None
    lw = PAP_LW
    c = 0.3
    drawing = False
    for event in record.recording.events:
        stamp = event.stamp
        pos = flip_y(event.coords_unit)

        # set drawing status
        if event.typ == QtCore.QEvent.TabletEnterProximity or \
           event.typ == QtCore.QEvent.TabletLeaveProximity:
            drawing = False
            pos = None
        elif event.pressure > 0:
            drawing = True
        elif event.typ == QtCore.QEvent.TabletRelease or event.pressure == 0.:
            drawing = False

        if old_pos:
            if drawing and pos:
                verts = [old_pos, pos]
                nlw = PAP_LW * 0.5 + random.random() * PAP_LW * 0.5
                lw = lw * 0.7 + nlw * 0.3
                nc = 0.05 + random.random() * 0.3
                c = c * 0.9 + nc * 0.1
                patch = PathPatch(Path(verts, codes), lw=lw,
                                  color=(c / 3, c / 2, c), capstyle='round')
                ax.add_patch(patch)

        # save old status
        old_pos = pos

    return fig


def renderStd(record, cpoints):
    fig = plt.figure()
    fig.set_size_inches((7,9))
    fig.subplots_adjust(top=0.9, hspace=0.1)

    gs = GridSpec(2, 1, height_ratios=[3,1])
    ax = fig.add_subplot(gs[0])
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.grid(True)

    # drawing/calibration points
    plt.plot(map(lambda x: x[0], record.drawing.points),
             map(lambda x: -x[1], record.drawing.points), '-')
    plt.scatter(map(lambda x: x[0], cpoints),
                map(lambda x: -x[1], cpoints))

    # track drawing status to recover actual tracing length/time
    codes = [Path.MOVETO, Path.LINETO]
    old_pos = None
    drawing = False
    for event in record.recording.events:
        stamp = event.stamp
        pos = flip_y(event.coords_unit)

        # set drawing status
        if event.typ == QtCore.QEvent.TabletEnterProximity or \
           event.typ == QtCore.QEvent.TabletLeaveProximity:
            drawing = False
            pos = None
        elif event.pressure > 0:
            drawing = True
        elif event.typ == QtCore.QEvent.TabletRelease or event.pressure == 0:
            drawing = False

        if old_pos and pos and old_pos != pos:
            if drawing:
                verts = [old_pos, pos]
                p = MIN_LW + math.pow(event.pressure, EXP_LEVEL) * MAX_LW
                patch = PathPatch(Path(verts, codes), lw=p, color='black', capstyle='round')
                ax.add_patch(patch)
            else:
                verts = [old_pos, pos]
                patch = PathPatch(Path(verts, codes), lw=SHA_LW, color='red')
                ax.add_patch(patch)

        # save old status
        old_pos = pos

    # pressure plot
    px = fig.add_subplot(gs[1])
    px.plot([x.pressure for x in record.recording.events])
    px.yaxis.grid(True)
    px.set_ylim(0,1)
    px.yaxis.set_label_text('pressure')

    return fig


def renderSpiral(record, output, paper, no_detail):
    # offline recalibration
    drawing = DrawingFactory.from_id(record.drawing.id)
    aff, error = drawing.calibrate(record.calibration.cpoints)
    if error: raise Exception("calibration error: {error}".format(error=error))

    # remap to unit coordinates
    cpoints = map(lambda x: aff.map(x[0], x[1]), record.calibration.cpoints)
    for event in record.recording.events:
        event.coords_unit = aff.map(event.coords_drawing[0], event.coords_drawing[1])

    fig = renderPaper(record) if paper else renderStd(record, cpoints)

    # compose a title
    if not no_detail:
        p_aid = record.aid
        p_type = record.config.pat_types.get(record.pat_type, record.pat_type)
        p_hand = remap(Data.PAT_HAND, record.pat_hand)
        p_hdn = remap(Data.PAT_HANDEDNESS, record.pat_handedness)
        fig.suptitle("{} {} ({} hand, {})".format(p_aid, p_type, p_hand, p_hdn),
                     y=0.95, fontsize='x-large')

    fig.savefig(output, bbox_inches='tight')


def __main__():
    ap = argparse.ArgumentParser(description='Batch drawing renderer')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('-p', dest='paper', action='store_true',
                    help='paper-like rendering')
    ap.add_argument('-n', dest='no_detail', action='store_true',
                    help='no details')
    ap.add_argument('file', help='drawing file')
    ap.add_argument('output', help='output file')
    args = ap.parse_args()

    record = Data.DrawingRecord.load(args.file, args.fast)
    renderSpiral(record, args.output, args.paper, args.no_detail)


if __name__ == '__main__':
    __main__()
