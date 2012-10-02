# -*- coding: utf-8 -*-
"""Main Drawing recorder application"""

# local modules
import AID
import Spiral
import Analysis
import DrawingWindow
import Consts

# system modules
import os
import uuid
from PyQt4 import QtCore, QtGui, uic


# implementation
class Params:
    def __init__(self, save_path, total_recordings, installation_uuid):
        self.save_path = save_path
        self.total_recordings = total_recordings
        self.installation_uuid = installation_uuid



class NewRecording(QtGui.QDialog):
    def __init__(self):
        super(NewRecording, self).__init__()
        form, _ = uic.loadUiType("ui/newrecording.ui")
        self._ui = form()
        self._ui.setupUi(self)


    def reset(self):
        self.aid = None
        self._ui.patient_id.clear()
        self._ui.patient_id.setFocus(True)


    def accept(self):
        self.aid = str(self._ui.patient_id.text())
        if AID.validate_with_error(self.aid):
            self.done(QtGui.QDialog.Accepted)



class EndRecording(QtGui.QDialog):
    def __init__(self):
        super(EndRecording, self).__init__()
        form, _ = uic.loadUiType("ui/endrecording.ui")
        self._ui = form()
        self._ui.setupUi(self)
        self._ui.save_path_btn.clicked.connect(self.on_save_path)


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

        self.comments = None
        self._ui.comments.clear()
        self._ui.comments.setFocus(True)


    def on_save_path(self):
        save_path = QtGui.QFileDialog.getSaveFileName(self, "Save File",
                                                      self._ui.save_path.text(),
                                                      "Recordings (*.yaml.gz)");
        if save_path:
            self._ui.save_path.setText(save_path)


    def accept(self):
        self.aid = str(self._ui.patient_id.text())
        self.comments = str(self._ui.comments.toPlainText())
        self.save_path = str(self._ui.save_path.text())

        # validate AID
        if not AID.validate_with_error(self.aid):
            return

        # check if the file already exists
        if os.path.exists(self.save_path):
            msg = ("The file {} already exists. " +
                   "Try with a different file name!").format(self.save_path)
            QtGui.QMessageBox.critical(self, "Save failure", msg)
            return

        self.done(QtGui.QDialog.Accepted)



class MainWindow(QtGui.QMainWindow):
    def __init__(self, drawing, params):
        super(MainWindow, self).__init__()
        form, _ = uic.loadUiType("ui/main.ui")
        self._ui = form()
        self._ui.setupUi(self)

        # signals
        self._ui.save_path_btn.clicked.connect(self.on_save_path)
        self._ui.calibrate.clicked.connect(self.on_calibrate)
        self._ui.new_recording.clicked.connect(self.on_new_recording)

        # dialogs
        self._new_recording_dialog = NewRecording()
        self._end_recording_dialog = EndRecording()
        self._drawing_window = DrawingWindow.DrawingWindow()
        self._dir_browser = QtGui.QFileDialog()
        self._dir_browser.setFileMode(QtGui.QFileDialog.Directory)
        self._dir_browser.setOption(QtGui.QFileDialog.ShowDirsOnly)

        # parameters
        self.set_drawing(drawing)
        self.set_params(params)

        # some running statistics
        self.drawing_number = 0
        self.calibration_age = 0


    def reset_calibration(self):
        self.calibration_age = 0
        self._ui.new_recording.setEnabled(False)
        self._ui.last_calibration.setText("-")


    def set_drawing(self, drawing):
        self._drawing_window.set_drawing(drawing)
        self._ui.drawing_dsc.setText(drawing.describe())
        self.reset_calibration()


    def set_params(self, params):
        self.params = params
        self._ui.save_path.setText(params.save_path)


    def on_save_path(self):
        if self._dir_browser.exec_():
            save_path = os.path.relpath(str(self._dir_browser.selectedFiles()[0]))
            self.set_save_path(save_path)


    def set_save_path(self, save_path):
        self.params.save_path = save_path
        self._ui.save_path.setText(save_path)


    def on_calibrate(self):
        self.reset_calibration()
        self._drawing_window.reset(DrawingWindow.Mode.Calibrate)
        if self._drawing_window.exec_():
            self._ui.new_recording.setEnabled(True)
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
                      "installation_uuid": self.params.installation_uuid}
        record = Analysis.DrawingRecord(self._new_recording_dialog.aid,
                                        self._drawing_window.drawing,
                                        self._drawing_window.calibration,
                                        self.calibration_age,
                                        self._drawing_window.recording,
                                        extra_data)

        # guess a decent path name
        save_path = record.recording.session_start.strftime("%Y%m%d")
        save_path = "{}_{}_{}.yaml.gz".format(save_path,
                                              record.aid,
                                              self.drawing_number)
        save_path = os.path.join(self.params.save_path, save_path)

        # keep trying until save is either aborted or succeeds
        self._end_recording_dialog.reset(save_path, record)
        while self._end_recording_dialog.exec_():
            record.aid = self._end_recording_dialog.aid
            record.comments = self._end_recording_dialog.comments
            save_path = self._end_recording_dialog.save_path
            try:
                record.save(save_path)
            except IOError as e:
                msg = ("Cannot save recording to {}: {}! " +
                       "Try with a different file name!").format(save_path, e.strerror)
                QtGui.QMessageBox.critical(self, "Save failure", msg)
            else:
                break


# main application
class Application(QtGui.QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)

        # initialize the default settings
        self.settings = QtCore.QSettings(Consts.APP_ORG, Consts.APP_NAME)
        params = Params(str(self.settings.value("save_path", "recordings").toString()),
                        self.settings.value("total_recordings", 0).toInt()[0],
                        str(self.settings.value("installation_uuid", uuid.getnode()).toString()))

        # create a spiral with our only current settings
        spiral = Spiral.Params(name = "SPR1",
                               diameter = 65,
                               turns = 5.,
                               direction = "CW")
        drawing = Spiral.Spiral(spiral)

        # initialize
        self.main_window = MainWindow(drawing, params)
        self.main_window.show()
        self.lastWindowClosed.connect(self._on_close)

    def _on_close(self):
        params = self.main_window.params
        self.settings.setValue("save_path", params.save_path)
        self.settings.setValue("total_recordings", params.total_recordings)
        self.settings.setValue("installation_uuid", params.installation_uuid)
