# -*- coding: utf-8 -*-
"""Various ID validation functions"""

# local modules
import Verhoeff
from Intl import translate

# system modules
from PyQt4 import QtGui


# implementation
def validate_aid(buf):
    return buf.isdigit() and Verhoeff.validate(buf)

def validate_aid_err(buf):
    ret = validate_aid(buf)
    if not ret:
        title = translate("ID", "Invalid Patient ID")
        msg = translate("ID", "The specified patient ID is invalid")
        QtGui.QMessageBox.critical(None, title, msg)
    return ret

def validate_tid(buf):
    return (len(buf) > 1 and
            buf[0] == 'T' and
            buf[1:].isdigit() and
            Verhoeff.validate(buf[1:]))

def validate_tid_err(buf):
    ret = validate_tid(buf)
    if not ret:
        title = translate("ID", "Invalid Tablet ID")
        msg = translate("ID", "The specified tablet ID is invalid")
        QtGui.QMessageBox.critical(None, title, msg)
    return ret
