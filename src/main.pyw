# -*- coding: utf-8 -*-
"""Entry point"""

# imports
import Application
import sys


# main module
if __name__ == '__main__':
    app = Application.Application(sys.argv)
    sys.exit(app.exec_())
