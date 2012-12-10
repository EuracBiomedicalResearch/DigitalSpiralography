# -*- coding: utf-8 -*-
"""Main Drawing recorder application"""

# local modules
import ID
import Analysis
import DrawingFactory
import DrawingWindow
import Shared
import Consts

# system modules
import os
import uuid
import datetime
import threading
from PyQt4 import QtCore, QtGui, uic


# implementation
class Params:
    def __init__(self, save_path, total_recordings,
                 installation_uuid, installation_stamp):
        self.save_path = save_path
        self.total_recordings = total_recordings
        self.installation_uuid = installation_uuid
        self.installation_stamp = installation_stamp



class NewCalibration(QtGui.QDialog):
    def __init__(self):
        super(NewCalibration, self).__init__()
        form, _ = uic.loadUiType("ui/newcalibration.ui")
        self._ui = form()
        self._ui.setupUi(self)


    def reset(self):
        self.tablet_id = None
        self.drawing = None
        self._ui.tablet_id.clear()
        self._ui.drawing_id.clear()
        self._ui.tablet_id.setFocus()


    def accept(self):
        # validate the tablet id
        self.tablet_id = str(self._ui.tablet_id.text())
        if not ID.validate_tid_err(self.tablet_id):
            return self.reset()

        # validate the drawing id
        self.drawing = DrawingFactory.from_id(str(self._ui.drawing_id.text()))
        if not self.drawing:
            QtGui.QMessageBox.critical(None, "Invalid drawing ID",
                                       "The specified drawing ID is invalid")
            return self.reset()

        self.done(QtGui.QDialog.Accepted)



class NewRecording(QtGui.QDialog):
    def __init__(self):
        super(NewRecording, self).__init__()
        form, _ = uic.loadUiType("ui/newrecording.ui")
        self._ui = form()
        self._ui.setupUi(self)


    def reset(self):
        self.aid = None
        self._ui.patient_id.clear()
        self._ui.patient_id.setFocus()


    def accept(self):
        self.aid = str(self._ui.patient_id.text())
        if not ID.validate_aid_err(self.aid):
            return self.reset()
        self.done(QtGui.QDialog.Accepted)



class EndRecording(QtGui.QDialog):
    def __init__(self):
        super(EndRecording, self).__init__()
        form, _ = uic.loadUiType("ui/endrecording.ui")
        self._ui = form()
        self._ui.setupUi(self)
        self._ui.save_path_btn.clicked.connect(self.on_save_path)

        self._file_browser = QtGui.QFileDialog(self)
        self._file_browser.setFileMode(QtGui.QFileDialog.AnyFile)
        self._file_browser.setOption(QtGui.QFileDialog.DontConfirmOverwrite)
        self._file_browser.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        self._file_browser.setFilter("Recordings (*.yaml.gz)")


    def reset(self, save_path, record):
        self.aid = record.aid
        self._ui.patient_id.setText(self.aid)

        self.save_path = save_path
        self._ui.save_path.setText(self.save_path)

        self._ui.date_time.setText(record.recording.session_start.strftime("%c"))
        self._ui.length.setText(str(record.recording.events[-1].stamp -
                                    record.recording.events[0].stamp))

        warn = record.check_warnings()
        font = self._ui.warnings.font()
        if warn:
            font.setBold(True)
            self._ui.warnings.setText(", ".join(warn))
        else:
            font.setBold(False)
            self._ui.warnings.setText("-")
        self._ui.warnings.setFont(font)

        self.pat_type = None
        self._ui.pat_type.setCurrentIndex(0)

        self.pat_handedness = None
        self._ui.pat_handedness.setCurrentIndex(0)

        self.pat_hand = None
        self._ui.pat_hand.setCurrentIndex(0)

        self.comments = None
        self._ui.comments.clear()
        self._ui.comments.setFocus()


    def on_save_path(self):
        (dir, name) = os.path.split(unicode(self._ui.save_path.text()))
        self._file_browser.setDirectory(dir)
        self._file_browser.selectFile(name)
        if self._file_browser.exec_():
            save_path = os.path.relpath(unicode(self._file_browser.selectedFiles()[0]))
            self._ui.save_path.setText(save_path)


    def reject(self):
        ret = QtGui.QMessageBox.warning(self, "Discard recording",
                                        "Are you sure you want to discard the acquired drawing?",
                                        "No", "Yes, discard")
        if ret:
            self.done(QtGui.QDialog.Rejected)


    def accept(self):
        self.aid = str(self._ui.patient_id.text())
        self.pat_type = str(self._ui.pat_type.currentText()) \
          if self._ui.pat_type.currentIndex() else None
        self.pat_handedness = str(self._ui.pat_handedness.currentText()) \
          if self._ui.pat_handedness.currentIndex() else None
        self.pat_hand = str(self._ui.pat_hand.currentText()) \
          if self._ui.pat_hand.currentIndex() else None
        self.comments = unicode(self._ui.comments.toPlainText())
        self.save_path = unicode(self._ui.save_path.text())

        # validate AID
        if not ID.validate_aid_err(self.aid):
            return

        # check if the file already exists
        if os.path.exists(self.save_path):
            msg = (u"The file {} already exists. " +
                   u"Try with a different file name!").format(self.save_path)
            QtGui.QMessageBox.critical(self, "Save failure", msg)
            return

        self.done(QtGui.QDialog.Accepted)



class MainWindow(QtGui.QMainWindow):
    def __init__(self, params):
        super(MainWindow, self).__init__()
        form, _ = uic.loadUiType("ui/main.ui")
        self._ui = form()
        self._ui.setupUi(self)

        # signals
        self._ui.save_path_btn.clicked.connect(self.on_save_path)
        self._ui.save_path.editingFinished.connect(self.on_save_path_changed)
        self._ui.info.clicked.connect(self.on_info)
        self._ui.calibrate.clicked.connect(self.on_calibrate)
        self._ui.new_recording.clicked.connect(self.on_new_recording)

        # dialogs
        self._new_calibration_dialog = NewCalibration()
        self._new_recording_dialog = NewRecording()
        self._end_recording_dialog = EndRecording()
        self._drawing_window = DrawingWindow.DrawingWindow()
        self._dir_browser = QtGui.QFileDialog(self)
        self._dir_browser.setFileMode(QtGui.QFileDialog.Directory)
        self._dir_browser.setOption(QtGui.QFileDialog.ShowDirsOnly)

        # parameters/initial state
        self.set_params(params)
        self.reset_calibration()
        self.drawing_number = 0


    def reset_calibration(self):
        self.calibration_age = 0
        self._ui.new_recording.setEnabled(False)
        self._ui.tablet_id.setText("-")
        self._ui.drawing_id.setText("-")
        self._ui.last_calibration.setText("-")


    def set_params(self, params):
        self.params = params
        self._ui.save_path.setText(params.save_path)


    def on_info(self, ev):
        msg = "{} {} {}".format(Consts.APP_ORG, Consts.APP_NAME, Consts.APP_VERSION)
        msg += "\nTotal recordings: " + str(self.params.total_recordings)
        msg += "\nInst. UUID: " + self.params.installation_uuid
        msg += "\nInst. Date: " + self.params.installation_stamp
        QtGui.QMessageBox.about(self, "About DrawingRecorder", msg)


    def on_save_path(self):
        self._dir_browser.setDirectory(self.params.save_path)
        if self._dir_browser.exec_():
            save_path = os.path.relpath(unicode(self._dir_browser.selectedFiles()[0]))
            self.set_save_path(save_path)


    def on_save_path_changed(self):
        self.params.save_path = unicode(self._ui.save_path.text())


    def set_save_path(self, save_path):
        self._ui.save_path.setText(save_path)
        self.on_save_path_changed()


    def on_calibrate(self):
        # setup the tablet id/drawing
        self._new_calibration_dialog.reset()
        if not self._new_calibration_dialog.exec_():
            return

        # perform the actual calibration
        self.reset_calibration()
        self._drawing_window.set_params(self._new_calibration_dialog.tablet_id,
                                        self._new_calibration_dialog.drawing)
        self._drawing_window.reset(DrawingWindow.Mode.Calibrate)
        if self._drawing_window.exec_():
            self._ui.new_recording.setEnabled(True)
            self._ui.tablet_id.setText(
                self._drawing_window.calibration.tablet_id)
            self._ui.drawing_id.setText(
                self._drawing_window.drawing.id + ": " +
                self._drawing_window.drawing.str)
            self._ui.last_calibration.setText(
                self._drawing_window.calibration.stamp.strftime("%c"))


    def on_new_recording(self):
        self._new_recording_dialog.reset()
        if not self._new_recording_dialog.exec_():
            return
        self._drawing_window.reset(DrawingWindow.Mode.Record)
        if not self._drawing_window.exec_():
            return

        # update stats
        self.drawing_number += 1
        self.calibration_age += 1
        self.params.total_recordings += 1

        extra_data = {"drawing_number": self.drawing_number,
                      "total_recordings": self.params.total_recordings,
                      "installation_uuid": self.params.installation_uuid,
                      "installation_stamp": self.params.installation_stamp}
        record = Analysis.DrawingRecord(self._new_recording_dialog.aid,
                                        self._drawing_window.drawing,
                                        self._drawing_window.calibration,
                                        self.calibration_age,
                                        self._drawing_window.recording,
                                        None, None, None, extra_data)

        # guess a decent path name
        save_path = record.recording.session_start.strftime("%Y%m%d")
        save_path = u"{}_{}_{}.yaml.gz".format(save_path,
                                               record.aid,
                                               self.drawing_number)
        save_path = os.path.join(self.params.save_path, save_path)

        # keep trying until save is either aborted or succeeds
        self._end_recording_dialog.reset(save_path, record)
        while self._end_recording_dialog.exec_():
            record.aid = self._end_recording_dialog.aid
            record.pat_type = self._end_recording_dialog.pat_type
            record.pat_handedness = self._end_recording_dialog.pat_handedness
            record.pat_hand = self._end_recording_dialog.pat_hand
            record.comments = self._end_recording_dialog.comments
            save_path = self._end_recording_dialog.save_path
            try:
                # put save into a background thread
                Shared.background_op("Saving, please wait...",
                                     lambda: Analysis.DrawingRecord.save(record, save_path),
                                     self)
            except IOError as e:
                msg = (u"Cannot save recording to {}: {}! " +
                       u"Try with a different file name!").format(save_path, e.strerror)
                QtGui.QMessageBox.critical(self, "Save failure", msg)
            else:
                break


# main application
class Application(QtGui.QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)

        # initialize the default settings
        self.settings = QtCore.QSettings(Consts.APP_ORG, Consts.APP_NAME)
        params = Params(unicode(self.settings.value("save_path", "recordings").toString()),
                        self.settings.value("total_recordings", 0).toInt()[0],
                        str(self.settings.value("installation_uuid", uuid.getnode()).toString()),
                        str(self.settings.value("installation_stamp", str(datetime.datetime.now())).toString()))

        # initialize
        self.main_window = MainWindow(params)
        self.main_window.show()
        self.lastWindowClosed.connect(self._on_close)

    def _on_close(self):
        params = self.main_window.params
        self.settings.setValue("save_path", params.save_path)
        self.settings.setValue("total_recordings", params.total_recordings)
        self.settings.setValue("installation_uuid", params.installation_uuid)
        self.settings.setValue("installation_stamp", params.installation_stamp)
