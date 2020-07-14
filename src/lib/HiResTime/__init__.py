# -*- coding: utf-8 -*-
"""Hi-res time sampling"""

import datetime
import sys
import time

__all__ = ('resync', 'now')


if sys.platform == 'win32':
    # On Win32 time() has only sub-second resolution. Use clock() instead,
    # which is a sub-ms resolution, raw monotonic clock.
    __ts_init = time.time() - time.clock()

    def resync():
        global __ts_init
        __ts_init = time.time() - time.clock()

    def now():
        return datetime.datetime.fromtimestamp(__ts_init + time.clock())


elif sys.platform == 'linux2':
    # On Linux we use CLOCK_MONOTONIC_RAW though the clock_gettime() function.
    import ctypes, os, time

    CLOCK_MONOTONIC_RAW = 4

    class timespec(ctypes.Structure):
        _fields_ = (
            ('tv_sec', ctypes.c_long),
            ('tv_nsec', ctypes.c_long),
    )

    librt = ctypes.CDLL('librt.so.1', use_errno=True)
    _clock_gettime = librt.clock_gettime
    _clock_gettime.argtypes = (ctypes.c_int, ctypes.POINTER(timespec))

    def clock_gettime():
        t = timespec()
        if _clock_gettime(CLOCK_MONOTONIC_RAW, ctypes.byref(t)) != 0:
            errno_ = ctypes.get_errno()
            raise OSError(errno_, os.strerror(errno_))
        return t.tv_sec + t.tv_nsec * 1e-9

    __ts_init = time.time() - clock_gettime()

    def resync():
        global __ts_init
        __ts_init = time.time() - clock_gettime()

    def now():
        return datetime.datetime.fromtimestamp(__ts_init + clock_gettime())


else:
    # On Posix systems time() calls gettimeofday() and is an hi-res wall clock,
    # but is not monotonic and is affected by adjtime.
    now = datetime.datetime.now

    def resync():
        pass
