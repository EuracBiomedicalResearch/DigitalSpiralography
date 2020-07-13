# -*- coding: utf-8 -*-
"""Drawing analysis"""

# local modules
from . import DrawingFactory

# system modules
import numpy as np
import pandas as pd
import scipy as sp
import scipy.signal

# Qt
from PyQt5 import QtCore


# General utilities
def trace_idx(recording, idx=0):
    return recording.events if idx == 0 \
        else recording.retries[idx - 1]

# Given an array length and a list of splitting index positions, return
# an array of the form (index, len), removing zero-length runs
def irlsplit(alen, indices):
    lst = 0
    for idx in indices:
        rl = idx - lst
        if rl > 0:
            yield (lst, rl)
        lst = idx
    rl = alen - lst
    if rl > 0:
        yield (lst, rl)

def where(cond):
    return np.where(cond)[0]

def diff_nz_idx(ary):
    return (where(np.diff(ary)) + 1)

def seg_slice(ary, start, length):
    return ary[start:(start+length)]

def seg_diff(ary, start, length):
    return (ary[start + length - 1] - ary[start])


# Data structures
class AnalysisException(RuntimeError):
    def __init__(self, stage, error):
        self.stage = stage
        self.error = error
        super(AnalysisException, self).__init__(error)

    def __str__(self):
        return "AnalysisException[{stage}]: {msg}".format(stage=self.stage, msg=self.error)


class AnalysisData(object):
    def __init__(self):
        self.cfg = None
        self.aff = None
        self.events = None
        self.error = None
        self.drawing = None
        self.cpoints = None
        self.freq_fit = None
        self.trace = None
        self.x_total_c_len = None
        self.x_total_d_len = None
        self.x_total_d_secs = None
        self.x_total_nd_len = None
        self.x_total_nd_secs = None
        self.x_press_min = None
        self.x_press_med = None
        self.x_press_avg = None
        self.x_press_max = None
        self.x_press_p10 = None
        self.x_press_p90 = None
        self.x_stroke_len_min = None
        self.x_stroke_len_med = None
        self.x_stroke_len_avg = None
        self.x_stroke_len_max = None
        self.x_weight_min = None
        self.x_weight_med = None
        self.x_weight_avg = None
        self.x_weight_max = None
        self.x_weight_p10 = None
        self.x_weight_p90 = None
        self.x_speed = {}
        self.x_acc = {}
        self.x_tamp = {}
        self.x_freq_peak_hz = None
        self.x_freq_peak_pwr = None
        self.xy_freq_peak_hz = None
        self.xy_freq_peak_pwr = None
        self.x_buck = {}
        self.xy_buck = {}


    def info(self):
        res =  {'FREQ_FIT': self.freq_fit,

                # TODO
                'SPR_CMB_LEN_MM': self.x_total_c_len,
                'SPR_DRW_LEN_MM': self.x_total_d_len,
                'SPR_DRW_SECS': self.x_total_d_secs,
                'SPR_AIR_LEN_MM': self.x_total_nd_len,
                'SPR_AIR_SECS': self.x_total_nd_secs,
                'SPR_PRESS_MIN': self.x_press_min,
                'SPR_PRESS_MED': self.x_press_med,
                'SPR_PRESS_AVG': self.x_press_avg,
                'SPR_PRESS_MAX': self.x_press_max,
                'SPR_PRESS_P10': self.x_press_p10,
                'SPR_PRESS_P90': self.x_press_p90,
                'SPR_STROKE_LEN_MM_MIN': self.x_stroke_len_min,
                'SPR_STROKE_LEN_MM_MED': self.x_stroke_len_med,
                'SPR_STROKE_LEN_MM_AVG': self.x_stroke_len_avg,
                'SPR_STROKE_LEN_MM_MAX': self.x_stroke_len_max,
                'SPR_WEIGHT_G_MIN': self.x_weight_min,
                'SPR_WEIGHT_G_MED': self.x_weight_med,
                'SPR_WEIGHT_G_AVG': self.x_weight_avg,
                'SPR_WEIGHT_G_MAX': self.x_weight_max,
                'SPR_WEIGHT_G_P10': self.x_weight_p10,
                'SPR_WEIGHT_G_P90': self.x_weight_p90,
                'SPR_W_PEAK_FREQ_HZ': self.x_freq_peak_hz,
                'SPR_W_PEAK_FREQ_PWR': self.x_freq_peak_pwr,
                'SPR_XY_PEAK_FREQ_HZ': self.xy_freq_peak_hz,
                'SPR_XY_PEAK_FREQ_PWR': self.xy_freq_peak_pwr,
                # TODO

                'ERR': self.error and "{}: {}".format(self.error.stage, self.error.error)}

        for ms in self.cfg.speed_win_ms:
            for typ in ['min', 'med', 'avg', 'max', 'p10', 'p90']:
                res['SPR_SPD_AIR_{}_{}'.format(ms, typ.upper())] = self.x_speed.get(False, {}).get(ms, {}).get(typ)
                res['SPR_SPD_DRW_{}_{}'.format(ms, typ.upper())] = self.x_speed.get(True, {}).get(ms, {}).get(typ)
                res['SPR_SPD_CMB_{}_{}'.format(ms, typ.upper())] = self.x_speed.get(None, {}).get(ms, {}).get(typ)
                res['SPR_ACC_AIR_{}_{}'.format(ms, typ.upper())] = self.x_acc.get(False, {}).get(ms, {}).get(typ)
                res['SPR_ACC_DRW_{}_{}'.format(ms, typ.upper())] = self.x_acc.get(True, {}).get(ms, {}).get(typ)
                res['SPR_ACC_CMB_{}_{}'.format(ms, typ.upper())] = self.x_acc.get(None, {}).get(ms, {}).get(typ)
                res['SPR_TAMP_AIR_{}_{}'.format(ms, typ.upper())] = self.x_tamp.get(False, {}).get(ms, {}).get(typ)
                res['SPR_TAMP_DRW_{}_{}'.format(ms, typ.upper())] = self.x_tamp.get(True, {}).get(ms, {}).get(typ)
                res['SPR_TAMP_CMB_{}_{}'.format(ms, typ.upper())] = self.x_tamp.get(None, {}).get(ms, {}).get(typ)

        for x in range(28):
            if x not in self.x_buck:
                self.x_buck[x] = {'RANGE': (0, 0), 'SMP': 0, 'PWR': None}
            res["SPR_W_FREQ_BAND_{:02d}_RANGE".format(x)] = "{:.3f}-{:.3f}".format(*self.x_buck[x]['RANGE'])
            res["SPR_W_FREQ_BAND_{:02d}_SMP".format(x)] = self.x_buck[x]['SMP']
            res["SPR_W_FREQ_BAND_{:02d}_PWR".format(x)] = self.x_buck[x]['PWR']

        for x in range(28):
            if x not in self.xy_buck:
                self.xy_buck[x] = {'RANGE': (0, 0), 'SMP': 0, 'PWR': None}
            res["SPR_XY_FREQ_BAND_{:02d}_RANGE".format(x)] = "{:.3f}-{:.3f}".format(*self.xy_buck[x]['RANGE'])
            res["SPR_XY_FREQ_BAND_{:02d}_SMP".format(x)] = self.xy_buck[x]['SMP']
            res["SPR_XY_FREQ_BAND_{:02d}_PWR".format(x)] = self.xy_buck[x]['PWR']

        return res



# Analysis stages
def _recalibrate(res, record):
    res.drawing = DrawingFactory.from_id(record.drawing.id)
    if not res.drawing:
        raise AnalysisException('calibration', 'unknown drawing ID')
    res.aff, error = res.drawing.calibrate(record.calibration.cpoints)
    if error:
        raise AnalysisException('calibration', error)


def _remap(res, record, pmap, idx):
    # select the event trace
    res.events = trace_idx(record.recording, idx)
    if not res.events:
        raise AnalysisException('remap', "no events to analyze for trace #{n}".format(n=idx))

    # drawing/tracking status
    trace_i = []
    trace_x = []
    trace_y = []
    trace_p = []
    trace_w = []
    trace_d = []
    trace_s = []

    segment = 0
    drawing = False
    for i, event in enumerate(res.events):
        xy = event.coords_drawing
        press = event.pressure

        # set drawing status
        if event.typ == QtCore.QEvent.TabletEnterProximity or \
           event.typ == QtCore.QEvent.TabletLeaveProximity:
            xy = None
            drawing = False
            segment += 1
        elif event.pressure > 0:
            drawing = True
        elif event.typ == QtCore.QEvent.TabletRelease or event.pressure == 0.:
            drawing = False

        # add to individual series
        if xy:
            xy = res.aff.map(*xy)
            if pmap and press is not None:
                weight = pmap(press)
            else:
                weight = 0;
            trace_i.append(i)
            trace_x.append(xy[0])
            trace_y.append(xy[1])
            trace_p.append(press)
            trace_w.append(weight)
            trace_d.append(drawing)
            trace_s.append(segment)

    # flatten all data into a DF
    cpoints = zip(*map(lambda x: res.aff.map(x[0], x[1]), record.calibration.cpoints))
    res.cpoints = pd.DataFrame({'X': cpoints[0], 'Y': cpoints[1]})
    res.trace = pd.DataFrame({'X': trace_x, 'Y': trace_y,
                              'P': trace_p, 'W': trace_w,
                              'D': trace_d, 'S': trace_s},
                             index=trace_i)


def _requantize(res, record, cfg):
    trace_ts = [res.events[x].stamp for x in res.trace.index]
    trace_sec = [(ts - trace_ts[0]).total_seconds() for ts in trace_ts]
    trace_d1 = np.hstack((0., np.diff(trace_sec)))

    # build a list of deltas using each segment independently
    trace_seg_d1 = []
    for seg in irlsplit(len(res.trace.index), diff_nz_idx(res.trace.S)):
        if seg_diff(trace_sec, *seg) >= 1.:
            trace_seg_d1.append(seg_slice(trace_d1, (seg[0] + 1), (seg[1] - 1)))
    if not len(trace_seg_d1):
        raise AnalysisException('requantize', 'not enough contiguous events')

    # timestamp jitter cutoff
    res.jitter_cutoff = np.percentile(np.hstack(trace_seg_d1), 99.) * 2
    res.jitter_min_samples = int(1. / res.jitter_cutoff) * 2

    # longest segment, based on S+jitter
    jit_segs = list(irlsplit(len(res.trace.index),
                             np.unique(list(where(trace_d1 > res.jitter_cutoff)) +
                                       list(diff_nz_idx(res.trace.S)))))
    jit_max_seg = max(jit_segs, key=lambda x: x[1])
    jit_max_seg = (jit_max_seg[0], jit_max_seg[1] - 100)
    jit_max_secs = seg_diff(trace_sec, *jit_max_seg)
    if jit_max_seg[1] < res.jitter_min_samples:
        msg = 'largest segment too short (#{n}, min: #{min})'.format(
            n=jit_max_seg[1], min=res.jitter_min_samples)
        raise AnalysisException('requantize', msg)
    if jit_max_secs < 1.:
        msg = 'largest segment too short ({secs}s)'.format(secs=jit_max_secs)
        raise AnalysisException('requantize', msg)

    # estimate initial target frequency
    #jit_fit = np.linalg.lstsq(
    #    np.vstack([range(jit_max_seg[1]), np.ones(jit_max_seg[1])]).T,
    #    seg_slice(trace_sec, *jit_max_seg))
    jit_fit = cfg.freq_map.get(record.calibration.tablet_id)
    if not jit_fit:
        raise AnalysisException('requantize', 'cannot estimate initial target frequency')
    res.freq_fit = jit_fit


def _cleanup(res, record, cfg):
    # --- remove air sections
    for i in range(0, len(res.trace)):
        if res.trace.D.iat[i]:
            break
    res.trace = res.trace[i:]

    for i in range(len(res.trace) - 1, 0, -1):
        if res.trace.D.iat[i]:
            break
    res.trace = res.trace[:i]

    # --- remove initial/final parts
    cut_ms = 250
    cut_mm = 10

    acc_len = 0
    acc_smp = res.freq_fit * (cut_ms / 1000)
    for i in range(1, len(res.trace)):
        acc_len += res.drawing.params.radius * np.sqrt(
            np.square(res.trace.X.iat[i-1] - res.trace.X.iat[i]) +
            np.square(res.trace.Y.iat[i-1] - res.trace.Y.iat[i]))
        if acc_len >= cut_mm and i >= acc_smp:
            break
    res.trace = res.trace[i:]

    acc_len = 0
    for i in range(len(res.trace) - 1, 1, -1):
        acc_len += res.drawing.params.radius * np.sqrt(
            np.square(res.trace.X.iat[i-1] - res.trace.X.iat[i]) +
            np.square(res.trace.Y.iat[i-1] - res.trace.Y.iat[i]))
        if acc_len >= cut_mm and (len(res.trace)-i) >= acc_smp:
            break
    res.trace = res.trace[:i]

    if len(res.trace) < (res.freq_fit * 2):
        raise AnalysisException('cleanup', 'spiral too short/fast for analysis after cleanup')


def _analyze_test(res, record, cfg):
    # spiral length/secs
    total_d_len = 0
    total_d_secs = 0
    total_nd_len = 0
    total_nd_secs = 0
    max_drw_trace = None
    for seg in irlsplit(len(res.trace.index),
                        np.unique(list(diff_nz_idx(res.trace.D)) +
                                  list(diff_nz_idx(res.trace.S)))):
        total_len = np.sum(np.sqrt(
            np.square(np.diff(seg_slice(res.trace.X, *seg))) +
            np.square(np.diff(seg_slice(res.trace.Y, *seg)))))
        trace_ts = [res.events[x].stamp for x in seg_slice(res.trace.index, *seg)]
        total_secs = (trace_ts[-1] - trace_ts[0]).total_seconds()
        if res.trace.D.iloc[seg[0]] == True:
            total_d_len += total_len
            total_d_secs += total_secs
            drw_trace = [seg_slice(res.trace.X, *seg), seg_slice(res.trace.Y, *seg)]
            if max_drw_trace is None or len(drw_trace[0]) > len(max_drw_trace[0]):
                max_drw_trace = drw_trace
        else:
            total_nd_len += total_len
            total_nd_secs += total_secs

    res.x_total_d_len = total_d_len * res.drawing.params.radius
    res.x_total_d_secs = total_d_secs
    res.x_total_nd_len = total_nd_len * res.drawing.params.radius
    res.x_total_nd_secs = total_nd_secs

    # combined
    total_len = np.sum(np.sqrt(
        np.square(np.diff(res.trace.X)) +
        np.square(np.diff(res.trace.Y))))
    res.x_total_c_len = total_len * res.drawing.params.radius

    # stroke lenghts
    stroke_len = []
    for seg in irlsplit(len(res.trace.index), diff_nz_idx(res.trace.D)):
        if res.trace.D.iloc[seg[0]] == True:
            seg_len = np.sum(np.sqrt(
                np.square(np.diff(seg_slice(res.trace.X, *seg))) +
                np.square(np.diff(seg_slice(res.trace.Y, *seg)))))
            stroke_len.append(seg_len)

    res.x_stroke_len_min = len(stroke_len) and np.min(stroke_len)
    res.x_stroke_len_med = len(stroke_len) and np.median(stroke_len)
    res.x_stroke_len_avg = len(stroke_len) and np.mean(stroke_len)
    res.x_stroke_len_max = len(stroke_len) and np.max(stroke_len)

    # pressures/weights
    press_seg = []
    press_weight = []

    for seg in irlsplit(len(res.trace.index), diff_nz_idx(res.trace.D)):
        trace_ts = [res.events[x].stamp for x in seg_slice(res.trace.index, *seg)]
        total_secs = (trace_ts[-1] - trace_ts[0]).total_seconds()
        if res.trace.D.iloc[seg[0]] == True:
            press_seg = seg_slice(res.trace.P, *seg)
            press_weight = seg_slice(res.trace.W, *seg)

    press_seg = press_seg[int(res.freq_fit):-int(res.freq_fit)]
    press_weight = press_weight[int(res.freq_fit):-int(res.freq_fit)]

    res.x_press_min = len(press_seg) and np.min(press_seg)
    res.x_press_med = len(press_seg) and np.median(press_seg)
    res.x_press_avg = len(press_seg) and np.mean(press_seg)
    res.x_press_max = len(press_seg) and np.max(press_seg)
    res.x_press_p10 = len(press_seg) and np.percentile(press_seg, 10.)
    res.x_press_p90 = len(press_seg) and np.percentile(press_seg, 90.)
    res.x_weight_min = len(press_weight) and np.min(press_weight)
    res.x_weight_med = len(press_weight) and np.median(press_weight)
    res.x_weight_avg = len(press_weight) and np.mean(press_weight)
    res.x_weight_max = len(press_weight) and np.max(press_weight)
    res.x_weight_p10 = len(press_weight) and np.percentile(press_weight, 10.)
    res.x_weight_p90 = len(press_weight) and np.percentile(press_weight, 90.)

    # speed/acc
    trace_dist = np.hstack([0., np.sqrt(
        np.square(np.diff(res.trace.X)) +
        np.square(np.diff(res.trace.Y)))])
    trace_speed = np.hstack([0., np.diff(trace_dist)])
    trace_acc = np.hstack([0., np.diff(trace_speed)])

    def _win_calc(trace, d, w):
        smp = int(res.freq_fit * (w / 1000.))
        win = np.full(smp, 1. / smp)
        sp = np.convolve(trace, win, 'same')
        if d == None:
            return sp
        fin_sp = []
        for seg in irlsplit(len(res.trace.index), diff_nz_idx(res.trace.D)):
            if res.trace.D.iloc[seg[0]] == d:
                fin_sp += list(seg_slice(sp, *seg))
        return fin_sp

    res.x_speed = {}
    for drw in [True, False]:
        res.x_speed[drw] = {}
        for ws in cfg.speed_win_ms:
            tmp = _win_calc(trace_dist, drw, ws)
            tmp = tmp[int(res.freq_fit):-int(res.freq_fit)]
            if not len(tmp):
                res.x_speed[drw][ws] = {'min': None, 'med': None, 'avg': None, 'max': None, 'p10': None, 'p90': None}
            else:
                tmp = np.multiply(tmp, res.drawing.params.radius * 1000.)
                res.x_speed[drw][ws] = {'min': np.min(tmp),
                                        'med': np.median(tmp),
                                        'avg': np.mean(tmp),
                                        'max': np.max(tmp),
                                        'p10': np.percentile(tmp, 10.),
                                        'p90': np.percentile(tmp, 90.)}

    res.x_acc = {}
    for drw in [True, False, None]:
        res.x_acc[drw] = {}
        for ws in cfg.speed_win_ms:
            tmp = _win_calc(trace_acc, drw, ws)
            tmp = tmp[int(res.freq_fit):-int(res.freq_fit)]
            if not len(tmp):
                res.x_acc[drw][ws] = {'min': None, 'med': None, 'avg': None, 'max': None, 'p10': None, 'p90': None}
            else:
                tmp = np.multiply(np.abs(tmp), res.drawing.params.radius * 1000.)
                res.x_acc[drw][ws] = {'min': np.min(tmp),
                                      'med': np.median(tmp),
                                      'avg': np.mean(tmp),
                                      'max': np.max(tmp),
                                      'p10': np.percentile(tmp, 10.),
                                      'p90': np.percentile(tmp, 90.)}

    # tremor amplitude
    def _win_calc(d, w):
        smp = int(res.freq_fit * (w / 1000.))
        win = scipy.signal.gaussian(smp, 7.)
        win /= np.sum(win)
        trace_x = np.convolve(res.trace.X, win, 'same')
        trace_y = np.convolve(res.trace.Y, win, 'same')
        sp = np.sqrt(
            np.square(trace_x - res.trace.X) +
            np.square(trace_y - res.trace.Y))
        # print(w)
        # if w == 150:
        #     from matplotlib import pyplot as plt
        #     plt.plot(res.trace.X, res.trace.Y, label='orig')
        #     plt.plot(trace_x, trace_y, label='new')
        #     plt.show()
        if d == None:
            return sp
        fin_sp = []
        for seg in irlsplit(len(res.trace.index), diff_nz_idx(res.trace.D)):
            if res.trace.D.iloc[seg[0]] == d:
                fin_sp += list(seg_slice(sp, *seg))
        return fin_sp

    res.x_tamp = {}
    for drw in [True, False, None]:
        res.x_tamp[drw] = {}
        for ws in cfg.speed_win_ms:
            tmp = _win_calc(drw, ws)
            tmp = tmp[int(res.freq_fit):-int(res.freq_fit)]
            if not len(tmp):
                res.x_tamp[drw][ws] = {'min': None, 'med': None, 'avg': None, 'max': None, 'p10': None, 'p90': None}
            else:
                tmp = np.multiply(tmp, res.drawing.params.radius)
                res.x_tamp[drw][ws] = {'min': np.min(tmp),
                                       'med': np.median(tmp),
                                       'avg': np.mean(tmp),
                                       'max': np.max(tmp),
                                       'p10': np.percentile(tmp, 10.),
                                       'p90': np.percentile(tmp, 90.)}

    def fta(trace_v, trace_fft, trace_freqs, buck_pref, peak_pref):
        trace_fft = abs(trace_fft[0:int(len(trace_v) / 2)])
        trace_freqs = trace_freqs[0:int(len(trace_v) / 2)]

        # buckets
        bucket_count = 28
        for x in range(bucket_count):
            b_span = 14. / bucket_count
            b_range = (2. + b_span * x, 2. + b_span * x + b_span)
            b_freq_range = (trace_freqs >= b_range[0]) & (trace_freqs < b_range[1])
            b_pwr = sum(trace_fft[b_freq_range]) / sum(b_freq_range)
            getattr(res, buck_pref)[x] = {'RANGE': b_range, 'PWR': b_pwr, 'SMP': sum(b_freq_range)}

        # peak/pwr
        filt_smp = int(res.freq_fit)
        filt_win = scipy.signal.gaussian(filt_smp, 7.)
        filt_win /= np.sum(filt_win)
        trace_fft = np.convolve(trace_fft, filt_win, 'same')
        #filt_range = (trace_freqs >= 1.) #& (trace_freqs < 16.)
        #trace_fft = trace_fft[filt_range]
        #trace_freqs = trace_freqs[filt_range]
        fft_peaks = sp.signal.find_peaks_cwt(trace_fft, np.arange(5, 6), min_snr=2.)
        fft_best_peak = None
        for x in fft_peaks:
            if x < len(trace_freqs) and trace_freqs[x] >= 2. and trace_freqs[x] < 32. and \
               ((fft_best_peak is None) or (trace_fft[x] > fft_best_peak[1])):
                fft_best_peak = (trace_freqs[x], trace_fft[x])
        if fft_best_peak:
            setattr(res, peak_pref + '_peak_hz', fft_best_peak[0])
            setattr(res, peak_pref + '_peak_pwr', fft_best_peak[1])

    # weight tremor frequency
    trace_v = res.trace.W[int(res.freq_fit):-int(res.freq_fit)]
    if len(trace_v) > int(res.freq_fit * 2):
        trace_fft = sp.fft(trace_v * np.blackman(len(trace_v)))
        trace_freqs = sp.fftpack.fftfreq(len(trace_v), d=1./res.freq_fit)
        fta(trace_v, trace_fft, trace_freqs, 'x_buck', 'x_freq')

    # xy tremor frequency
    if max_drw_trace is not None and len(max_drw_trace) > int(res.freq_fit * 2):
        trace_v = [complex(max_drw_trace[0].iloc[i], max_drw_trace[1].iloc[i]) for i in range(len(max_drw_trace[0]))]
        trace_v = trace_v[int(res.freq_fit):-int(res.freq_fit)]
        if len(trace_v) > int(res.freq_fit * 2):
            trace_fft = sp.fft(trace_v * np.blackman(len(trace_v)))
            trace_freqs = sp.fftpack.fftfreq(len(trace_v), d=1./res.freq_fit)
            fta(trace_v, trace_fft, trace_freqs, 'xy_buck', 'xy_freq')


# Main entry
def analyze(record, cfg, pmap, idx=0):
    res = AnalysisData()
    res.cfg = cfg
    try:
        _recalibrate(res, record)
        _remap(res, record, pmap, idx)
        _requantize(res, record, cfg)
        _cleanup(res, record, cfg)
        _analyze_test(res, record, cfg)
    except AnalysisException as e:
        res.error = e
    return res
