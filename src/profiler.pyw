# -*- coding: utf-8 -*-
"""Entry point for Profiler"""

# imports
import Profiler
import sys


# main module
if __name__ == '__main__':
    app = Profiler.Application(sys.argv)
    sys.exit(app.exec_())
