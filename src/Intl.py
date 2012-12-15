# -*- coding: utf-8 -*-
"""Internationalization helpers"""

# imports
import os
from PyQt4 import QtCore, QtGui


# implementation
def translate(ctx, msg):
    return unicode(QtGui.QApplication.translate(ctx, msg))

def initialize(file):
    path = os.path.join("intl", file)
    translator = QtCore.QTranslator(QtGui.QApplication.instance())
    if translator.load(QtCore.QLocale.system(), path, "."):
        QtGui.QApplication.installTranslator(translator)
