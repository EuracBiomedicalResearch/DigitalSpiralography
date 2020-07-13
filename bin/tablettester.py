#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tablet tester"""

# setup path
import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src/lib')))

# local modules
from DrawingRecorder import Consts
from DrawingRecorder import Tablet
import HiResTime
import QExtTabletWindow

# system modules
import argparse
import datetime
import os
from PyQt5 import QtCore, QtWidgets, QtGui


class MainWindow(QExtTabletWindow.QExtTabletWindow):
    def __init__(self, device):
        super(MainWindow, self).__init__(device)

        # scene setup
        self._scene = QtWidgets.QGraphicsScene()
        self._scene.setBackgroundBrush(QtGui.QBrush(Consts.FILL_COLOR))
        self._view = QtWidgets.QGraphicsView()
        self._view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        self._view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view.setCacheMode(QtWidgets.QGraphicsView.CacheNone)
        self._view.setOptimizationFlag(QtWidgets.QGraphicsView.DontSavePainterState)
        self._view.setInteractive(False)
        self._view.setFrameStyle(0)
        self._view.setScene(self._scene)
        self.setCursor(QtCore.Qt.BlankCursor)
        self.setCentralWidget(self._view)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self._screen_group = QtWidgets.QGraphicsItemGroup()
        self._scene.addItem(self._screen_group)

        # cursor
        tmp = QtGui.QPainterPath()
        tmp.moveTo(0, -Consts.CURSOR_LEN)
        tmp.lineTo(0, Consts.CURSOR_LEN)
        tmp.moveTo(-Consts.CURSOR_LEN, 0)
        tmp.lineTo(Consts.CURSOR_LEN, 0)
        tmp.moveTo(-Consts.CURSOR_LEN / 4, -Consts.CURSOR_LEN / 4)
        tmp.lineTo(Consts.CURSOR_LEN / 4, Consts.CURSOR_LEN / 4)
        tmp.moveTo(Consts.CURSOR_LEN / 4, -Consts.CURSOR_LEN / 4)
        tmp.lineTo(-Consts.CURSOR_LEN / 4, Consts.CURSOR_LEN / 4)
        self._cursor = QtWidgets.QGraphicsPathItem(tmp, self._screen_group)

        # main text
        self._main_text = QtWidgets.QGraphicsSimpleTextItem(self._screen_group)
        self._main_text.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        self._main_text.setText("TABLET TESTER")
        font = self._main_text.font()
        font.setPointSize(Consts.MAIN_TEXT_SIZE)
        font.setBold(True)
        self._main_text.setFont(font)

        # sub text
        self._sub_text = QtWidgets.QGraphicsTextItem(self._screen_group)
        self._sub_text.setDefaultTextColor(QtCore.Qt.gray)
        font = self._sub_text.font()
        font.setFamily("Consolas")
        font.setPointSize(Consts.NORM_TEXT_SIZE)
        self._sub_text.setFont(font)

        # initial state
        self.reset()
        self._drawing_state = False
        self._tracking_state = False
        self._cursor.hide()
        self._cursor.setPen(QtGui.QPen(Consts.CURSOR_INACTIVE, 0))
        self.showFullScreen()
        self.startTimer(Consts.REFRESH_DELAY)


    def rate_init(self, now):
        self.rate_buckets = [0] * 61
        self.rate_last = now
        self.rate_first = now
        self.rate_status = 'waiting'


    def rate_update(self, now):
        l_sec = int((self.rate_last - self.rate_first).total_seconds())
        n_sec = int((now - self.rate_first).total_seconds())
        bucket = n_sec % len(self.rate_buckets)

        if n_sec != l_sec:
            # clear new bucket
            self.rate_buckets[bucket] = 0

            if l_sec >= (len(self.rate_buckets) - 1):
                # full
                acc = 0
                for b in range(len(self.rate_buckets)):
                    if b != bucket:
                        acc += self.rate_buckets[b]
                self.ev_rate = float(acc) / (len(self.rate_buckets) - 1)
                self.rate_status = '{}s avg'.format((len(self.rate_buckets) - 1))
            elif l_sec > 1:
                # partial
                acc = sum([self.rate_buckets[s % (len(self.rate_buckets) - 1)] for s in range(1, l_sec)])
                self.ev_rate = float(acc) / (l_sec - 1)
                self.rate_status = '{}s avg'.format(l_sec)

        self.rate_buckets[bucket] += 1
        self.rate_last = now


    def resizeEvent(self, ev):
        # resize to match current screen resolution
        size = ev.size()
        self._view.setSceneRect(0, 0, size.width(), size.height())

        # layout text
        tmp = self._view.sceneRect().topLeft()
        self._main_text.setPos(tmp)
        tmp.setY(tmp.y() + self._main_text.boundingRect().height())
        self._sub_text.setPos(tmp)


    def extTabletEvent(self, ev):
        # only consider pen events and only when visible
        if self.isVisible() is False:
            return

        # update drawing state
        if ev.subtype == QtCore.QEvent.TabletPress:
            self._cursor.setPen(QtGui.QPen(Consts.CURSOR_ACTIVE, 0))
            self._tracking_state = True
            self._drawing_state = True
        elif ev.subtype == QtCore.QEvent.TabletRelease:
            self._cursor.setPen(QtGui.QPen(Consts.CURSOR_INACTIVE, 0))
            self._tracking_state = True
            self._drawing_state = False
        elif ev.subtype == QtCore.QEvent.TabletEnterProximity:
            self._tracking_state = True
            self._drawing_state = False
        elif ev.subtype == QtCore.QEvent.TabletLeaveProximity:
            self._tracking_state = False
            self._drawing_state = False

        # also update the cursor position
        self._cursor.setPos(ev.position)
        self._cursor.setVisible(self._tracking_state)

        # refresh data
        if self.first_ev is None:
            self.first_ev = ev
            self.rate_init(ev.os_stamp)
        if self.dev_off is None and ev.dev_stamp is not None:
            self.dev_off = (ev.dev_stamp, HiResTime.now())
            self.ev_drops = 0
        if self.last_ev is not None and self.last_ev.dev_serial is not None and ev.dev_serial is not None:
            # take into account wrap-arounds
            if self.last_ev.dev_serial < ev.dev_serial:
                self.ev_drops += (ev.dev_serial - self.last_ev.dev_serial) - 1
        self.last_ev = ev
        self.rate_update(ev.os_stamp)
        self.update()


    def timerEvent(self, ev):
        self.update()


    def update(self):
        if self.first_ev is None:
            return

        # basic state
        msg  =   "Tracking: " + ("<b>TRUE</b>" if self._tracking_state else "false")
        msg += "\nDrawing:  " + ("<b>TRUE</b>" if self._drawing_state else "false")

        # data
        msg += "\nPressure: {:8.3f}".format(self.last_ev.pressure)
        msg += "\nPosition: {:8.3f} {:8.3f}".format(self.last_ev.position.x(), self.last_ev.position.y())
        msg += "\nTilt:     {:8.3f} {:8.3f}".format(*self.last_ev.tilt)
        msg += "\n"

        # timing
        os_time = datetime.datetime.now()
        hr_time = HiResTime.now()
        os_hr_delta = (os_time - hr_time).total_seconds() * 1000.
        self.os_hr_max = max(self.os_hr_max, abs(os_hr_delta))

        dev_time = None
        hr_dv_delta = float("nan")
        hr_dv_dsc = ''
        if self.dev_off is not None and self.last_ev.dev_stamp is not None:
            off = self.last_ev.dev_stamp - self.dev_off[0]
            dev_time = self.dev_off[1] + datetime.timedelta(seconds=(off / 1000.))
            hr_dv_delta = (hr_time - dev_time).total_seconds() * 1000.
            if abs(hr_dv_delta) >= 25.:
                hr_dv_pc = hr_dv_delta * 100. / off
                hr_dv_dsc = " [{:.3f}% DV]".format(hr_dv_pc)

        msg += "\nOS Time: " + str(os_time)
        msg += "\nHR Time: " + str(hr_time)
        msg += "\nEV Time: " + str(self.last_ev.os_stamp)
        msg += "\nDV Time: " + str(dev_time)
        msg += "\n"

        # clock deltas
        msg += "\nOS-HR delta ms: {:8.3f} [{:.3} max]".format(os_hr_delta, self.os_hr_max)
        msg += "\nHR-DV delta ms: {:8.3f}{}".format(hr_dv_delta, hr_dv_dsc)
        msg += "\nEV Rate HZ:     {:8.3f} [{}]".format(self.ev_rate, self.rate_status)
        msg += "\n"

        # device stamp/serial/rate
        msg += "\nDV Stamp:   " + str(self.last_ev.dev_stamp)
        msg += "\nDV Serial:  " + str(self.last_ev.dev_serial)
        msg += "\nDV Drop:    " + str(self.ev_drops)

        # update text
        msg = msg.replace(" ", "&nbsp;")
        msg = msg.replace("\n", "<br/>")
        self._sub_text.setHtml(msg)


    def reset(self):
        self._sub_text.setHtml("Waiting for first event ...")
        HiResTime.resync()
        self.first_ev = None
        self.last_ev = None
        self.dev_off = None
        self.ev_drops = None
        self.os_hr_max = 0.
        self.ev_rate = float("nan")


    def keyEvent(self, ev):
        if ev.key() == QtCore.Qt.Key_Escape:
            self.close()
        elif ev.key() == QtCore.Qt.Key_Tab:
            self.reset()


    def event(self, ev):
        if ev.type() == QExtTabletWindow.EVENT_TYPE:
            self.extTabletEvent(ev)
            ev.accept()
            return True
        elif ev.type() == QtCore.QEvent.KeyPress and not ev.isAutoRepeat():
            self.keyEvent(ev)
            ev.accept()
            return True
        return super(MainWindow, self).event(ev)


# main application
class Application(QtWidgets.QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)

        # command-line flags
        ap = argparse.ArgumentParser(description='Tablet tester')
        ap.add_argument('dir', nargs='?', help='project directory')
        args = ap.parse_args(args[1:])

        # initialize
        device = Tablet.get_tablet_device()
        self.main_window = MainWindow(device)
        self.main_window.show()


# main module
if __name__ == '__main__':
    app = Application(sys.argv)
    sys.exit(app.exec_())
