# -*- coding: utf-8 -*-
"""Entry point for Visualizer"""

# imports
import Visualizer
import sys


# main module
if __name__ == '__main__':
    app = Visualizer.Application(sys.argv)
    sys.exit(app.exec_())
