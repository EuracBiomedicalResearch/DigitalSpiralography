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
def get_tablet_device():
    if QExtTabletWindow.get_device_count() < 1:
        pd = QtGui.QProgressDialog(translate("tablet", "Waiting for tablet device ..."),
                                   QtCore.QString(), 0, 0, None)
        pd.setWindowTitle(Consts.APP_NAME)
        pd.setWindowModality(QtCore.Qt.ApplicationModal)
        pd.show()

        while QExtTabletWindow.get_device_count() < 1 and pd.isVisible():
            QtGui.QApplication.processEvents()
            time.sleep(Consts.APP_DELAY)

        pd.close()
        pd.deleteLater()

    if QExtTabletWindow.get_device_count() < 1:
        raise QExtTabletWindow.QExtTabletException("No available tablet devices")

    return QExtTabletWindow.get_device(0)
