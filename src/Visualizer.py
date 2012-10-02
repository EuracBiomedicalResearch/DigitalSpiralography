# -*- coding: utf-8 -*-
"""Main Drawing visualizer application"""

# local modules
import Shared
import Analysis
import Consts

# system modules
import math
import platform
import threading
from PyQt4 import QtCore, QtGui, uic


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

        self._ui.actionRAWCorr.setChecked(self._showRaw)
        self._ui.actionSpeedTime.setChecked(self._showTime)
        self._ui.actionShowTraces.setChecked(self._showTraces)

        # signals and events
        self._ui.actionOpen.triggered.connect(self.on_load)
        self._ui.actionInfo.triggered.connect(self.on_info)
        self._ui.actionShowTraces.triggered.connect(self.on_trace)
        self._ui.actionRAWCorr.triggered.connect(self.on_raw)
        self._ui.actionSpeedTime.triggered.connect(self.on_time)
        self._ui.view.wheelEvent = self.on_wheel

        # props
        self._props = QtGui.QStandardItemModel()
        self._ui.props.setModel(self._props)

        # scene
        self._scene = QtGui.QGraphicsScene()
        self._scene.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.black))
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
        self._props.setHorizontalHeaderLabels(["Property", "Value"])


    def _reset_scene(self):
        self._scene.clear()


    def _append_prop(self, name, value):
        self._props.appendRow([QtGui.QStandardItem(unicode(name)),
                               QtGui.QStandardItem(unicode(value))])


    def _load_props(self, record):
        self._append_prop("Pat. ID", record.aid)
        self._append_prop("Pat. type", record.pat_type or "N/A")
        self._append_prop("Pat. handedness", record.pat_handedness or "N/A")
        self._append_prop("Pat. hand", record.pat_hand or "N/A")

        self._append_prop("Drawing ID", record.drawing.id)
        self._append_prop("Drawing descr.", record.drawing.str)

        self._append_prop("Recording date", record.recording.session_start)
        self._append_prop("Recording no.", record.extra_data['drawing_number'])
        self._append_prop("Recording retries", record.recording.retries)
        self._append_prop("Recording strokes", record.recording.strokes)
        self._append_prop("Recording events", len(record.recording.events))
        self._append_prop("Recording start", record.recording.events[0].stamp)
        self._append_prop("Recording length", record.recording.events[-1].stamp -
                          record.recording.events[0].stamp)

        self._append_prop("Calib. tablet ID", record.calibration.tablet_id)
        self._append_prop("Calib. date", record.calibration.stamp)
        self._append_prop("Calib. age", record.calibration_age)

        self._append_prop("Screen width", int(record.recording.rect_size[0]))
        self._append_prop("Screen height", int(record.recording.rect_size[1]))

        self._append_prop("Software version", record.extra_data['version'])
        self._append_prop("Format version", record.extra_data['format'])

        self._append_prop("Inst. UUID", record.extra_data['installation_uuid'])
        self._append_prop("Inst. date", record.extra_data['installation_stamp'])
        self._append_prop("Inst. recordings", record.extra_data['total_recordings'])

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
        tmp = QtGui.QPainterPath()
        pen = QtGui.QPen(Consts.RECORDING_COLOR)
        pen.setCapStyle(QtCore.Qt.RoundCap)

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
            elif event.typ == QtCore.QEvent.TabletLeaveProximity:
                drawing = False
                old_pos = None

            if old_pos:
                if drawing:
                    # calculate speed/color
                    if self._showTime:
                        sf1 = (stamp - record.recording.events[0].stamp).total_seconds() / total_secs
                        sf0 = 1. - sf1
                    else:
                        ds = math.hypot(old_pos[0] - pos[0], old_pos[1] - pos[1])
                        dt = max(speed_repr, (stamp - old_stamp).total_seconds())
                        sf1 = min(1., (ds / dt) * speed_repr)
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

                if drawing or self._showTraces:
                    # create the item
                    tmp = QtGui.QGraphicsLineItem(old_pos[0], old_pos[1], pos[0], pos[1])
                    tmp.setPen(pen)
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
            record = Shared.background_op("Loading, please wait...",
                                          lambda: Analysis.DrawingRecord.load(path))
        except Exception as e:
            msg = "Cannot load recording {}: {}".format(path, e)
            QtGui.QMessageBox.critical(self, "Load failure", msg)
            return

        # only update the view on success
        self.load_record(record)


    def on_load(self, ev):
        path = QtGui.QFileDialog.getOpenFileName(self, "Load recording",
                                                 QtCore.QString(),
                                                 "Recordings (*.yaml.gz)");
        if path:
            self.load(str(path))


    def on_info(self, ev):
        QtGui.QMessageBox.about(self, "About DrawingVisualizer",
                                "{} {} {}".format(Consts.APP_ORG,
                                                  Consts.APP_NAME,
                                                  Consts.APP_VERSION))

    def _redraw_scene(self):
        if self.record:
            self._reset_scene()
            self._load_scene(self.record)


    def on_trace(self, ev):
        self._showTraces = self._ui.actionShowTraces.isChecked()
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

        self.main_window = MainWindow()
        self.main_window.show()

        # if a file was specified on the cmd-line, load it
        if platform.system() != 'Windows':
            args = self.arguments()
            if len(args) > 1:
                self.main_window.load(str(args[1]))
