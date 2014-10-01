# -*- coding: utf-8 -*-
"""Drawing window"""

# local modules
import Analysis
import Consts
from UI import translate

# system modules
import math
import datetime
from PyQt4 import QtCore, QtGui


# implementation
class Mode(object):
    Calibrate, Record = range(2)


class Handler(object):
    def keyEvent(self, ev):
        pass

    def tabletEventTS(self, ev, stamp):
        pass

    def timerEvent(self, ev):
        pass

    def terminate(self):
        pass


class CalibrationHandler(Handler):
    def __init__(self, dw):
        self.dw = dw
        self.dw.reset_recording()
        self.dw.reset_calibration()
        self.dw._main_text.setText(translate("calib", "CALIBRATION"))
        self.dw._sub_text.setText(
            translate("calib",
                      "Place the pen on the red point and press ENTER\n"
                      "Press TAB to restart, ESC to abort calibration"))
        self.items = None
        self.restart()


    def restart(self):
        self.dw._cursor.hide()
        self.dw._warning.setText("")

        # storage for graphical items
        if self.items is not None:
            self.dw._scene.removeItem(self.items)
        self.items = QtGui.QGraphicsItemGroup(self.dw._supp_group)

        # initial state
        self.cpoints = []
        self.point = None
        self.prepare_next_point()


    def completed(self):
        res, error = self.dw.setup_calibration(
            Analysis.CalibrationData(self.dw.oid, self.dw.tablet_id, self.dw.stylus_id, self.cpoints))
        if not res:
            msg = translate("calib",
                            "CALIBRATION FAILED: {reason}!\n"
                            "Try refitting the paper. Restarting calibration...")
            msg = msg.format(reason=error.upper())
            self.restart()
            self.dw._warning.setText(msg)
        else:
            self.point = None
            self.dw._cursor.show()
            self.dw._set_bt_text(
                translate("calib",
                          "Previewing calibration. "
                          "To accept the results press ENTER"))


    def prepare_next_point(self):
        # update visual
        if self.point:
            self.dw._warning.setText("")
            self.point.setPen(QtGui.QPen(QtCore.Qt.green))
            self.point.setBrush(QtGui.QBrush(QtGui.QColor(0, 255, 0, 127)))

        # check if we reached the last point
        pos = len(self.cpoints)
        pos_max = len(self.dw.drawing.cpoints)
        if pos == pos_max:
            return self.completed()

        # prepare the next point
        next_point = self.dw.drawing.cpoints[pos]
        self.point = QtGui.QGraphicsEllipseItem(-Consts.POINT_LEN / 2,
                                                -Consts.POINT_LEN / 2,
                                                Consts.POINT_LEN,
                                                Consts.POINT_LEN)
        self.point.setPen(QtGui.QPen(QtCore.Qt.red))
        self.point.setPos(next_point[0], next_point[1])
        self.point.setParentItem(self.items)

        # update status
        msg = translate("calib", "Calibrating point {cur}/{tot}")
        self.dw._set_bt_text(msg.format(cur=pos+1, tot=pos_max))


    def add_point(self):
        if not self.dw._drawing_state:
            self.dw._warning.setText(translate("calib", "No cursor at point!"))
        else:
            self.cpoints.append((self.dw._drawing_pos.x(), self.dw._drawing_pos.y()))
            self.prepare_next_point()


    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key_Return or \
          ev.key() == QtCore.Qt.Key_Enter:
            # enter pressed
            if self.point:
                # currently calibrating
                self.add_point()
            else:
                # previewing
                self.dw.accept()
        elif ev.key() == QtCore.Qt.Key_Tab:
            self.restart()


    def keyEvent(self, ev):
        if ev.type() == QtCore.QEvent.KeyPress and not ev.isAutoRepeat():
            self.keyPressEvent(ev)


    def tabletEventTS(self, ev, stamp):
        if self.point:
            if ev.type() == QtCore.QEvent.TabletPress:
                self.point.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0, 127)))
            elif ev.type() == QtCore.QEvent.TabletRelease:
                self.point.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0, 0)))
        else:
            self.dw._cursor.setVisible(self.dw._tracking_state)


    def terminate(self):
        if self.items is not None:
            self.dw._scene.removeItem(self.items)



class RecordingHandler(Handler):
    def __init__(self, dw):
        self.dw = dw
        self.dw.reset_recording()
        self.dw._main_text.setText(translate("rec", "RECORDING"))
        self.dw._sub_text.setText(
            translate("rec",
                      "Recording starts automatically as soon as the pen touches the tablet\n"
                      "Press TAB to restart, ENTER to stop, ESC to abort recording"))
        self.dw._warning.setText("")

        # drawing support
        self.item = QtGui.QGraphicsPixmapItem()
        self.item.setParentItem(self.dw._back_group)
        self.buffer = QtGui.QPixmap(self.dw.size())
        self.painter = QtGui.QPainter(self.buffer)
        self.painter.setRenderHints(self.dw._view.renderHints())
        self.pen = QtGui.QPen(Consts.RECORDING_COLOR)
        self.pen.setCapStyle(QtCore.Qt.RoundCap)

        # initial state
        self.dw.recording = Analysis.RecordingData()
        rect = self.dw._view.sceneRect()
        self.dw.recording.rect_size = (rect.width(), rect.height())
        self.dw.recording.rect_drawing = self.get_rect(rect, self.dw._drawing_group)
        self.dw.recording.rect_trans = self.get_rect(rect, self.dw._trans_group)
        self.old_trans_pos = None
        self.restart()


    def get_rect(self, rect, item):
        ret = []
        tmp = item.mapFromScene(rect)
        for i in range(0, 4):
            p = tmp.value(i)
            ret.append((p.x(), p.y()))
        return ret


    def restart(self):
        self.dw.recording.clear()
        self.buffer.fill(Consts.FILL_COLOR)
        self.update_buffer()
        self.dw._set_bt_text(translate("rec", "Waiting for events..."))


    def update_buffer(self):
        self.item.setPixmap(self.buffer)
        self._needs_update = False


    def sched_update_buffer(self):
        self._needs_update = True


    def timerEvent(self, ev):
        # update the viewport
        if self._needs_update:
            self.update_buffer()

        # update the indicator
        if self.dw.recording.events:
            stamp = datetime.datetime.now()
            elapsed = stamp - self.dw.recording.events[0].stamp
            length = (self.dw.recording.events[-1].stamp -
                      self.dw.recording.events[0].stamp)
            msg = translate("rec",
                            "recording: {recording}\n"
                            "strokes: {strokes}\n"
                            "events: {events}\n"
                            "length: {length}")
            msg = msg.format(recording=str(elapsed),
                             strokes=self.dw.recording.strokes,
                             events=len(self.dw.recording.events),
                             length=str(length))
            self.dw._set_bt_text(msg)


    def tabletEventTS(self, ev, stamp):
        # record the data
        coords_drawing = self.dw._drawing_pos
        coords_trans = self.dw._trans_pos
        self.dw.recording.append(
            Analysis.RecordingEvent(
                ev.type(),
                [coords_drawing.x(), coords_drawing.y()],
                [coords_trans.x(), coords_trans.y()],
                ev.pressure(), self.dw._drawing_tilt,
                self.dw._trans_tilt, stamp))

        if not self.dw._drawing_state:
            self.old_trans_pos = None
        else:
            # new stroke
            if self.old_trans_pos is not None:
                self.pen.setWidthF(1 + ev.pressure() * (Consts.PEN_MAXWIDTH - 1))
                self.painter.setPen(self.pen)
                self.painter.drawLine(self.old_trans_pos, self.dw._trans_pos)
                self.sched_update_buffer()

            # update the old positions
            self.old_trans_pos = self.dw._trans_pos

        # cursor state
        self.dw._cursor.setVisible(self.dw._tracking_state)


    def keyEvent(self, ev):
        if ev.type() == QtCore.QEvent.KeyPress and not ev.isAutoRepeat():
            if ev.key() == QtCore.Qt.Key_Return or \
              ev.key() == QtCore.Qt.Key_Enter:
                self.dw.accept()
            elif ev.key() == QtCore.Qt.Key_Tab:
                self.restart()


    def terminate(self):
        self.painter = None
        self.dw._scene.removeItem(self.item)



class DrawingWindow(QtGui.QMainWindow):
    def __init__(self):
        super(DrawingWindow, self).__init__()

        # scene setup
        self._scene = QtGui.QGraphicsScene(self)
        self._scene.setBackgroundBrush(QtGui.QBrush(Consts.FILL_COLOR))
        self._view = QtGui.QGraphicsView(self._scene)
        self._view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        self._view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view.setCacheMode(QtGui.QGraphicsView.CacheNone)
        self._view.setOptimizationFlag(QtGui.QGraphicsView.DontSavePainterState)
        self._view.setInteractive(False)
        self._view.setFrameStyle(0)
        self.setCursor(QtCore.Qt.BlankCursor)
        self.setCentralWidget(self._view)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # back/projected/support/transposed/screen space
        self._back_group = QtGui.QGraphicsItemGroup(scene=self._scene)
        self._drawing_group = QtGui.QGraphicsItemGroup(scene=self._scene)
        self._supp_group = QtGui.QGraphicsItemGroup(scene=self._scene)
        self._trans_group = QtGui.QGraphicsItemGroup(scene=self._scene)
        self._screen_group = QtGui.QGraphicsItemGroup(scene=self._scene)

        # bars
        tmp = QtGui.QPainterPath()
        tmp.moveTo(0., -Consts.BAR_LEN)
        tmp.lineTo(0., 0.)
        tmp.lineTo(Consts.BAR_LEN, 0.)
        tmp = QtGui.QGraphicsPathItem(tmp, self._supp_group)
        tmp.setPen(QtGui.QPen(QtCore.Qt.green))

        tmp = QtGui.QPainterPath()
        tmp.moveTo(-Consts.BAR_LEN, Consts.BAR_LEN)
        tmp.lineTo(Consts.BAR_LEN, -Consts.BAR_LEN)
        tmp = QtGui.QGraphicsPathItem(tmp, self._supp_group)
        tmp.setPen(QtGui.QPen(QtCore.Qt.yellow))

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
        self._cursor = QtGui.QGraphicsPathItem(tmp, self._screen_group)

        # main text
        self._main_text = QtGui.QGraphicsSimpleTextItem(self._screen_group)
        self._main_text.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        font = self._main_text.font()
        font.setPointSize(Consts.MAIN_TEXT_SIZE)
        font.setBold(True)
        self._main_text.setFont(font)

        # sub text
        self._sub_text = QtGui.QGraphicsSimpleTextItem(self._screen_group)
        self._sub_text.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        font = self._sub_text.font()
        font.setPointSize(Consts.NORM_TEXT_SIZE)
        self._sub_text.setFont(font)

        # bt text
        self._bt_text = QtGui.QGraphicsSimpleTextItem(self._screen_group)
        self._bt_text.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        font = self._bt_text.font()
        font.setPointSize(Consts.NORM_TEXT_SIZE)
        self._bt_text.setFont(font)

        # warning
        self._warning = QtGui.QGraphicsSimpleTextItem(self._screen_group)
        self._warning.setBrush(QtGui.QBrush(QtCore.Qt.yellow))
        font = self._warning.font()
        font.setPointSize(Consts.WARN_TEXT_SIZE)
        self._warning.setFont(font)

        # initial state
        self.mode = None
        self._drawing_item = None
        self.reset_calibration()
        self.reset_recording()


    def reset_calibration(self):
        self.calibration = None


    def reset_recording(self):
        self.recording = None


    def setup_calibration(self, calibration):
        # peform the actual calibration
        res, error = self.drawing.calibrate(calibration.cpoints)
        if res is None:
            return False, error

        # setup the transposed space
        self.calibration = calibration
        self._trans_group.resetTransform()
        trans = QtGui.QTransform()
        pos = self._drawing_group.pos()
        trans.translate(pos.x(), pos.y())
        scale = self._drawing_group.scale()
        trans.scale(scale, scale)
        self._trans_group.setTransform(res * trans)
        return True, None


    def timerEvent(self, ev):
        self.handler.timerEvent(ev)


    def closeEvent(self, ev):
        self.reject()


    def event(self, ev):
        # handle proximity events like normal tablet events
        if ev.type() == QtCore.QEvent.TabletEnterProximity or \
          ev.type() == QtCore.QEvent.TabletLeaveProximity:
            self.tabletEventTS(ev, datetime.datetime.now())
            ev.accept()
            return True

        return super(DrawingWindow, self).event(ev)


    def _mapTiltToScene(self, tilt, pos):
        # extract absolute rotation at position (to support non-linear transforms)
        p0 = self._trans_group.mapToScene(QtCore.QPointF(pos.x(), pos.y()))
        p1 = self._trans_group.mapToScene(QtCore.QPointF(pos.x() + 1, pos.y()))
        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()
        dl = math.hypot(dx, dy)
        c = dx / dl
        s = dy / dl
        x = tilt[0] * c - tilt[1] * s
        y = tilt[0] * s + tilt[1] * c
        return (x, y)


    def tabletEventTS(self, ev, stamp):
        # only consider pen events and only when visible
        if ev.pointerType() != QtGui.QTabletEvent.Pen or \
          self.isVisible() is False:
            return

        # screen/drawing position
        self._screen_pos = ev.hiResGlobalPos()
        self._drawing_pos = self._drawing_group.mapFromScene(self._screen_pos)
        self._trans_pos = self._trans_group.mapToScene(self._drawing_pos)

        # screen/drawing tilt
        self._drawing_tilt = (ev.xTilt(), ev.yTilt())
        self._trans_tilt = self._mapTiltToScene(self._drawing_tilt, self._drawing_pos)

        # also update the cursor position within the translated space
        self._cursor.setPos(self._trans_pos)

        # update drawing state
        if ev.type() == QtCore.QEvent.TabletPress:
            self._cursor.setPen(QtGui.QPen(Consts.CURSOR_ACTIVE))
            self._tracking_state = True
            self._drawing_state = True
        elif ev.type() == QtCore.QEvent.TabletRelease:
            self._cursor.setPen(QtGui.QPen(Consts.CURSOR_INACTIVE))
            self._tracking_state = True
            self._drawing_state = False
        elif ev.type() == QtCore.QEvent.TabletEnterProximity:
            self._tracking_state = True
            self._drawing_state = False
        elif ev.type() == QtCore.QEvent.TabletLeaveProximity:
            self._tracking_state = False
            self._drawing_state = False

        self.handler.tabletEventTS(ev, stamp)


    def tabletEvent(self, ev):
        self.tabletEventTS(ev, datetime.datetime.now())


    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key_Escape:
            return self.closeEvent(QtGui.QCloseEvent())
        self.handler.keyEvent(ev)


    def keyReleaseEvent(self, ev):
        self.handler.keyEvent(ev)


    def reset(self, mode):
        self.mode = mode
        if mode == Mode.Calibrate:
            self.handler = CalibrationHandler(self)
        elif mode == Mode.Record:
            self.handler = RecordingHandler(self)


    def resizeEvent(self, ev):
        # resize to match current screen resolution
        size = ev.size()
        self._view.setSceneRect(0, 0, size.width(), size.height())
        self._drawing_group.setPos(size.width() / 2., size.height() / 2.)
        self._drawing_group.setScale(min(size.width(), size.height()) / 2. * 0.9)
        self._supp_group.setPos(self._drawing_group.pos())
        self._supp_group.setScale(self._drawing_group.scale())
        self._layout_all_text()


    def _layout_all_text(self):
        # main text
        tmp = self._view.sceneRect().topLeft()
        self._main_text.setPos(tmp)
        tmp.setY(tmp.y() + self._main_text.boundingRect().height())
        self._sub_text.setPos(tmp)
        tmp.setY(tmp.y() + self._sub_text.boundingRect().height())
        self._warning.setPos(tmp)

        # bottom text
        self._layout_bt_text()


    def _layout_bt_text(self):
        tmp = self._view.sceneRect().bottomLeft()
        tmp.setY(tmp.y() - self._bt_text.boundingRect().height())
        self._bt_text.setPos(tmp)


    def _set_bt_text(self, text):
        self._bt_text.setText(text)
        self._layout_bt_text()


    def exec_(self):
        self.result = None
        self._screen_pos = None
        self._drawing_pos = None
        self._drawing_state = False
        self._tracking_state = False
        self._cursor.hide()
        self._cursor.setPen(QtGui.QPen(Consts.CURSOR_INACTIVE))

        self.showFullScreen()
        tid = self.startTimer(Consts.REFRESH_DELAY)
        while self.isVisible():
            QtGui.QApplication.processEvents()
        self.killTimer(tid)
        return self.result


    def set_params(self, oid, tablet_id, stylus_id, drawing):
        # reset calibration/drawing if restarting
        if self._drawing_item is not None:
            self.reset_calibration()
            self.reset_recording()
            self._scene.removeItem(self._drawing_item)

        # calibration device
        self.oid = oid
        self.tablet_id = tablet_id
        self.stylus_id = stylus_id

        # create the graphical item
        self.drawing = drawing
        self._drawing_item = self.drawing.generate()
        self._drawing_item.setPen(QtGui.QPen(Consts.DRAWING_COLOR))
        self._drawing_item.setPos(0., 0.)
        self._drawing_item.setParentItem(self._drawing_group)


    def accept(self):
        self.hide()
        self.result = True
        self.handler.terminate()


    def reject(self):
        self.hide()
        self.result = False
        self.handler.terminate()
