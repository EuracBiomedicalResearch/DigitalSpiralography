# -*- coding: utf-8 -*-
"""Various ID validation functions"""

# imports
import Verhoeff
from PyQt4 import QtGui


# implementation
def validate_aid(buf):
    return buf.isdigit() and Verhoeff.validate(buf)

def validate_aid_err(buf):
    ret = validate_aid(buf)
    if not ret:
        QtGui.QMessageBox.critical(None, "Invalid Patient ID",
                                   "The specified patient ID is invalid")
    return ret

def validate_tid(buf):
    return (len(buf) > 1 and
            buf[0] == 'T' and
            buf[1:].isdigit() and
            Verhoeff.validate(buf[1:]))

def validate_tid_err(buf):
    ret = validate_tid(buf)
    if not ret:
        QtGui.QMessageBox.critical(None, "Invalid Tablet ID",
                                   "The specified tablet ID is invalid")
    return ret
