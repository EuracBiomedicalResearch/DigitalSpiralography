# -*- coding: utf-8 -*-
"""Various ID validation functions"""

# local modules
from . import Verhoeff
from .UI import translate

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

def validate_sid(buf):
    return (len(buf) > 1 and
            buf[0] == 'S' and
            buf[1:].isdigit() and
            Verhoeff.validate(buf[1:]))

def validate_sid_err(buf):
    ret = validate_sid(buf)
    if not ret:
        title = translate("ID", "Invalid Pen ID")
        msg = translate("ID", "The specified pen ID is invalid")
        QtGui.QMessageBox.critical(None, title, msg)
    return ret
