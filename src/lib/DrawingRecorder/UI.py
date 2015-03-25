# -*- coding: utf-8 -*-
"""UI helpers"""

# local modules
from . import Paths

# system modules
import os
from PyQt4 import QtCore, QtGui, uic


# implementation
def translate(ctx, msg, cmt=None):
    return unicode(QtGui.QApplication.translate(ctx, msg, cmt))

def init_intl(file):
    path = os.path.join(Paths.INTL, file)
    translator = QtCore.QTranslator(QtGui.QApplication.instance())
    if translator.load(QtCore.QLocale.system(), path, "."):
        QtGui.QApplication.installTranslator(translator)

def load_ui(obj, file):
    cwd = os.getcwd()
    try:
        # chdir to the "ui" directory to preserve icon paths
        os.chdir(Paths.UI)

        # setup the form and attach it to obj
        form, _ = uic.loadUiType(file)
        ret = form()
        ret.setupUi(obj)
    finally:
        # switch back
        os.chdir(cwd)
    return ret
