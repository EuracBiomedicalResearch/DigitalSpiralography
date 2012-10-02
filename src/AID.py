# -*- coding: utf-8 -*-
"""AID Validation"""

# imports
import Verhoeff
from PyQt4 import QtGui


# implementation
def validate(str):
    return str.isdigit() and Verhoeff.validate(str)

def validate_with_error(str):
    ret = validate(str)
    if not ret:
        QtGui.QMessageBox.critical(None, "Invalid Patient ID",
                                   "The specified patient ID is invalid")
    return ret
