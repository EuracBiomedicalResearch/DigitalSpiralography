# -*- coding: utf-8 -*-
"""Main Drawing visualizer application"""

# local modules
import AID
import Spiral
import Analysis
import Consts

# system modules
import os
import uuid
import threading
from PyQt4 import QtCore, QtGui, uic


# main application
class Application(QtGui.QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        print args
