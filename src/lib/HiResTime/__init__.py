# -*- coding: utf-8 -*-
"""Hi-res time sampling"""

import datetime
import sys
import time

if sys.platform != 'win32':
    # On Posix systems time() calls gettimeofday() and is an hi-res wall clock
    now = datetime.datetime.now
else:
    # On Win32 time() has only sub-second resolution. Use clock() instead,
    # which is actually sub-ms resolution wall clock.
    __ts_init = time.time() - time.clock()

    def now():
        return datetime.datetime.fromtimestamp(__ts_init + time.clock())
