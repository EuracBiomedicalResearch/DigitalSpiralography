#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Main Drawing recorder application"""

from __future__ import print_function

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import ID
from DrawingRecorder import Data
from DrawingRecorder.Data import PatHand, PatHandedness
from DrawingRecorder import DrawingFactory
from DrawingRecorder import DrawingWindow
from DrawingRecorder import Shared
from DrawingRecorder import Consts
from DrawingRecorder import UI
from DrawingRecorder.UI import translate

# system modules
import argparse
import datetime
import gc
import os
import uuid
from PyQt4 import QtCore, QtGui


# helpers
def _to_type(cb):
    val = cb.itemData(cb.currentIndex()).toPyObject()
    if type(val) is QtCore.QString:
        val = unicode(val)
    return val


def _set_type(cb, val):
    if val is None:
        cb.setCurrentIndex(0)
    else:
        cb.setCurrentIndex(cb.findData(val))


def _reset_grp_state(group):
    group.setExclusive(False)
    for button in group.buttons():
        if button.isChecked():
            button.setChecked(False)
    group.setExclusive(True)


# implementation
class Params(object):
    def __init__(self, proj_path, total_recordings,
                 installation_uuid, installation_stamp):
        self.proj_path = proj_path
        self.total_recordings = total_recordings
        self.installation_uuid = installation_uuid
        self.installation_stamp = installation_stamp



class NewCalibration(QtGui.QDialog):
    def __init__(self):
        super(NewCalibration, self).__init__()
        self._ui = UI.load_ui(self, "newcalibration.ui")


    def reset(self):
        self.oid = None
        self.tablet_id = None
        self.stylus_id = None
        self.drawing = None
        self._ui.operator_id.clear()
        self._ui.tablet_id.clear()
        self._ui.stylus_id.clear()
        self._ui.drawing_id.clear()
        self._ui.operator_id.setFocus()


    def accept(self):
        # validate the operator
        self.oid = str(self._ui.operator_id.text())
        if not self.oid:
            title = translate("recorder", "Invalid operator")
            msg = translate("recorder", "The specified operator is invalid")
            QtGui.QMessageBox.critical(None, title, msg)
            return self.reset()

        # ... tablet id
        self.tablet_id = str(self._ui.tablet_id.text())
        if not ID.validate_tid_err(self.tablet_id):
            return self.reset()

        # ... stylus id
        self.stylus_id = str(self._ui.stylus_id.text())
        if not ID.validate_sid_err(self.stylus_id):
            return self.reset()

        # ... drawing id
        self.drawing = DrawingFactory.from_id(str(self._ui.drawing_id.text()))
        if not self.drawing:
            title = translate("recorder", "Invalid drawing ID")
            msg = translate("recorder", "The specified drawing ID is invalid")
            QtGui.QMessageBox.critical(None, title, msg)
            return self.reset()

        self.done(QtGui.QDialog.Accepted)



class NewRecording(QtGui.QDialog):
    def __init__(self):
        super(NewRecording, self).__init__()
        self._ui = UI.load_ui(self, "newrecording.ui")


    def reset(self):
        self.oid = None
        self.aid = None
        self._ui.operator_id.clear()
        self._ui.patient_id.clear()
        self._ui.operator_id.setFocus()


    def accept(self):
        self.oid = str(self._ui.operator_id.text())
        self.aid = str(self._ui.patient_id.text())

        # validate the operator
        if not self.oid:
            title = translate("recorder", "Invalid operator")
            msg = translate("recorder", "The specified operator is invalid")
            QtGui.QMessageBox.critical(None, title, msg)
            return self.reset()

        # validate the AID
        if not ID.validate_aid_err(self.aid):
            return self.reset()
        self.done(QtGui.QDialog.Accepted)



class EndRecording(QtGui.QDialog):
    def __init__(self):
        super(EndRecording, self).__init__()
        self._ui = UI.load_ui(self, "endrecording.ui")
        self._ui.save_path_btn.clicked.connect(self.on_save_path)
        self._ui.next_hand_btn.clicked.connect(self.on_next_hand)

        self._file_browser = QtGui.QFileDialog(self)
        self._file_browser.setFileMode(QtGui.QFileDialog.AnyFile)
        self._file_browser.setOption(QtGui.QFileDialog.DontConfirmOverwrite)
        self._file_browser.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        ext_name = translate("recorder", "Recordings")
        self._file_browser.setFilter(ext_name + " (*.rec.yaml.gz)")

        pal = self._ui.preview.palette()
        pal.setColor(self._ui.preview.backgroundRole(), Consts.FILL_COLOR)
        self._ui.preview.setPalette(pal)


    def reset(self, config, record, preview, save_path, cycle_state):
        self.config = config
        cb = self._ui.pat_type
        cb.clear()
        cb.addItem(translate("types", "N/A"))
        for k, v in config.pat_types.iteritems():
            cb.addItem(v, k)

        self.oid = record.oid
        self._ui.operator_id.setText(self.oid)

        self.aid = record.aid
        self._ui.patient_id.setText(self.aid)

        self.save_path = save_path
        self._ui.save_path.setText(self.save_path)

        self._ui.date_time.setText(record.recording.session_start.strftime("%c"))
        if not record.recording.events:
            self._ui.length.setText("-")
        else:
            length = record.recording.events[-1].stamp - record.recording.events[0].stamp
            self._ui.length.setText(Shared.timedelta_min_sec(length))

        warn = record.check_warnings()
        font = self._ui.warnings.font()
        if warn:
            font.setBold(True)
            self._ui.warnings.setText(", ".join(warn))
        else:
            font.setBold(False)
            self._ui.warnings.setText("-")
        self._ui.warnings.setFont(font)

        self._orig_pat_type = record.pat_type
        self.pat_type = record.pat_type
        _set_type(self._ui.pat_type, self.pat_type)

        self._orig_pat_hand_cnt = record.pat_hand_cnt
        self.pat_hand_cnt = record.pat_hand_cnt
        if self.pat_hand_cnt == 1:
            self._ui.hand_cnt_1.setChecked(True)
        elif self.pat_hand_cnt == 2:
            self._ui.hand_cnt_2.setChecked(True)
        else:
            _reset_grp_state(self._ui.hand_cnt_grp)

        self._orig_pat_handedness = record.pat_handedness
        self.pat_handedness = record.pat_handedness
        if self.pat_handedness == PatHandedness.left:
            self._ui.handedness_left.setChecked(True)
        elif self.pat_handedness == PatHandedness.right:
            self._ui.handedness_right.setChecked(True)
        elif self.pat_handedness == PatHandedness.ambidextrous:
            self._ui.handedness_ambidextrous.setChecked(True)
        else:
            _reset_grp_state(self._ui.handedness_grp)

        for btn in self._ui.hand_grp.buttons():
            font = btn.font()
            font.setBold(False)
            btn.setFont(font)
        self._orig_pat_hand = record.pat_hand
        self.pat_hand = record.pat_hand
        if self.pat_hand == PatHand.left:
            self._ui.hand_left.setChecked(True)
            font = self._ui.hand_left.font()
            font.setBold(True)
            self._ui.hand_left.setFont(font)
        elif self.pat_hand == PatHand.right:
            self._ui.hand_right.setChecked(True)
            font = self._ui.hand_right.font()
            font.setBold(True)
            self._ui.hand_right.setFont(font)
        else:
            _reset_grp_state(self._ui.hand_grp)

        self.blood_drawn = record.extra_data.get("blood_drawn", None)
        self._orig_blood_drawn = self.blood_drawn
        if self.blood_drawn == True:
            self._ui.blood_drawn.setChecked(True)
        elif self.blood_drawn == False:
            self._ui.blood_not_drawn.setChecked(True)
        else:
            _reset_grp_state(self._ui.blood_grp)

        self.comments = None
        self._ui.comments.clear()
        self._ui.comments.setFocus()

        size = self._ui.preview.size()
        preview = preview.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self._ui.preview.setPixmap(preview)

        self.next_hand = None
        self.cycle_state = cycle_state
        self.allow_next = (cycle_state[0] < cycle_state[1])
        self._ui.next_hand_lbl.setVisible(self.allow_next)
        self._ui.next_hand_btn.setEnabled(self.allow_next)
        if self.allow_next:
            msg = translate("recorder", "Spiral {cycle}/{total}")
            msg = msg.format(cycle=cycle_state[0], total=cycle_state[1])
            self._ui.next_hand_lbl.setText(msg)


    def on_save_path(self):
        (dir, name) = os.path.split(unicode(self._ui.save_path.text()))
        self._file_browser.setDirectory(dir)
        self._file_browser.selectFile(name)
        if self._file_browser.exec_():
            save_path = os.path.relpath(unicode(self._file_browser.selectedFiles()[0]))
            self._ui.save_path.setText(save_path)


    def on_next_hand(self):
        self.accept(next_hand=True)


    def reject(self):
        title = translate("recorder", "Discard recording")
        msg = translate("recorder", "Are you sure you want to discard the acquired drawing?")
        ret = QtGui.QMessageBox.warning(self, title, msg,
                                        translate("recorder", "No"),
                                        translate("recorder", "Yes, discard"))
        if ret:
            self.done(QtGui.QDialog.Rejected)


    def accept(self, next_hand=False):
        self.oid = str(self._ui.operator_id.text())
        self.aid = str(self._ui.patient_id.text())
        self.pat_type = _to_type(self._ui.pat_type)

        self.pat_hand_cnt = 1 if self._ui.hand_cnt_1.isChecked() else \
          2 if self._ui.hand_cnt_2.isChecked() else \
          None

        self.pat_handedness = PatHandedness.left if self._ui.handedness_left.isChecked() else \
          PatHandedness.right if self._ui.handedness_right.isChecked() else \
          PatHandedness.ambidextrous if self._ui.handedness_ambidextrous.isChecked() else \
          None

        self.pat_hand = PatHand.left if self._ui.hand_left.isChecked() else \
          PatHand.right if self._ui.hand_right.isChecked() else \
          None

        self.blood_drawn = True if self._ui.blood_drawn.isChecked() else \
          False if self._ui.blood_not_drawn.isChecked() else \
          None

        self.comments = unicode(self._ui.comments.toPlainText())
        self.save_path = unicode(self._ui.save_path.text())

        # validate AID
        if not ID.validate_aid_err(self.aid):
            return

        # other mandatory fields
        if not self.oid:
            title = translate("recorder", "Invalid operator")
            msg = translate("recorder", "The specified operator is invalid")
            QtGui.QMessageBox.critical(None, title, msg)
            return

        if self.pat_type is None and not self.config.allow_no_pat_type:
            title = translate("recorder", "Patient type not set")
            msg = translate("recorder", "Patient type must be specified")
            QtGui.QMessageBox.critical(None, title, msg)
            return

        if self.pat_hand_cnt is None:
            title = translate("recorder", "Hand count not set")
            msg = translate("recorder", "Patient hand count must be specified")
            QtGui.QMessageBox.critical(None, title, msg)
            return

        if self.pat_handedness is None:
            title = translate("recorder", "Handedness not set")
            msg = translate("recorder", "Patient handedness must be specified")
            QtGui.QMessageBox.critical(None, title, msg)
            return

        if self.pat_hand is None:
            title = translate("recorder", "Hand not set")
            msg = translate("recorder", "Drawing hand must be specified")
            QtGui.QMessageBox.critical(None, title, msg)
            return

        if self.blood_drawn is None:
            title = translate("recorder", "Blood drawn not set")
            msg = translate("recorder", "Blood drawn state must be specified")
            QtGui.QMessageBox.critical(None, title, msg)
            return

        # check if the file already exists
        if os.path.exists(self.save_path):
            title = translate("recorder", "Save failure")
            msg = translate("recorder",
                            "The file {path} already exists. "
                            "Try with a different file name!")
            msg = msg.format(path=self.save_path)
            QtGui.QMessageBox.critical(self, title, msg)
            return

        # sanity checking
        if len(self.comments) < 3 and self.config.require_change_comments:
            # .. parameter consistency
            if self.cycle_state[0] > 1:
                broken_param = None
                if self.pat_type != self._orig_pat_type:
                    broken_param = translate("recorder", "Patient type", "param_changed")
                elif self.pat_handedness != self._orig_pat_handedness:
                    broken_param = translate("recorder", "Patient handedness", "param_changed")
                elif self.pat_hand_cnt != self._orig_pat_hand_cnt:
                    broken_param = translate("recorder", "Patient hand count", "param_changed")
                elif self.pat_hand != self._orig_pat_hand:
                    broken_param = translate("recorder", "Drawing hand", "param_changed")
                elif self._orig_blood_drawn is not None and self.blood_drawn != self._orig_blood_drawn:
                    broken_param = translate("recorder", "Blood drawn state", "param_changed")
                if broken_param is not None:
                    title = translate("recorder", "Patient parameters changed", "param_changed")
                    msg = translate("recorder", "{parameter} was changed, "
                                    "but no reason is given in the comments!\n\n"
                                    "Please write a reason in the comments!",
                                    "param_changed")
                    msg = msg.format(parameter=broken_param)
                    QtGui.QMessageBox.warning(self, title, msg)
                    return

            # .. ensure we really want to stop cycling
            if self.allow_next and not next_hand:
                title = translate("recorder", "Incomplete session")
                msg = translate("recorder", "Not all required drawings were collected "
                                "and no reason is given in the comments!\n\n"
                                "Please write a reason in the comments!")
                QtGui.QMessageBox.warning(self, title, msg)
                return

        self.next_hand = next_hand
        self.done(QtGui.QDialog.Accepted)



class MainWindow(QtGui.QMainWindow):
    def __init__(self, params):
        super(MainWindow, self).__init__()
        self._ui = UI.load_ui(self, "main.ui")

        # signals
        self._ui.proj_path_btn.clicked.connect(self.on_proj_path)
        self._ui.proj_path.editingFinished.connect(self.on_proj_path_changed)
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
        self.calibration_age = 0
        self.drawing_number = 0
        self.set_params(params)


    def on_data_changed(self):
        if self.config is not None:
            self._ui.proj_id.setText(self.config.project_id)
            self._ui.proj_name.setText(self.config.project_name)
        else:
            self._ui.proj_id.setText("-")
            self._ui.proj_name.setText("-")

        if self._drawing_window.calibration is not None:
            self._ui.tablet_id.setText(
                self._drawing_window.calibration.tablet_id)
            self._ui.stylus_id.setText(
                self._drawing_window.calibration.stylus_id)
            self._ui.drawing_id.setText(
                self._drawing_window.drawing.id + ": " +
                self._drawing_window.drawing.str)
            self._ui.last_calibration.setText(
                self._drawing_window.calibration.stamp.strftime("%c"))
        else:
            self._ui.tablet_id.setText("-")
            self._ui.stylus_id.setText("-")
            self._ui.drawing_id.setText("-")
            self._ui.last_calibration.setText("-")

        ready = self._drawing_window.calibration is not None and self.config is not None
        self._ui.new_recording.setEnabled(ready)


    def set_params(self, params):
        self.params = params
        self._ui.proj_path.setText(params.proj_path)

        # load configuration
        try:
            conf_path = os.path.join(self.params.proj_path, Consts.PROJ_CONFIG)
            self.config = Data.Config.load(conf_path)
        except:
            self.config = None

        self.on_data_changed()


    def on_info(self, ev):
        title = translate("recorder", "About DrawingRecorder")
        ver = "{} {} {}".format(Consts.APP_ORG, Consts.APP_NAME, Consts.APP_VERSION)
        about = translate("recorder",
                          "Total recordings: {total}\n"
                          "Inst. UUID: {uuid}\n"
                          "Inst. Date: {date}")
        about = about.format(total=str(self.params.total_recordings),
                             uuid=self.params.installation_uuid,
                             date=self.params.installation_stamp)
        QtGui.QMessageBox.about(self, title, ver + "\n" + about)


    def on_proj_path(self):
        self._dir_browser.setDirectory(self.params.proj_path)
        if self._dir_browser.exec_():
            proj_path = os.path.relpath(unicode(self._dir_browser.selectedFiles()[0]))
            self._ui.proj_path.setText(proj_path)
            self.on_proj_path_changed()


    def on_proj_path_changed(self):
        proj_path = unicode(self._ui.proj_path.text())
        if self.params.proj_path == proj_path:
            # do not re-validate when losing focus without changes
            return

        self.params.proj_path = unicode(self._ui.proj_path.text())
        conf_path = os.path.join(self.params.proj_path, Consts.PROJ_CONFIG)

        # show errors when configuring the recorder interactively
        try:
            self.config = Data.Config.load(conf_path)
        except Exception as e:
            self.config = None
            msg = translate("recorder",
                            "Invalid project directory {path}: {reason}")
            msg = msg.format(path=self.params.proj_path, reason=e)
            title = translate("recorder", "Project directory")
            QtGui.QMessageBox.critical(self, title, msg)

        self.on_data_changed()


    def on_calibrate(self):
        # setup the tablet id/drawing
        self._new_calibration_dialog.reset()
        if not self._new_calibration_dialog.exec_():
            return

        # perform the actual calibration
        self._drawing_window.set_params(self._new_calibration_dialog.oid,
                                        self._new_calibration_dialog.tablet_id,
                                        self._new_calibration_dialog.stylus_id,
                                        self._new_calibration_dialog.drawing)
        self._drawing_window.reset(DrawingWindow.Mode.Calibrate)
        self._drawing_window.exec_()
        self.on_data_changed()


    def new_recording(self, oid, aid,
                      pat_type=None, pat_hand_cnt=None, pat_handedness=None, pat_hand=None,
                      blood_drawn=None, cycle_state=(1,1)):
        # setup a good description
        desc = None
        if pat_hand == PatHand.left:
            desc = translate("recorder", "LEFT HAND", "rec_desc")
        elif pat_hand == PatHand.right:
            desc = translate("recorder", "RIGHT HAND", "rec_desc")

        # use the current calibration to take a new recording
        self._drawing_window.reset(DrawingWindow.Mode.Record, desc)
        gc.collect()
        if not self._drawing_window.exec_():
            return

        # update stats
        self.drawing_number += 1
        self.calibration_age += 1
        self.params.total_recordings += 1
        preview = self._drawing_window.handler.buffer

        extra_data = {"blood_drawn": blood_drawn,
                      "drawing_number": self.drawing_number,
                      "total_recordings": self.params.total_recordings,
                      "installation_uuid": self.params.installation_uuid,
                      "installation_stamp": self.params.installation_stamp}
        record = Data.DrawingRecord(self.config, oid, aid,
                                    self._drawing_window.drawing,
                                    self._drawing_window.calibration,
                                    self.calibration_age,
                                    self._drawing_window.recording,
                                    cycle_state[0],
                                    pat_type, pat_hand_cnt, pat_handedness, pat_hand,
                                    extra_data)

        # guess a decent path name
        save_path = u"{}_{}_{}.rec.yaml.gz".format(
            record.recording.session_start.strftime("%Y%m%d"),
            record.aid, self.drawing_number)
        save_path = os.path.join(
            self.params.proj_path,
            record.recording.session_start.strftime("%Y%m"),
            save_path)

        # keep trying until save is either aborted or succeeds
        self._end_recording_dialog.reset(self.config, record, preview, save_path, cycle_state)
        while self._end_recording_dialog.exec_():
            record.oid = self._end_recording_dialog.oid
            record.aid = self._end_recording_dialog.aid
            record.pat_type = self._end_recording_dialog.pat_type
            record.pat_hand_cnt = self._end_recording_dialog.pat_hand_cnt
            record.pat_handedness = self._end_recording_dialog.pat_handedness
            record.pat_hand = self._end_recording_dialog.pat_hand
            record.extra_data["blood_drawn"] = self._end_recording_dialog.blood_drawn
            record.comments = self._end_recording_dialog.comments
            save_path = self._end_recording_dialog.save_path
            try:
                # attempt to create hierarchy
                path_dir = os.path.dirname(save_path)
                if not os.path.isdir(path_dir):
                    os.makedirs(path_dir)

                # put save into a background thread
                Shared.background_op(translate("recorder", "Saving, please wait..."),
                                     lambda: Data.DrawingRecord.save(record, save_path),
                                     self)
            except IOError as e:
                msg = translate("recorder",
                                "Cannot save recording to {path}: {reason}! "
                                "Try with a different file name!")
                msg = msg.format(path=save_path, reason=e.strerror)
                title = translate("recorder", "Save failure")
                QtGui.QMessageBox.critical(self, title, msg)
            else:
                return record

        # save aborted
        return None


    def on_new_recording(self):
        # fetch operator/AID immediately
        self._new_recording_dialog.reset()
        if not self._new_recording_dialog.exec_():
            return

        oid = self._new_recording_dialog.oid
        aid = self._new_recording_dialog.aid

        # setup recording cycle
        cycle = 1
        total = 2 * self.config.cycle_count
        cycle_state = (cycle, total)

        # initial state
        pat_type = None
        pat_hand_cnt = None
        pat_handedness = None
        pat_hand = None
        blood_drawn_state = {PatHand.left: None, PatHand.right: None}
        blood_drawn = None

        while True:
            record = self.new_recording(oid, aid,
                           pat_type, pat_hand_cnt, pat_handedness,
                           pat_hand, blood_drawn, cycle_state)
            if record is None or self._end_recording_dialog.next_hand != True:
                return

            # update
            oid = record.oid
            aid = record.aid
            pat_type = record.pat_type
            pat_hand_cnt = record.pat_hand_cnt
            pat_handedness = record.pat_handedness
            blood_drawn_state[record.pat_hand] = record.extra_data["blood_drawn"]

            # other hand
            if pat_hand_cnt == 1:
                pat_hand = record.pat_hand
            else:
                pat_hand = PatHand.left if record.pat_hand == PatHand.right else PatHand.right
            blood_drawn = blood_drawn_state[pat_hand]

            # recalculate cycle count
            cycle = record.cycle + 1
            total = pat_hand_cnt * self.config.cycle_count
            cycle_state = (cycle, total)

            # clear memory
            del record



# main application
class Application(QtGui.QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        UI.init_intl("recorder")

        # command-line flags
        ap = argparse.ArgumentParser(description='Drawing recorder')
        ap.add_argument('dir', nargs='?', help='project directory')
        args = ap.parse_args(map(unicode, args[1:]))

        # initialize the default settings
        self.settings = QtCore.QSettings(Consts.APP_ORG, Consts.APP_NAME)
        proj_path = args.dir if args.dir else \
          unicode(self.settings.value("proj_path", "recordings").toString())
        params = Params(proj_path, self.settings.value("total_recordings", 0).toInt()[0],
                        str(self.settings.value("installation_uuid", uuid.getnode()).toString()),
                        str(self.settings.value("installation_stamp", str(datetime.datetime.now())).toString()))

        # initialize
        self.main_window = MainWindow(params)
        self.main_window.show()
        self.lastWindowClosed.connect(self._on_close)


    def _on_close(self):
        params = self.main_window.params
        self.settings.setValue("proj_path", params.proj_path)
        self.settings.setValue("total_recordings", params.total_recordings)
        self.settings.setValue("installation_uuid", params.installation_uuid)
        self.settings.setValue("installation_stamp", params.installation_stamp)


    def event(self, ev):
        # re-send tablet proximity events up the chain
        if ev.type() == QtCore.QEvent.TabletEnterProximity or \
          ev.type() == QtCore.QEvent.TabletLeaveProximity:
            return self.sendEvent(self.activeWindow(), ev)

        # normal handling
        return super(Application, self).event(ev)



# main module
if __name__ == '__main__':
    app = Application(sys.argv)
    sys.exit(app.exec_())
