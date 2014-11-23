# -*- coding: utf-8 -*-
"""UI helpers"""

# local modules
import Paths

# system modules
import os
from PyQt4 import QtCore, QtGui, uic


# implementation
def translate(ctx, msg):
    return unicode(QtGui.QApplication.translate(ctx, msg))

def init_intl(file):
    path = os.path.join(Paths.INTL, file)
    translator = QtCore.QTranslator(QtGui.QApplication.instance())
    if translator.load(QtCore.QLocale.system(), path, "."):
        QtGui.QApplication.installTranslator(translator)

def load_ui(obj, file):
    # chdir to the "ui" directory to preserve icon paths
    cwd = os.getcwd()
    os.chdir(Paths.UI)

    # setup the form and attach it to obj
    form, _ = uic.loadUiType(file)
    ret = form()
    ret.setupUi(obj)

    # switch back
    os.chdir(cwd)
    return ret
