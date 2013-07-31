#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing batch renderer"""

from __future__ import print_function

# local modules
import Analysis

# Qt
from PyQt4 import QtCore

# system modules
import time
import sys
import codecs
import argparse
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
EXP_LEVEL = 2


def flip_y(vert):
    return (vert[0], -vert[1])


def remap(vmap, value):
    if value not in vmap:
        return "N/A"
    return vmap[value]


def renderSpiral(record, output):
    fig = plt.figure()
    fig.set_size_inches((7,9))

    gs = GridSpec(2, 1, height_ratios=[3,1])
    ax = fig.add_subplot(gs[0])
    codes = [Path.MOVETO, Path.LINETO]

    # track drawing status to recover actual tracing length/time
    old_pos = None
    old_stamp = None
    drawing = False
    for event in record.recording.events:
        stamp = event.stamp
        pos = flip_y(event.coords_drawing)

        # set drawing status
        if event.typ == QtCore.QEvent.TabletPress:
            drawing = True
        elif event.typ == QtCore.QEvent.TabletRelease:
            drawing = False
        elif event.typ == QtCore.QEvent.TabletEnterProximity:
            old_pos = None
            drawing = False
        elif event.typ == QtCore.QEvent.TabletLeaveProximity:
            drawing = False
            pos = None

        if old_pos:
            if drawing and pos:
                verts = [old_pos, pos]
                p = MIN_LW + math.pow(event.pressure, EXP_LEVEL) * MAX_LW
                patch = PathPatch(Path(verts, codes), lw=p)
                ax.add_patch(patch)
            elif pos:
                verts = [old_pos, pos]
                patch = PathPatch(Path(verts, codes), lw=SHA_LW, edgecolor='red')
                ax.add_patch(patch)

        # save old status
        old_pos = pos
        old_stamp = stamp

    # compose a title
    p_aid = record.aid
    p_type = remap(Analysis.PAT_TYPE, record.pat_type)
    p_hand = remap(Analysis.PAT_HAND, record.pat_hand)
    p_hdn = remap(Analysis.PAT_HANDEDNESS, record.pat_handedness)
    ax.set_title("{} {} ({} hand, {})".format(p_aid, p_type, p_hand, p_hdn))

    ax.set_xlim(-1,1)
    ax.set_ylim(-1,1)
    ax.grid(True)

    # pressure plot
    ax = fig.add_subplot(gs[1])
    ax.plot([x.pressure for x in record.recording.events])
    ax.yaxis.grid(True)
    ax.set_ylim(0,1)
    ax.yaxis.set_label_text('pressure')

    fig.tight_layout()
    fig.savefig(output, bbox_inches='tight')


def __main__():
    ap = argparse.ArgumentParser(description='Batch drawing renderer')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('file', help='drawing file')
    ap.add_argument('output', help='output file')
    args = ap.parse_args()

    record = Analysis.DrawingRecord.load(args.file, args.fast)
    renderSpiral(record, args.output)


if __name__ == '__main__':
    __main__()
