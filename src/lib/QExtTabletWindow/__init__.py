# -*- coding: utf-8 -*-
from __future__ import print_function
import sys

from .core import *

if sys.platform != 'win32':
    from .generic import *
else:
    from .wintab import *
