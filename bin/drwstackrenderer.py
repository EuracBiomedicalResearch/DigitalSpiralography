#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Drawing batch stack renderer"""

from __future__ import print_function

# setup path
import os, sys
DR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(DR_ROOT, "src", "lib"))
sys.path.append(os.path.join(DR_ROOT, "src", "dist"))

# local modules
from DrawingRecorder import Analysis

# Qt
from PyQt4 import QtCore

# system modules
import time
import sys
import codecs
import argparse
import math

# matplotlib
import numpy as np
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


def renderPatch(record, ax, c, pressure):
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

        if old_pos and drawing and pos:
            verts = [old_pos, pos]
            p = MIN_LW + math.pow(event.pressure, EXP_LEVEL) * MAX_LW if pressure else None
            patch = PathPatch(Path(verts, codes), lw=p, edgecolor=c)
            ax.add_patch(patch)

        # save old status
        old_pos = pos
        old_stamp = stamp


def renderSpirals(files, output, fast, pressure, desc, ticks):
    fig = plt.figure()
    fig.set_size_inches((7.35,9))

    # spiral axis
    gs = GridSpec(2, 2, height_ratios=[3,1], width_ratios=[20, 1])
    s_ax = fig.add_subplot(gs[0,0])
    s_ax.set_xlim(-1,1)
    s_ax.set_ylim(-1,1)
    s_ax.grid(True)

    # pressure axis
    p_ax = fig.add_subplot(gs[1,0])
    p_ax.set_ylim(0,1)
    p_ax.yaxis.grid(True)
    p_ax.yaxis.set_label_text('pressure')

    # color map
    nfiles = len(files)
    cmap = mpl.cm.get_cmap('brg')
    norm = mpl.colors.Normalize(0, nfiles)
    smap = mpl.cm.ScalarMappable(norm, cmap)

    c_ax = fig.add_subplot(gs[0, 1])
    cbar = mpl.colorbar.ColorbarBase(c_ax, cmap=cmap, norm=norm, ticks=[0, nfiles / 2, nfiles])
    if desc: cbar.ax.set_ylabel(desc)
    if ticks: cbar.ax.set_yticklabels(ticks, rotation='vertical')

    sys.stderr.write("loading ")
    for i in range(nfiles):
        path = files[i]
        c = smap.to_rgba(i)

        sys.stderr.write("1")
        record = Analysis.DrawingRecord.load(path, fast)

        sys.stderr.write("\b2")
        renderPatch(record, s_ax, c, pressure)

        sys.stderr.write("\b3")
        p_ax.plot([x.pressure for x in record.recording.events], color=c)
        sys.stderr.write("\b.")

    sys.stderr.write("\nrendering ...")
    fig.tight_layout()
    fig.savefig(output, bbox_inches='tight')
    sys.stderr.write("\n")


def __main__():
    ap = argparse.ArgumentParser(description='Batch drawing stack renderer')
    ap.add_argument('-o', dest='output', required=True, help='output file')
    ap.add_argument('-t', dest='ticks', nargs=3, help='colorbar low/med/high values')
    ap.add_argument('-d', dest='desc', default=None, help='colorbar description')
    ap.add_argument('-p', dest='pressure', action='store_true',
                    help='simulate pressure level')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('files', nargs='+', help='drawing file/s')
    args = ap.parse_args()
    renderSpirals(args.files, args.output, args.fast,
                  args.pressure, args.desc, args.ticks)

if __name__ == '__main__':
    __main__()
