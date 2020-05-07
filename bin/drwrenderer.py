#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drawing batch renderer"""

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
import argparse
from random import random
from math import pow

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

PAP_LW_B = 0.5  # minimal line width
PAP_LW_R = 0.1  # random width component
PAP_LW_V = 0.7  # real width component

PAP_LC_B = 0.7  # base black level
PAP_LC_R = 0.1  # random black component
PAP_LC_V = 0.5  # real black component

EXP_LEVEL = 2


def flip_y(vert):
    return (vert[0], -vert[1])


def remap(vmap, value):
    if value not in vmap:
        return "N/A"
    return vmap[value]


def renderPaper(record, dpi):
    drawing = DrawingFactory.from_id(record.drawing.id)
    spc = 1
    scale = drawing.params.radius * spc
    size_in = scale * 2 / 25.4
    fig = plt.figure(figsize=(size_in,size_in), dpi=dpi)

    ax = fig.gca()
    ax.grid(False)
    ax.axis('off')
    ax.set_xlim(-spc, spc)
    ax.set_ylim(-spc, spc)

    # scale ruler
    ll = [-drawing.params.radius * 0.5, -drawing.params.radius * 0.5]
    mfunc = lambda v: (v[0] / scale - spc, v[1] / scale - spc)
    whl = (100, 5, 0.3)
    ax.add_patch(PathPatch(Path(list(map(mfunc, [[0, 0], [whl[0], 0]]))),
                           lw=whl[2], color='k', fill=False, clip_on=False))
    ax.add_patch(PathPatch(Path(list(map(mfunc, [[0, -whl[1]/2], [0, whl[1]/2]]))),
                           lw=whl[2], color='k', fill=False, clip_on=False))
    ax.add_patch(PathPatch(Path(list(map(mfunc, [[whl[0], -whl[1]/2], [whl[0], whl[1]/2]]))),
                           lw=whl[2], color='k', fill=False, clip_on=False))
    ax.add_artist(plt.Text(*mfunc([whl[0] + whl[1]/2, -whl[1]/2]), '10cm',
                           va='bottom', ha='left', clip_on=False))

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
        elif event.typ == QtCore.QEvent.TabletRelease or event.pressure == 0.:
            drawing = False

        if old_pos:
            if drawing and pos:
                verts = [old_pos, pos]
                lw = (PAP_LW_B + (PAP_LW_R * random() - PAP_LW_R/2)
                      + (PAP_LW_V * event.pressure - PAP_LW_V/2))
                lc = (PAP_LC_B + (PAP_LC_R * random() - PAP_LC_R/2)
                      + (PAP_LC_V * event.pressure - PAP_LW_V/2))
                lc = 1 - min(1, max(0, lc))
                patch = PathPatch(Path(verts, codes), lw=lw,
                                  color=(lc, lc, lc), capstyle='round')
                ax.add_patch(patch)

        # save old status
        old_pos = pos

    return fig


def renderStd(record, cpoints, dpi):
    fig = plt.figure(figsize=(7,9), dpi=dpi)
    fig.subplots_adjust(top=0.9, hspace=0.1)

    gs = GridSpec(2, 1, height_ratios=[3,1])
    ax = fig.add_subplot(gs[0])
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.grid(True)

    # drawing/calibration points
    plt.plot([x[0] for x in record.drawing.points],
             [-x[1] for x in record.drawing.points], '-')
    plt.scatter([x[0] for x in cpoints],
                [-x[1] for x in cpoints])

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
                p = MIN_LW + pow(event.pressure, EXP_LEVEL) * MAX_LW
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


def renderSpiral(record, output, paper, no_detail, cal_mode, dpi):
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

    fig = renderPaper(record, dpi) if paper else renderStd(record, cpoints, dpi)

    # compose a title
    if not no_detail:
        p_aid = record.aid
        p_type = record.config.pat_types.get(record.pat_type, record.pat_type)
        p_hand = remap(Data.PAT_HAND, record.pat_hand)
        p_hdn = remap(Data.PAT_HANDEDNESS, record.pat_handedness)
        fig.suptitle("{} {} ({} hand, {})".format(p_aid, p_type, p_hand, p_hdn),
                     y=0.95, fontsize='x-large')

    fig.savefig(output, bbox_inches='tight', dpi='figure')


def __main__():
    cal_choices = {'full': Drawing.CalibrationMode.Full,
                   'extent': Drawing.CalibrationMode.Extent}
    ap = argparse.ArgumentParser(description='Batch drawing renderer')
    ap.add_argument('-f', dest='fast', action='store_true',
                    help='Enable fast loading')
    ap.add_argument('--cal', choices=cal_choices.keys(), default='full',
                    help='Calibration method')
    ap.add_argument('-p', dest='paper', action='store_true',
                    help='paper-like rendering')
    ap.add_argument('-n', dest='no_detail', action='store_true',
                    help='hide spiral details')
    ap.add_argument('--dpi', type=float, default=100,
                    help='output DPI')
    ap.add_argument('file', help='drawing file')
    ap.add_argument('output', help='output file')
    args = ap.parse_args()

    record = Data.DrawingRecord.load(args.file, args.fast)
    renderSpiral(record, args.output, args.paper, args.no_detail,
                 cal_choices.get(args.cal), args.dpi)


if __name__ == '__main__':
    __main__()
