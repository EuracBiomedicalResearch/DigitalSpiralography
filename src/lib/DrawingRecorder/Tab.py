# -*- coding: utf-8 -*-
"""Tabular file handling"""

from __future__ import print_function
import io


class TabException(IOError):
    def __init__(self, fd, error):
        self.fd = fd
        super(TabException, self).__init__(error)


class TabReader(object):
    def __init__(self, fd_or_path, columns=None, types=None):
        self._fd = io.open(fd_or_path, 'r', encoding='utf-8') \
                   if isinstance(fd_or_path, basestring) else fd_or_path
        self._types = types if types is not None else {}
        self._lno = 1

        # check for header
        line = self._fd.readline().rstrip('\n')
        if not line:
            raise TabException(self._fd, 'File has no header/empty file')

        # get/check column names
        self._cols = line.split('\t')
        if columns is not None:
            for col in columns:
                if col not in self._cols:
                    raise TabException(self._fd, 'Required column {} not found'.format(col))


    def __iter__(self):
        return self


    def read(self):
        line = self._fd.readline()
        if not line:
            return None

        self._lno += 1
        cols = line.rstrip('\n').split('\t')
        if len(cols) != len(self._cols):
            raise TabException(self._fd, "Variable number of columns at line {}".format(self._lno))

        row = {}
        for i, v in enumerate(cols):
            col = self._cols[i]
            typ = self._types.get(col, unicode)
            v = typ(v) if isinstance(typ, basestring) or len(v) != 0 else None
            row[col] = v

        return row


    def next(self):
        row = self.read()
        if row is None:
            raise StopIteration()
        return row



def _check_str(v):
    for c in ['\n', '\t']:
        if c in v:
            raise ValueError(v)


class TabWriter(object):
    def __init__(self, fd_or_path, columns):
        self._fd = io.open(fd_or_path, 'w', encoding='utf-8') \
                   if isinstance(fd_or_path, basestring) else fd_or_path
        self._cols = columns

        # write header
        for col in columns:
            _check_str(col)
        line = u'\t'.join(columns)
        print(line, file=self._fd)


    def write(self, row, default=False):
        buf = []
        for col in self._cols:
            v = row.get(col) if default else row[col]
            if v is None:
                v = u''
            else:
                v = unicode(v)
                _check_str(v)
            buf.append(v)
        print(u'\t'.join(buf), file=self._fd)
