# -*- coding: utf-8 -*-
"""Tablet handling functions"""

# local modules
from . import Consts
from .UI import translate

# Qt
from PyQt4 import QtCore, QtGui
import QExtTabletWindow

# system modules
import time


# get default tablet device or wait for it
def get_tablet_device(device=None, waitfor=True):
    if QExtTabletWindow.get_device_count() <= (device or 0) and waitfor == True:
        pd = QtGui.QProgressDialog(translate("tablet", "Waiting for tablet device ..."),
                                   QtCore.QString(), 0, 0, None)
        pd.setWindowTitle(Consts.APP_NAME)
        pd.setWindowModality(QtCore.Qt.ApplicationModal)
        pd.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint | \
                          QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowSystemMenuHint)
        pd.show()
        while QExtTabletWindow.get_device_count() < 1 and pd.isVisible():
            QtGui.QApplication.processEvents()
            time.sleep(Consts.APP_DELAY)
        pd.close()
        pd.deleteLater()

    dev_count = QExtTabletWindow.get_device_count()
    if dev_count <= (device or 0):
        raise QExtTabletWindow.QExtTabletException("No available tablet devices")
    elif dev_count > 1 and device is None:
        devices = [QExtTabletWindow.get_device(n) for n in range(dev_count)]
        dev_list = ["{}: {}".format(n + 1, dev.device_name)
                    for n, dev in enumerate(devices)]
        item, ret = QtGui.QInputDialog.getItem(None, Consts.APP_NAME,
                                               translate("tablet", "Select tablet device"),
                                               dev_list, editable=False)
        if not ret:
            raise QExtTabletWindow.QExtTabletException("User cancelled tablet selection")
        device = dev_list.index(item)

    return QExtTabletWindow.get_device(device or 0)
