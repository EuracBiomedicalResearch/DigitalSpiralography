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

        self._ui.actionRAWCorr.setChecked(self._showRaw)
        self._ui.actionSpeedTime.setChecked(self._showTime)
        self._ui.actionShowTraces.setChecked(self._showTraces)
        self._ui.actionShowTilt.setChecked(self._showTilt)

        # signals and events
        self._ui.actionOpen.triggered.connect(self.on_load)
        self._ui.actionInfo.triggered.connect(self.on_info)
        self._ui.actionShowTraces.triggered.connect(self.on_trace)
        self._ui.actionRAWCorr.triggered.connect(self.on_raw)
        self._ui.actionSpeedTime.triggered.connect(self.on_time)
        self._ui.actionShowTilt.triggered.connect(self.on_tilt)
        self._ui.view.wheelEvent = self.on_wheel

        # props
        self._props = QtGui.QStandardItemModel()
        self._ui.props.setModel(self._props)

        # scene
        self._scene = QtGui.QGraphicsScene()
        self._scene.setBackgroundBrush(QtGui.QBrush(Consts.FILL_COLOR))
        self._ui.view.setScene(self._scene)

        self.record = None
        self.reset()


    def reset(self):
        self._reset_props()
        self._reset_scene()
        self._ui.comments.clear()


    def _reset_props(self):
        self._props.clear()
        self._props.setColumnCount(2)
        self._props.setHorizontalHeaderLabels(
            [translate("visualizer", "Property"),
             translate("visualizer", "Value")])


    def _reset_scene(self):
        self._scene.clear()


    def _append_prop(self, name, value):
        name = unicode(name)
        if value is not None:
            value = unicode(value)
        else:
            value = translate("types", "N/A")

        self._props.appendRow([QtGui.QStandardItem(name),
                               QtGui.QStandardItem(value)])


    def _append_prop_map(self, name, type_map, value):
        if value in type_map:
            self._append_prop(name, translate("types", type_map[value]))
        else:
            self._append_prop(name, value)


    def _load_props(self, record):
        name = translate("visualizer", "Pat. ID")
        self._append_prop(name, record.aid)
        name = translate("visualizer", "Pat. type")
        self._append_prop_map(name, Analysis.PAT_TYPE_DSC, record.pat_type)
        name = translate("visualizer", "Pat. handedness")
        self._append_prop_map(name, Analysis.PAT_HANDEDNESS_DSC, record.pat_handedness)
        name = translate("visualizer", "Pat. hand")
        self._append_prop_map(name, Analysis.PAT_HAND_DSC, record.pat_hand)

        name = translate("visualizer", "Operator")
        self._append_prop(name, record.extra_data.get('operator'))
        name = translate("visualizer", "Blood drawn")
        self._append_prop_map(name, Analysis.BOOL_MAP_DSC,
                              record.extra_data.get('blood_drawn'))

        name = translate("visualizer", "Drawing ID")
        self._append_prop(name, record.drawing.id)
        name = translate("visualizer", "Drawing descr.")
        self._append_prop(name, record.drawing.str)

        name = translate("visualizer", "Rec. date")
        self._append_prop(name, record.recording.session_start)
        name = translate("visualizer", "Rec. no.")
        self._append_prop(name, record.extra_data['drawing_number'])
        name = translate("visualizer", "Rec. retries")
        self._append_prop(name, record.recording.retries)
        name = translate("visualizer", "Rec. strokes")
        self._append_prop(name, record.recording.strokes)
        name = translate("visualizer", "Rec. events")
        self._append_prop(name, len(record.recording.events))
        name = translate("visualizer", "Rec. start")
        self._append_prop(name, record.recording.events[0].stamp)
        name = translate("visualizer", "Rec. length")
        self._append_prop(name, record.recording.events[-1].stamp -
                          record.recording.events[0].stamp)

        name = translate("visualizer", "Calib. tablet ID")
        self._append_prop(name, record.calibration.tablet_id)
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

        # trace
        pen = QtGui.QPen(Consts.RECORDING_COLOR)
        pen.setCapStyle(QtCore.Qt.RoundCap)

        tilt_pen = QtGui.QPen(Consts.TILT_COLOR)
        tilt_pen.setWidthF(0.1)

        low_color = QtGui.QColor(Consts.RECORDING_COLOR)
        high_color = QtGui.QColor(Consts.FAST_COLOR)

        speed_repr = 1. / Consts.FAST_SPEED
        total_secs = (record.recording.events[-1].stamp -
                      record.recording.events[0].stamp).total_seconds()

        old_pos = None
        old_stamp = None
        drawing = False
        for event in record.recording.events:
            stamp = event.stamp
            if not self._showRaw:
                pos = event.coords_trans
            else:
                # reproject drawing coordinates into screen space
                pos = event.coords_drawing
                pos = self._screen_group.mapFromItem(self._drawing_group, QtCore.QPointF(pos[0], pos[1]))
                pos = (pos.x(), pos.y())

            # set drawing status
            if event.typ == QtCore.QEvent.TabletPress:
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
                        sf1 = (stamp - record.recording.events[0].stamp).total_seconds() / total_secs
                        sf0 = 1. - sf1
                    else:
                        speed = speedAtPoint(record.recording.events, stamp, 0.05)
                        sf1 = min(1., max(0., speed * speed_repr))
                        sf0 = 1. - sf1

                    # blend the color
                    color = QtGui.QColor(low_color.red() * sf0 + high_color.red() * sf1,
                                         low_color.green() * sf0 + high_color.green() * sf1,
                                         low_color.blue() * sf0 + high_color.blue() * sf1)

                    # pen parameters
                    pen.setColor(color)
                    pen.setWidthF(1 + event.pressure * (Consts.PEN_MAXWIDTH - 1))
                else:
                    pen.setColor(Consts.CURSOR_INACTIVE)
                    pen.setWidthF(0.5)

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
            old_pos = pos
            old_stamp = stamp


    def _fit_view(self):
        rect_size = self.record.recording.rect_size
        self._ui.view.fitInView(0, 0, rect_size[0], rect_size[1],
                                mode=QtCore.Qt.KeepAspectRatio)


    def load_record(self, record):
        self.reset()
        self.record = record
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


    def on_tilt(self, ev):
        self._showTilt = self._ui.actionShowTilt.isChecked()
        self._redraw_scene()


    def on_raw(self, ev):
        self._showRaw = self._ui.actionRAWCorr.isChecked()
        self._redraw_scene()


    def on_time(self, ev):
        self._showTime = self._ui.actionSpeedTime.isChecked()
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
