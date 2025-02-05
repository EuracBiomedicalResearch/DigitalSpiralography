#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main Stylus profiler application"""

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Consts
from DrawingRecorder import Data
from DrawingRecorder import ID
from DrawingRecorder import Tablet
from DrawingRecorder import UI
from DrawingRecorder.UI import translate
import QExtTabletWindow

# system modules
import argparse
import datetime
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets


# helpers
class blocked_signals(object):
    def __init__(self, widget):
        self.widget = widget

    def __enter__(self):
        self.orig = self.widget.signalsBlocked()
        self.widget.blockSignals(True)

    def __exit__(self, exc_type, exc_value, traceback):
        self.widget.blockSignals(self.orig)


class sorting_disabled(object):
    def __init__(self, widget):
        self.widget = widget

    def __enter__(self):
        self.orig = self.widget.isSortingEnabled()
        self.widget.setSortingEnabled(False)

    def __exit__(self, ex_type, exc_value, traceback):
        self.widget.setSortingEnabled(self.orig)


# main application
class MainWindow(QExtTabletWindow.QExtTabletWindow):
    def __init__(self, device):
        super(MainWindow, self).__init__(device)
        self._ui = UI.load_ui(self, "profiler.ui")

        # signals and events
        self._ui.actionNew.triggered.connect(self.on_new)
        self._ui.actionOpen.triggered.connect(self.on_load)
        self._ui.actionSave.triggered.connect(self.on_save)
        self._ui.actionFullScreen.toggled.connect(self.on_fullscreen)
        self._ui.actionInfo.triggered.connect(self.on_info)
        self._ui.add_weight_btn.clicked.connect(self.on_add)

        self._ui.operator_id.textEdited.connect(
            lambda: self.on_meta_changed("oid", self._ui.operator_id))
        self._ui.stylus_id.textEdited.connect(
            lambda: self.on_meta_changed("sid", self._ui.stylus_id))
        self._ui.tablet_id.textEdited.connect(
            lambda: self.on_meta_changed("tid", self._ui.tablet_id))

        self._ui.tare_btn.clicked.connect(self.on_tare)
        self._ui.weight.textEdited.connect(self.on_weight)
        self._ui.tare.textEdited.connect(self.on_weight)

        # data
        self._ui.data.setEditable(True)
        self._ui.data.installEventFilter(self)
        self._ui.data.itemChanged.connect(self.on_data_changed)
        self._ui.data.itemSelectionChanged.connect(self.on_selected)
        self._ui.data.setColumnCount(2)
        self._ui.data.setHorizontalHeaderLabels(
            [translate("profiler", "Pressure"),
            translate("profiler", "Weight (g)")])

        # plot
        self.pg = self._ui.view
        self.pg.setLabel("bottom", "Weight", units="g")
        self.pg.setLabel("left", "Pressure")
        self.pg.showGrid(True, True)
        self.pg.hideButtons()

        self.rsp_fit = pg.PlotCurveItem(pen=(255, 0, 0))
        self.pg.addItem(self.rsp_fit)

        self.rsp_txt = pg.TextItem()
        self.rsp_txt.setFont(QtGui.QFont("monospace"))
        self.rsp_txt.setParentItem(self.pg.getViewBox())

        self.rsp = pg.ScatterPlotItem()
        self.pg.addItem(self.rsp)

        self.cb = [pg.InfiniteLine(None, 0), pg.InfiniteLine(None, 90)]
        self._hide_cb()
        self.pg.addItem(self.cb[0])
        self.pg.addItem(self.cb[1])

        self.pi = pg.InfiniteLine(None, 0, pen=(0, 255, 255))
        self.pi.hide()
        self.pg.addItem(self.pi)

        # current state
        self._tablet = False
        self.reset()


    def event(self, ev):
        # just eat all tablet events and update the internal state
        if ev.type() != QExtTabletWindow.EVENT_TYPE:
            return super(MainWindow, self).event(ev)
        ev.accept()
        if ev.subtype == QExtTabletWindow.EventSubtypes.LEAVE:
            if self._tablet:
                self._exit_proximity()
        else:
            if not self._tablet:
                self._enter_proximity()
            self.update_pi(ev.pressure)
        return True


    def update_cb(self, pos):
        for i in range(2):
            self.cb[i].setValue(pos[i])
            self.cb[i].show()


    def update_pi(self, pos):
        self.pi.show()
        self.pi.setValue(pos)
        self._ui.pressure.setText(str(pos))


    def _enter_proximity(self):
        self._tablet = True
        self._ui.pressure.setEnabled(False)
        self.pi.show()


    def _exit_proximity(self):
        self._tablet = False
        self.pi.hide()
        self._ui.pressure.setEnabled(True)


    def _hide_cb(self):
        self.cb[0].hide()
        self.cb[1].hide()


    def _update_meta(self):
        # update timestamps
        self.data.ts_updated = datetime.datetime.now()
        self._ui.ts_updated.setText(str(self.data.ts_updated))
        self.changed = True


    def _update_rsp(self):
        # keep the data sorted by pressure
        self.data.data = sorted(self.data.data, key=lambda x: x.pressure)

        # update the curve
        if len(self.data.data) < 2:
            self.rsp.hide()
        else:
            x = [el.weight for el in self.data.data]
            y = [el.pressure for el in self.data.data]
            self.rsp.setData(x, y)
            self.rsp.show()

        # 2nd degree fit
        if len(self.data.data) < 3:
            self.data.fit = None
        else:
            try:
                self.data.fit = np.polyfit(y, x, 3, full=True)
            except ValueError:
                pass

        if self.data.fit is None:
            self.fit = None
            self.rsp_fit.hide()
            self.rsp_txt.hide()
        else:
            fy = [el / 50. for el in range(51)]
            fx = [np.polyval(self.data.fit[0], el) for el in fy]

            self.rsp_fit.setData(fx, fy)
            self.rsp_fit.show()

            text = "Response fit: " + str(self.data.fit[0])
            if self.data.fit[1]:
                text += "\n    Residual: " + str(self.data.fit[1])

            self.rsp_txt.setText(text)
            self.rsp_txt.show()


    def _update_data(self):
        # reconstruct data from the table
        self.data.data = []
        self.data_ok = True

        for y in range(self._ui.data.rowCount()):
            v = [None, None]
            for x in range(2):
                item = self._ui.data.item(y, x)
                try:
                    v[x] = float(item.text())
                except ValueError:
                    self.data_ok = False
            if v[0] is not None and v[1] is not None:
                self.data.data.append(
                    Data.StylusResponseData(v[0], v[1]))

        self._update_rsp()
        self._update_meta()


    def on_meta_changed(self, var, item):
        v = item.text()
        if getattr(self.data, var) != v:
            setattr(self.data, var, v)
            self._update_meta()


    def on_data_changed(self, item):
        try:
            float(item.text())
            item.setBackground(self._ui.data.viewOptions().palette.base())
            self.on_selected()
        except ValueError:
            item.setBackgroundColor(QtCore.Qt.yellow)
        self._update_data()


    def on_selected(self):
        idx = self._ui.data.selectedIndexes()
        if not idx or not idx[0].isValid():
            self._hide_cb()
        else:
            row = idx[0].row()
            v = [None, None]
            try:
                v[0] = float(self._ui.data.item(row, 0).text())
                v[1] = float(self._ui.data.item(row, 1).text())
            except ValueError:
                pass
            if v[0] is not None and v[1] is not None:
                self.update_cb(v)


    def _add(self, pressure, weight):
        with sorting_disabled(self._ui.data) \
          and blocked_signals(self._ui.data):
            self._ui.data.addRow([str(pressure), str(weight)])
            self._update_data()


    def on_add(self, ev):
        press = self._ui.pressure.text()
        try:
            press = float(press)
        except ValueError:
            self._ui.pressure.selectAll()
            self._ui.pressure.setFocus()
            return

        weight = self._ui.weight.text()
        try:
            weight = float(weight)
        except ValueError:
            self._ui.weight.selectAll()
            self._ui.weight.setFocus()
            return

        if not self._tare:
            total = weight
        else:
            tare = self._ui.tare.text()
            try:
                tare = float(tare)
            except ValueError:
                self._ui.tare.selectAll()
                self._ui.tare.setFocus()
                return
            total = weight + tare

        self._add(press, total)
        self._ui.weight.clear()
        self.on_weight(None)
        if self._tablet:
            self._ui.weight.setFocus()
        else:
            self._ui.pressure.clear()
            self._ui.pressure.setFocus()


    def eventFilter(self, watched, ev):
        # delegate to handle 'del' for row deletion in TableWidget
        if watched == self._ui.data and \
          ev.type() == QtCore.QEvent.KeyPress and \
          ev.key() == QtCore.Qt.Key_Delete:
            self.on_delete()
            return True
        return False


    def on_delete(self):
        idx = self._ui.data.selectedIndexes()
        if idx and idx[0].isValid():
            self._ui.data.removeRow(idx[0].row())
            self._update_data()


    def load_profile(self, profile):
        self.data = profile
        self._ui.ts_created.setText(str(self.data.ts_created))
        self._ui.ts_updated.setText(str(self.data.ts_updated))
        self._ui.operator_id.setText(self.data.oid or "")
        self._ui.stylus_id.setText(self.data.sid or "")
        self._ui.tablet_id.setText(self.data.tid or "")

        with sorting_disabled(self._ui.data) \
          and blocked_signals(self._ui.data):
            self._ui.data.setRowCount(0)
            for p in self.data.data:
                self._ui.data.addRow([str(p.pressure), str(p.weight)])
        self._ui.data.sortItems(0)

        self._hide_cb()
        self._update_rsp()
        self.pg.setXRange(0, 350)
        self.pg.setYRange(0, 1)
        self.data_ok = True
        self.changed = False

        self._ui.pressure.clear()
        self._ui.weight.clear()
        self._ui.tare.clear()
        self._ui.tare_btn.setChecked(False)
        self.on_tare(False)

        self._ui.operator_id.setFocus()


    def reset(self):
        self.load_profile(Data.StylusProfile())


    def _check_changed(self):
        if not self.changed:
            return True

        title = translate("profiler", "Discard profile")
        msg = translate("profiler", "The current profile has been edited.\n"
                        "Are you sure you want to discard the profile?")
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Warning, title, msg)
        box.addButton(translate("profiler", "No"), QtWidgets.QMessageBox.NoRole)
        box.addButton(translate("profiler", "Yes, discard"), QtWidgets.QMessageBox.YesRole)
        return box.exec_()


    def on_new(self, ev):
        if self._check_changed():
            self.reset()


    def load(self, path):
        try:
            profile = Data.StylusProfile.load(path)
        except Exception as e:
            msg = translate("profiler",
                            "Cannot load profile {path}: {reason}")
            msg = msg.format(path=path, reason=e)
            title = translate("profiler", "Load failure")
            QtWidgets.QMessageBox.critical(self, title, msg)
            return

        # only update the view on success
        self.load_profile(profile)


    def on_load(self, ev):
        if not self._check_changed():
            return

        title = translate("profiler", "Load profile")
        ext_name = translate("profiler", "Profiles")
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, title, "", ext_name + " (*.prof.json.gz *.prof.yaml.gz)")
        if path:
            self.load(path)


    def on_save(self, ev):
        # check data
        if len(self.data.data) < 2:
            title = translate("profiler", "Invalid data")
            msg = translate("profiler", "The current curve is too short")
            QtWidgets.QMessageBox.critical(None, title, msg)
            return

        if not self.data_ok:
            title = translate("profiler", "Invalid data")
            msg = translate("profiler", "The current curve data contains invalid values")
            QtWidgets.QMessageBox.critical(None, title, msg)
            return

        # validate the operator
        if not self.data.oid:
            title = translate("profiler", "Invalid operator")
            msg = translate("profiler", "The specified operator is invalid")
            QtWidgets.QMessageBox.critical(None, title, msg)
            self._ui.operator_id.selectAll()
            self._ui.operator_id.setFocus()
            return

        # check IDs
        if not ID.validate_sid_err(self.data.sid):
            self._ui.stylus_id.selectAll()
            self._ui.stylus_id.setFocus()
            return
        if not ID.validate_tid_err(self.data.tid):
            self._ui.tablet_id.selectAll()
            self._ui.tablet_id.setFocus()
            return

        # file prompt
        title = translate("profiler", "Save profile")
        ext_name = translate("profiler", "Profiles")
        path = u"{}_{}_{}.prof.json.gz".format(self.data.sid, self.data.tid,
                                               self.data.ts_updated.strftime("%Y%m%d"))
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, title, path, ext_name + " (*.prof.json.gz)")
        if not path:
            return

        try:
            Data.StylusProfile.save(self.data, path)
        except IOError as e:
            msg = translate("profiler",
                            "Cannot save profile to {path}: {reason}!")
            msg = msg.format(path=path, reason=e.strerror)
            title = translate("profiler", "Save failure")
            QtWidgets.QMessageBox.critical(self, title, msg)
        self.changed = False


    def on_tare(self, state):
        self._tare = state
        self._ui.tare_lbl.setEnabled(state)
        self._ui.total_lbl.setEnabled(state)
        self._ui.tare.setEnabled(state)
        if state:
            self._ui.tare.setFocus()
        else:
            self._ui.weight.setFocus()
        self.on_weight(None)


    def on_weight(self, ev):
        weight = self._ui.weight.text()
        try:
            weight = float(weight)
        except ValueError:
            self._ui.total.clear()
            return

        if not self._tare:
            total = weight
        else:
            tare = self._ui.tare.text()
            try:
                tare = float(tare)
            except ValueError:
                self._ui.total.clear()
                return
            total = weight + tare

        self._ui.total.setText(str(total))


    def on_fullscreen(self, state):
        if state:
            self.showFullScreen()
        else:
            self.showNormal()


    def on_info(self, ev):
        ver = "{} {} {}".format(Consts.APP_ORG, Consts.APP_NAME, Consts.APP_VERSION)
        title = translate("profiler", "About StylusProfiler")
        QtWidgets.QMessageBox.about(self, title, ver)



# main application
class Application(QtWidgets.QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        UI.init_intl("profiler")

        # command-line flags
        ap = argparse.ArgumentParser(description='Stylus profiler')
        ap.add_argument('file', nargs='?', help='stylus profile to load')
        args = ap.parse_args(args[1:])

        # initialize
        device = Tablet.get_tablet_device()
        self.main_window = MainWindow(device)
        self.main_window.show()
        if args.file:
            self.main_window.load(args.file)


# entry point
if __name__ == '__main__':
    app = Application(sys.argv)
    sys.exit(app.exec_())
