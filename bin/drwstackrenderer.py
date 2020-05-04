#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drawing batch stack renderer"""

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Data
from DrawingRecorder import Drawing
from DrawingRecorder import DrawingFactory

# Qt
from PyQt5 import QtCore

# system modules
import sys
import argparse
import math
import itertools

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


def renderPatch(record, ax, c, pressure):
    codes = [Path.MOVETO, Path.LINETO]

    # track drawing status to recover actual tracing length/time
    old_pos = None
    old_stamp = None
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

        if old_pos and drawing and pos:
            verts = [old_pos, pos]
            p = MIN_LW + math.pow(event.pressure, EXP_LEVEL) * MAX_LW if pressure else None
            patch = PathPatch(Path(verts, codes), lw=p, edgecolor=c)
            ax.add_patch(patch)

        # save old status
        old_pos = pos
        old_stamp = stamp


def remapSpiral(record, cal_mode):
    # offline recalibration
    drawing = DrawingFactory.from_id(record.drawing.id)
    aff, error = drawing.calibrate(record.calibration.cpoints,
                                   record.recording.rect_drawing,
                                   cal_mode)
    if error: raise Exception("calibration error: {error}".format(error=error))

    # remap to unit coordinates
    cpoints = [aff.map(x[0], x[1]) for x in record.calibration.cpoints]
    for event in record.recording.events:
        event.coords_unit = aff.map(event.coords_drawing[0], event.coords_drawing[1])


def renderSpirals(files, output, fast, pressure, desc, ticks, cal_mode):
    fig = plt.figure()
    fig.set_size_inches((7.35,9))

    # spiral axis
    gs = GridSpec(2, 2, height_ratios=[3,1], width_ratios=[20, 1])
    s_ax = fig.add_subplot(gs[0,0])
    s_ax.set_xlim(-1.2, 1.2)
    s_ax.set_ylim(-1.2, 1.2)
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
        step = itertools.count()

        sys.stderr.write(str(next(step)))
        record = Data.DrawingRecord.load(path, fast)

        if i == 0:
            # we assume we're comparing identical drawings
            sys.stderr.write("\b" + str(next(step)))
            s_ax.plot([x[0] for x in record.drawing.points],
                      [-x[1] for x in record.drawing.points],
                      '-', color='gray', alpha=0.5)

        sys.stderr.write("\b" + str(next(step)))
        remapSpiral(record, cal_mode)

        sys.stderr.write("\b" + str(next(step)))
        renderPatch(record, s_ax, c, pressure)

        sys.stderr.write("\b" + str(next(step)))
        p_ax.plot([x.pressure for x in record.recording.events], color=c)

        # clear
        sys.stderr.write("\b.")

    sys.stderr.write("\nrendering ...")
    fig.tight_layout()
    fig.savefig(output, bbox_inches='tight')
    sys.stderr.write("\n")


def __main__():
    cal_choices = {'full': Drawing.CalibrationMode.Full,
                   'extent': Drawing.CalibrationMode.Extent}
    ap = argparse.ArgumentParser(description='Batch drawing stack renderer')
    ap.add_argument('-o', dest='output', required=True, help='output file')
    ap.add_argument('-t', dest='ticks', nargs=3, help='colorbar low/med/high values')
    ap.add_argument('-d', dest='desc', default=None, help='colorbar description')
    ap.add_argument('-p', dest='pressure', action='store_true',
                    help='simulate pressure level')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('--cal', choices=cal_choices.keys(), default='full',
                    help='Calibration method')
    ap.add_argument('files', nargs='+', help='drawing file/s')
    args = ap.parse_args()
    renderSpirals(args.files, args.output, args.fast,
                  args.pressure, args.desc, args.ticks,
                  cal_choices.get(args.cal))

if __name__ == '__main__':
    __main__()
