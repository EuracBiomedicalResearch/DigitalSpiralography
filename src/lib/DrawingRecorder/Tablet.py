# -*- coding: utf-8 -*-
"""Tablet handling functions"""

# local modules
from .UI import translate
from .Shared import background_op
import QExtTabletWindow

# system modules
import time


# get default tablet device or wait for it
def get_tablet_device():
    if QExtTabletWindow.get_device_count() < 1:
        def wait_func():
            while QExtTabletWindow.get_device_count() < 1:
                time.sleep(1)
        background_op(translate("tablet", "Waiting for tablet device ..."), wait_func)
    return QExtTabletWindow.get_device(0)
