# -*- coding: utf-8 -*-
"""Main Drawing visualizer application"""

# local modules
import Shared
import Analysis
import Consts
import Intl
from Intl import translate

# system modules
import math
import platform
import threading
from PyQt4 import QtCore, QtGui, uic


# support functions
def speedAtPoint(events, stamp, window):
    w_events = []
    for w_event in events:
        if abs((w_event.stamp - stamp).total_seconds()) < window:
            w_events.append(w_event)
    w_secs = (w_events[-1].stamp - w_events[0].stamp).total_seconds()
    if not w_secs:
        return -1

    w_len = 0
    for i in range(1, len(w_events) - 1):
        old_pos = w_events[i - 1].coords_drawing
        pos = w_events[i].coords_drawing
        w_len += math.hypot(old_pos[0] - pos[0], old_pos[1] - pos[1])

    return w_len / w_secs


def sampleSpeed(events, window):
    for event in events:
        event.speed = speedAtPoint(events, event.stamp, 0.05)

def ctrb(x, a, b, ctrl, bias):
    i = (x - a) / (b - a) + bias - 1.
    r = math.pow(max(min(i, 1.), 0.), 1. / (1. - (ctrl - 1.)))
    return a + (b - a) * max(min(r, b), a)


class CtrbWidget(QtGui.QWidget):
    def __init__(self, ctrl_f, bias_f, descr):
        super(QtGui.QWidget, self).__init__()
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        self.setMaximumWidth(300)
        self.ctrl_s = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.ctrl_s.setRange(0, 100)
        self.ctrl_s.setValue(50)
        self.ctrl_s.valueChanged.connect(ctrl_f)
        self.ctrl_s.setToolTip(translate("visualizer", "{} Contrast".format(descr)))
        layout.addWidget(self.ctrl_s, 0, 0)
        self.bias_s = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.bias_s.setRange(0, 100)
        self.bias_s.setValue(50)
        self.bias_s.valueChanged.connect(bias_f)
        self.bias_s.setToolTip(translate("visualizer", "{} Bias".format(descr)))
        layout.addWidget(self.bias_s, 1, 0)
        self.reset_btn = QtGui.QPushButton(self.style().standardIcon(QtGui.QStyle.SP_DialogCancelButton), "")
        self.reset_btn.setToolTip(translate("visualizer", "Reset {}".format(descr)))
        self.reset_btn.clicked.connect(self.reset)
        layout.addWidget(self.reset_btn, 0, 1, 2, 1)

    def reset(self):
        with blocked_signals(self):
            self.ctrl_s.setValue(50)
            self.bias_s.setValue(50)


class blocked_signals(object):
    def __init__(self, widget):
        self.widget = widget

    def __enter__(self):
        self.orig = self.widget.signalsBlocked()
        self.widget.blockSignals(True)

    def __exit__(self, exc_type, exc_value, traceback):
        self.widget.blockSignals(self.orig)



# main application
class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        form, _ = uic.loadUiType("ui/visualizer.ui")
        self._ui = form()
        self._ui.setupUi(self)

        # defaults
        self._showRaw = False
        self._showTime = False
        self._showTraces = True
        self._showTilt = True
        self._showStrokes = True
        self._wc = [1., 1.]
        self._cc = [1., 1.]

        self._ui.actionRAWCorr.setChecked(self._showRaw)
        self._ui.actionSpeedTime.setChecked(self._showTime)
        self._ui.actionShowTraces.setChecked(self._showTraces)
        self._ui.actionShowTilt.setChecked(self._showTilt)
        self._ui.actionShowStrokes.setChecked(self._showStrokes)

        # props
        self._ui.props.setColumnCount(2)
        self._ui.props.setHorizontalHeaderLabels(
            [translate("visualizer", "Property"),
             translate("visualizer", "Value")])

        # signals and events
        self._ui.actionOpen.triggered.connect(self.on_load)
        self._ui.actionInfo.triggered.connect(self.on_info)
        self._ui.actionShowTraces.triggered.connect(self.on_trace)
        self._ui.actionRAWCorr.triggered.connect(self.on_raw)
        self._ui.actionSpeedTime.triggered.connect(self.on_time)
        self._ui.actionShowTilt.triggered.connect(self.on_tilt)
        self._ui.actionShowStrokes.triggered.connect(self.on_strokes)
        self._ui.view.wheelEvent = self.on_wheel

        # trial selector
        ts = self._ui.trialSelector = QtGui.QComboBox()
        ts.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        ts.currentIndexChanged.connect(self.on_trial)
        self._ui.mainToolBar.insertWidget(self._ui.actionRAWCorr, ts)

        # width/color ctrb
        self._ui.widthCtrb = CtrbWidget(self.on_wc_c, self.on_wc_b, translate("visualizer", "Width"))
        self._ui.ctrbToolBar.insertWidget(self._ui.actionInfo, self._ui.widthCtrb)
        self._ui.colorCtrb = CtrbWidget(self.on_cc_c, self.on_cc_b, translate("visualizer", "Color"))
        self._ui.ctrbToolBar.insertWidget(self._ui.actionInfo, self._ui.colorCtrb)

        # scene
        self._scene = QtGui.QGraphicsScene()
        self._scene.setBackgroundBrush(QtGui.QBrush(Consts.FILL_COLOR))
        self._ui.view.setScene(self._scene)

        self.record = None
        self.reset()


    def reset(self):
        self._reset_trials()
        self._reset_scene()
        self._ui.props.setRowCount(0)
        self._ui.comments.clear()


    def _reset_trials(self):
        self._curTrial = 0
        with blocked_signals(self._ui.trialSelector):
            self._ui.trialSelector.clear()
            self._ui.trialSelector.setDisabled(True)


    def _reset_scene(self):
        self._scene.clear()


    def _append_prop(self, name, value):
        name = unicode(name)
        if value is not None:
            value = unicode(value)
        else:
            value = translate("types", "N/A")

        pos = self._ui.props.rowCount()
        self._ui.props.insertRow(pos)
        self._ui.props.setItem(pos, 0, QtGui.QTableWidgetItem(name))
        self._ui.props.setItem(pos, 1, QtGui.QTableWidgetItem(value))


    def _append_prop_map(self, name, type_map, value):
        if value in type_map:
            self._append_prop(name, translate("types", type_map[value]))
        else:
            self._append_prop(name, value)


    def _load_trials(self, record):
        ts = self._ui.trialSelector
        with blocked_signals(ts):
            ts.addItem(translate("visualizer", "Main recording"), 0)
            if record.recording.retries:
                for i in range(len(record.recording.retries)):
                    if record.recording.retries[i]:
                        msg = translate("visualizer", "Attempt {attempt}")
                    else:
                        msg = translate("visualizer", "Attempt {attempt} (no data)")
                    ts.addItem(msg.format(attempt=i + 1), i + 1)
                ts.setDisabled(False)


    def _load_props(self, record):
        name = translate("visualizer", "Pat. ID")
        self._append_prop(name, record.aid)
        name = translate("visualizer", "Pat. type")
        self._append_prop_map(name, Consts.PAT_TYPES, record.pat_type)
        name = translate("visualizer", "Pat. hand count")
        self._append_prop(name, record.pat_hand_cnt)
        name = translate("visualizer", "Pat. handedness")
        self._append_prop_map(name, Analysis.PAT_HANDEDNESS_DSC, record.pat_handedness)
        name = translate("visualizer", "Pat. hand")
        self._append_prop_map(name, Analysis.PAT_HAND_DSC, record.pat_hand)

        name = translate("visualizer", "Operator")
        self._append_prop(name, record.oid)
        name = translate("visualizer", "Blood drawn")
        self._append_prop_map(name, Analysis.BOOL_MAP_DSC,
                              record.extra_data.get('blood_drawn'))

        name = translate("visualizer", "Drawing ID")
        self._append_prop(name, record.drawing.id)
        name = translate("visualizer", "Drawing descr.")
        self._append_prop(name, record.drawing.str)

        name = translate("visualizer", "File created")
        self._append_prop(name, record.ts_created)
        name = translate("visualizer", "File updated")
        self._append_prop(name, record.ts_updated)

        name = translate("visualizer", "Rec. date")
        self._append_prop(name, record.recording.session_start)
        name = translate("visualizer", "Rec. no.")
        self._append_prop(name, record.extra_data['drawing_number'])
        name = translate("visualizer", "Rec. cycle")
        self._append_prop(name, record.cycle)
        name = translate("visualizer", "Rec. retries")
        self._append_prop(name, len(record.recording.retries) + 1)
        name = translate("visualizer", "Rec. strokes")
        self._append_prop(name, record.recording.strokes)
        name = translate("visualizer", "Rec. events")
        self._append_prop(name, len(record.recording.events))
        name = translate("visualizer", "Rec. start")
        self._append_prop(name, record.recording.events[0].stamp)
        name = translate("visualizer", "Rec. length")
        self._append_prop(name, record.recording.events[-1].stamp -
                          record.recording.events[0].stamp)

        name = translate("visualizer", "Calib. operator")
        self._append_prop(name, record.calibration.oid)
        name = translate("visualizer", "Calib. tablet ID")
        self._append_prop(name, record.calibration.tablet_id)
        name = translate("visualizer", "Calib. stylus ID")
        self._append_prop(name, record.calibration.stylus_id)
        name = translate("visualizer", "Calib. date")
        self._append_prop(name, record.calibration.stamp)
        name = translate("visualizer", "Calib. age")
        self._append_prop(name, record.calibration_age)

        name = translate("visualizer", "Screen width")
        self._append_prop(name, int(record.recording.rect_size[0]))
        name = translate("visualizer", "Screen height")
        self._append_prop(name, int(record.recording.rect_size[1]))

        name = translate("visualizer", "Software version")
        self._append_prop(name, record.extra_data['version'])
        name = translate("visualizer", "Format version")
        self._append_prop(name, record.extra_data['format'])

        name = translate("visualizer", "Inst. UUID")
        self._append_prop(name, record.extra_data['installation_uuid'])
        name = translate("visualizer", "Inst. date")
        self._append_prop(name, record.extra_data['installation_stamp'])
        name = translate("visualizer", "Inst. recordings")
        self._append_prop(name, record.extra_data['total_recordings'])

        self._ui.comments.setPlainText(record.comments)


    def _load_scene(self, record):
        # projected/support/screen space
        self._drawing_group = QtGui.QGraphicsItemGroup(scene=self._scene)
        self._supp_group = QtGui.QGraphicsItemGroup(scene=self._scene)
        self._screen_group = QtGui.QGraphicsItemGroup(scene=self._scene)

        # setup transforms
        rect_size = record.recording.rect_size
        scene_poly = Shared.size2qpoly(rect_size[0], rect_size[1])
        drawing_poly = Shared.poly2qpoly(record.recording.rect_drawing)

        transform = QtGui.QTransform()
        QtGui.QTransform.quadToQuad(drawing_poly, scene_poly, transform)

        self._drawing_group.setTransform(transform)
        self._supp_group.setTransform(transform)

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

        if not self._showRaw:
            # drawing
            tmp = QtGui.QPainterPath()
            tmp.moveTo(*record.drawing.points[0])
            for x, y in record.drawing.points[1:]:
                tmp.lineTo(x, y)
            tmp = QtGui.QGraphicsPathItem(tmp)
            tmp.setPen(QtGui.QPen(Consts.DRAWING_COLOR))
            tmp.setPos(0., 0.)
            tmp.setParentItem(self._drawing_group)

        if self._showRaw:
            # calibration points
            pen = QtGui.QPen(QtGui.QColor(255, 0, 0, 127))
            brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 64))
            for point in record.calibration.cpoints:
                tmp = QtGui.QGraphicsEllipseItem(-Consts.POINT_LEN / 2,
                                                 -Consts.POINT_LEN / 2,
                                                 Consts.POINT_LEN,
                                                 Consts.POINT_LEN)
                tmp.setPen(pen)
                tmp.setBrush(brush)
                tmp.setPos(point[0], point[1])
                tmp.setParentItem(self._drawing_group)

        # select the event trace
        events = record.recording.events if self._curTrial == 0 \
            else record.recording.retries[self._curTrial - 1]

        # trace
        pen = QtGui.QPen(Consts.RECORDING_COLOR)
        pen.setCapStyle(QtCore.Qt.RoundCap)

        tilt_pen = QtGui.QPen(Consts.TILT_COLOR)
        tilt_pen.setWidthF(0.1)

        lift_pen = QtGui.QPen(Consts.LIFT_COLOR)
        lift_pen.setWidthF(Consts.LIFT_PEN_WIDTH)
        lift_pen.setColor(QtGui.QColor(Consts.LIFT_COLOR))

        low_color = QtGui.QColor(Consts.RECORDING_COLOR)
        high_color = QtGui.QColor(Consts.FAST_COLOR)

        # sample the speed only once
        if not self._showTime and 'speed' not in dir(events[0]):
            record = Shared.background_op(
                translate("visualizer", "Sampling speed..."),
                lambda: sampleSpeed(events, 0.05))

        speed_repr = 1. / Consts.FAST_SPEED
        total_secs = (events[-1].stamp - events[0].stamp).total_seconds()

        old_pos = None
        old_stamp = None
        drawing = False
        old_drawing = False
        for event in events:
            stamp = event.stamp
            if not self._showRaw:
                pos = event.coords_trans
            else:
                # reproject drawing coordinates into screen space
                pos = event.coords_drawing
                pos = self._screen_group.mapFromItem(self._drawing_group, QtCore.QPointF(pos[0], pos[1]))
                pos = (pos.x(), pos.y())

            # set drawing status
            if event.typ == QtCore.QEvent.TabletPress or event.pressure:
                drawing = True
            elif event.typ == QtCore.QEvent.TabletRelease:
                drawing = False
            elif event.typ == QtCore.QEvent.TabletEnterProximity or \
              event.typ == QtCore.QEvent.TabletLeaveProximity:
                drawing = False
                pos = None

            if old_pos:
                if drawing:
                    # calculate speed/color
                    if self._showTime:
                        sf1 = (stamp - events[0].stamp).total_seconds() / total_secs
                    else:
                        sf1 = min(1., max(0., event.speed * speed_repr))

                    # blend the color
                    sf1 = ctrb(sf1, 0, 1, self._cc[0], self._cc[1])
                    sf0 = 1. - sf1
                    color = QtGui.QColor(low_color.red() * sf0 + high_color.red() * sf1,
                                         low_color.green() * sf0 + high_color.green() * sf1,
                                         low_color.blue() * sf0 + high_color.blue() * sf1)

                    # pen parameters
                    p = 1 + ctrb(event.pressure, 0, 1, self._wc[0], self._wc[1]) * (Consts.PEN_MAXWIDTH - 1)
                    pen.setColor(color)
                    pen.setWidthF(p)
                else:
                    # set trace color only
                    pen.setColor(Consts.CURSOR_INACTIVE)
                    pen.setWidthF(0.5)

                    # highlight stroke/lifts
                    if self._showStrokes and old_drawing and event is not events[-1]:
                        tmp = QtGui.QGraphicsEllipseItem(old_pos[0] - Consts.LIFT_RADIUS / 2,
                                                         old_pos[1] - Consts.LIFT_RADIUS / 2,
                                                         Consts.LIFT_RADIUS, Consts.LIFT_RADIUS)
                        tmp.setPen(lift_pen)
                        tmp.setParentItem(self._screen_group)

                if pos and (drawing or self._showTraces):
                    # the line itself
                    tmp = QtGui.QGraphicsLineItem(old_pos[0], old_pos[1], pos[0], pos[1])
                    tmp.setPen(pen)
                    tmp.setParentItem(self._screen_group)

                    # tilt vector
                    if self._showTilt and event.tilt_drawing is not None:
                        if not self._showRaw:
                            tilt = event.tilt_trans
                        else:
                            tilt = event.tilt_drawing

                        # the vector itself
                        tmp = QtGui.QGraphicsLineItem(pos[0], pos[1],
                                                      pos[0] + tilt[0] * Consts.TILT_MAXLEN,
                                                      pos[1] + tilt[1] * Consts.TILT_MAXLEN)
                        tmp.setPen(tilt_pen)
                        tmp.setParentItem(self._screen_group)

            # save old status
            old_drawing = drawing
            old_pos = pos
            old_stamp = stamp


    def _fit_view(self):
        rect_size = self.record.recording.rect_size
        self._ui.view.fitInView(0, 0, rect_size[0], rect_size[1],
                                mode=QtCore.Qt.KeepAspectRatio)


    def load_record(self, record):
        self.reset()
        self.record = record
        self._load_trials(self.record)
        self._load_props(self.record)
        self._load_scene(self.record)
        self._fit_view()


    def on_wheel(self, ev):
        delta = ev.delta() / 100.
        if delta < 0:
            delta = 1. / -delta
        self._ui.view.scale(delta, delta)


    def load(self, path):
        try:
            # perform the loading in background thread
            record = Shared.background_op(
                translate("visualizer", "Loading, please wait..."),
                lambda: Analysis.DrawingRecord.load(path))
        except Exception as e:
            msg = translate("visualizer",
                            "Cannot load recording {path}: {reason}")
            msg = msg.format(path=path, reason=e)
            title = translate("visualizer", "Load failure")
            QtGui.QMessageBox.critical(self, title, msg)
            return

        # only update the view on success
        self.load_record(record)


    def on_load(self, ev):
        title = translate("visualizer", "Load recording")
        ext_name = translate("visualizer", "Recordings")
        path = QtGui.QFileDialog.getOpenFileName(
            self, title, QtCore.QString(), ext_name + " (*.yaml.gz)")
        if path:
            self.load(unicode(path))


    def on_info(self, ev):
        ver = "{} {} {}".format(Consts.APP_ORG, Consts.APP_NAME, Consts.APP_VERSION)
        title = translate("visualizer", "About DrawingVisualizer")
        QtGui.QMessageBox.about(self, title, ver)


    def _redraw_scene(self):
        if self.record:
            self._reset_scene()
            self._load_scene(self.record)


    def on_trace(self, ev):
        self._showTraces = self._ui.actionShowTraces.isChecked()
        self._redraw_scene()


    def on_trial(self, ev):
        self._curTrial = self._ui.trialSelector.itemData(
            self._ui.trialSelector.currentIndex()).toPyObject()
        self._redraw_scene()


    def on_tilt(self, ev):
        self._showTilt = self._ui.actionShowTilt.isChecked()
        self._redraw_scene()


    def on_strokes(self, ev):
        self._showStrokes = self._ui.actionShowStrokes.isChecked()
        self._redraw_scene()


    def on_raw(self, ev):
        self._showRaw = self._ui.actionRAWCorr.isChecked()
        self._redraw_scene()


    def on_time(self, ev):
        self._showTime = self._ui.actionSpeedTime.isChecked()
        self._redraw_scene()


    def on_wc_c(self, v):
        v = 0.01 + float(v) / 51.
        self._wc[0] = v
        self._redraw_scene()


    def on_wc_b(self, v):
        v = 0.01 + float(v) / 51.
        self._wc[1] = v
        self._redraw_scene()


    def on_cc_c(self, v):
        v = 0.01 + float(v) / 51.
        self._cc[0] = v
        self._redraw_scene()


    def on_cc_b(self, v):
        v = 0.01 + float(v) / 51.
        self._cc[1] = v
        self._redraw_scene()



# main application
class Application(QtGui.QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        Intl.initialize("visualizer")

        # initialize
        self.main_window = MainWindow()
        self.main_window.show()

        # if a file was specified on the cmd-line, load it
        if platform.system() != 'Windows':
            args = self.arguments()
            if len(args) > 1:
                self.main_window.load(unicode(args[1]))
