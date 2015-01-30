# -*- coding: utf-8 -*-
"""Pandas helpers"""

# system modules
import pandas as pd
import csv


def read_tab(fd_or_path, compat=False, **kwargs):
    return pd.read_table(fd_or_path, sep='\t', quoting=csv.QUOTE_NONE, na_values='',
                         encoding='utf-8', dtype=str, **kwargs)


def write_tab(data, fd_or_path, compat=False, **kwargs):
    return data.to_csv(fd_or_path, sep='\t', index=False, quoting=csv.QUOTE_NONE,
                       na_rep='', encoding='utf-8', **kwargs)
