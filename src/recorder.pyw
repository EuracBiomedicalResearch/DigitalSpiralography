# -*- coding: utf-8 -*-
"""Entry point for Recorder"""

# imports
import Recorder
import sys


# main module
if __name__ == '__main__':
    app = Recorder.Application(sys.argv)
    sys.exit(app.exec_())
