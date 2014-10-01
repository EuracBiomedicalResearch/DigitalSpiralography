# -*- coding: utf-8 -*-
"""UI helpers"""

# imports
import os
from PyQt4 import QtCore, QtGui, uic


# implementation
def translate(ctx, msg):
    return unicode(QtGui.QApplication.translate(ctx, msg))

def init_intl(root, file):
    path = os.path.join(root, "src", "intl", file)
    translator = QtCore.QTranslator(QtGui.QApplication.instance())
    if translator.load(QtCore.QLocale.system(), path, "."):
        QtGui.QApplication.installTranslator(translator)

def load_ui(obj, root, file):
    # chdir to the "ui" directory to preserve icon paths
    cwd = os.getcwd()
    path = os.path.join(root, "src", "ui")
    os.chdir(path)

    # setup the form and attach it to obj
    form, _ = uic.loadUiType(file)
    ret = form()
    ret.setupUi(obj)

    # switch back
    os.chdir(cwd)
    return ret
