#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stylus usage report generator"""

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Data
from DrawingRecorder import PdUtil

# system modules
import argparse
import pandas as pd


def __main__():
    ap = argparse.ArgumentParser(description='Stylus usage report generator')
    ap.add_argument('-o', dest='output', help='Output report file', required=True)
    ap.add_argument('-f', dest='freq', help='Resolution (interval)', default='d')
    ap.add_argument('files', nargs='+', help='drwstat output files')
    args = ap.parse_args()

    data = pd.DataFrame({'SID': pd.Series(dtype=str),
                         'TS': pd.Series(dtype=int)})

    # load/aggregate all files
    for path in args.files:
        tmp = PdUtil.read_tab(path)
        data = pd.merge(data, pd.DataFrame({'SID': tmp['CAL_SID'],
                                            'TS': tmp['REC_TS'].astype(int)}),
                        on=['SID', 'TS'], how='outer')

    idx = pd.to_datetime(data['TS'], unit='s')
    data.set_index(pd.DatetimeIndex(idx, tz='UTC'), inplace=True)
    data = data.groupby('SID')

    # generate counters
    sur = {}
    for sid, group in data:
        group = group.resample(args.freq).count()
        rep = []
        acc = 0
        for i, cnt in group['TS'].items():
            if cnt:
                rep.append(Data.StylusUsageMark(i.to_pydatetime(), int(acc)))
                acc += int(cnt)
        sur[sid] = rep

    # save
    data = Data.StylusUsageReport(sur)
    Data.StylusUsageReport.save(data, args.output)


if __name__ == '__main__':
    __main__()
