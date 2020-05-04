# -*- coding: utf-8 -*-
"""UI helpers"""

# local modules
from . import Paths

# system modules
import os, sys
from PyQt5 import QtCore, QtWidgets, uic


# implementation
def translate(ctx, msg, cmt=None):
    return QtWidgets.QApplication.translate(ctx, msg, cmt)

def init_intl(file):
    path = os.path.join(Paths.INTL, file)
    translator = QtCore.QTranslator(QtWidgets.QApplication.instance())
    if translator.load(QtCore.QLocale.system(), path, "."):
        QtWidgets.QApplication.installTranslator(translator)

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
