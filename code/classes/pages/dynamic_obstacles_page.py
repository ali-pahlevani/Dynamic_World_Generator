from PyQt5.QtWidgets import (
    QWizardPage, QHBoxLayout, QVBoxLayout, QComboBox, QListWidget,
    QPushButton, QLineEdit, QMessageBox, QGraphicsLineItem,
    QGraphicsEllipseItem, QWidget, QGroupBox, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt, QEvent, QPointF, QLineF, QRectF
from PyQt5.QtGui import QPen, QColor
from classes.zoomable_graphics_view import ZoomableGraphicsView
from classes.apply_worker import ApplyWorker
import math


def _btn(text, role=None):
    b = QPushButton(text)
    if role:
        b.setProperty("btnRole", role)
    return b


class DynamicObstaclesPage(QWizardPage):
    def __init__(self, scene):
        super().__init__()
        self.setTitle("Add Dynamic Obstacles")
        self.world_manager = None
        self.scene = scene
        self.current_obstacle = None
        self.current_motion_type = "linear"
        self.points = []
        self.clicking_enabled = False

        # ── Left panel ─────────────────────────────────────────────
        self.left_widget = QWidget()
        self.left_widget.setFixedWidth(260)
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(10)

        # Obstacle selection group
        sel_group = QGroupBox("Select Obstacle")
        sg_layout = QVBoxLayout(sel_group)
        sg_layout.setSpacing(6)
        self.obstacle_list = QListWidget()
        self.obstacle_list.setFixedHeight(110)
        self.obstacle_list.itemClicked.connect(self.select_obstacle)
        sg_layout.addWidget(self.obstacle_list)
        left_layout.addWidget(sel_group)

        # Motion type group
        mtype_group = QGroupBox("Motion Type")
        mg_layout = QVBoxLayout(mtype_group)
        mg_layout.setSpacing(6)
        self.motion_type_combo = QComboBox()
        self.motion_type_combo.addItems(["Linear", "Elliptical", "Polygon"])
        self.motion_type_combo.currentTextChanged.connect(self.update_motion_type)
        mg_layout.addWidget(self.motion_type_combo)
        left_layout.addWidget(mtype_group)

        # Parameters group
        params_group = QGroupBox("Motion Parameters")
        pg_layout = QVBoxLayout(params_group)
        pg_layout.setSpacing(6)
        pg_layout.addWidget(QLabel("Velocity (m/s)"))
        self.velocity_input = QLineEdit()
        self.velocity_input.setPlaceholderText("1.0")
        pg_layout.addWidget(self.velocity_input)
        pg_layout.addWidget(QLabel("Velocity std dev"))
        self.std_input = QLineEdit()
        self.std_input.setPlaceholderText("0.1")
        pg_layout.addWidget(self.std_input)
        self._lbl_sm = QLabel("Semi-major axis")
        pg_layout.addWidget(self._lbl_sm)
        self.semi_major_input = QLineEdit()
        self.semi_major_input.setPlaceholderText("1.0")
        pg_layout.addWidget(self.semi_major_input)
        self._lbl_sn = QLabel("Semi-minor axis")
        pg_layout.addWidget(self._lbl_sn)
        self.semi_minor_input = QLineEdit()
        self.semi_minor_input.setPlaceholderText("0.5")
        pg_layout.addWidget(self.semi_minor_input)
        left_layout.addWidget(params_group)

        # Path definition group
        path_group = QGroupBox("Path Definition")
        ph_layout = QVBoxLayout(path_group)
        ph_layout.setSpacing(6)
        self.status_label = QLabel("Select an obstacle to begin")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #7F8C8D; font-size: 9pt;")
        ph_layout.addWidget(self.status_label)
        btn_row = QHBoxLayout()
        self.start_button = _btn("Start Path")
        self.start_button.clicked.connect(self.start_path)
        self.finish_button = _btn("Finish Path")
        self.finish_button.clicked.connect(self.finish_path)
        btn_row.addWidget(self.start_button)
        btn_row.addWidget(self.finish_button)
        ph_layout.addLayout(btn_row)
        left_layout.addWidget(path_group)

        left_layout.addStretch(1)

        self.apply_button = _btn("Apply and Preview", "success")
        self.apply_button.clicked.connect(self.apply_changes)
        left_layout.addWidget(self.apply_button)

        # ── Canvas ─────────────────────────────────────────────────
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("white"))
        self.view.installEventFilter(self)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ── Main layout ────────────────────────────────────────────
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.left_widget)
        layout.addWidget(self.view, 1)

        # Initialize field visibility
        self._set_ellipse_fields_visible(False)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _set_ellipse_fields_visible(self, visible):
        for w in (self._lbl_sm, self.semi_major_input, self._lbl_sn, self.semi_minor_input):
            w.setVisible(visible)

    def _set_status(self, text):
        self.status_label.setText(text)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error",
                                "Select a simulation and create/load a world first.")
            return
        self.obstacle_list.clear()
        for m in self.world_manager.models:
            if m["type"] in ("box", "cylinder", "sphere"):
                self.obstacle_list.addItem(m["name"])
        self.wizard().refresh_canvas(self.scene)

    # ── Motion type handling ───────────────────────────────────────────────

    def update_motion_type(self, text):
        self.current_motion_type = text.lower()
        self._set_ellipse_fields_visible(self.current_motion_type == "elliptical")
        self.clear_path()
        self.points = []

    def select_obstacle(self, item):
        self.current_obstacle = item.text()
        model = next((m for m in self.world_manager.models
                      if m["name"] == self.current_obstacle), None)
        if model and "motion" in model["properties"]:
            motion = model["properties"]["motion"]
            self.motion_type_combo.blockSignals(True)
            self.motion_type_combo.setCurrentText(motion["type"].capitalize())
            self.motion_type_combo.blockSignals(False)
            self.current_motion_type = motion["type"]
            self._set_ellipse_fields_visible(self.current_motion_type == "elliptical")
            self.velocity_input.setText(str(motion["velocity"]))
            self.std_input.setText(str(motion["std"]))
            if motion["type"] == "elliptical":
                self.semi_major_input.setText(str(motion["semi_major"]))
                self.semi_minor_input.setText(str(motion["semi_minor"]))
                center_m = model["properties"]["position"][:2]
                center = QPointF(center_m[0]*100, -center_m[1]*100)
                ang = motion["angle"]
                self.points = [center + QPointF(
                    motion["semi_major"]*100*math.cos(ang),
                    -motion["semi_major"]*100*math.sin(ang),
                )]
            else:
                self.points = [QPointF(x*100, -y*100) for x, y in motion["path"]]
            self.draw_path(close_polygon=(motion["type"] == "polygon"))
            self._set_status(f"Editing: {self.current_obstacle}")
        else:
            self.clear_path()
            self.points = []
            for inp in (self.velocity_input, self.std_input,
                        self.semi_major_input, self.semi_minor_input):
                inp.clear()
            self._set_status(f"Click 'Start Path' to define motion for {self.current_obstacle}")

    # ── Path definition ────────────────────────────────────────────────────

    def start_path(self):
        if not self.current_obstacle or not self.current_motion_type:
            self._set_status("Select an obstacle first")
            return
        self.clicking_enabled = True
        self.points = []
        self.clear_path()
        tip = {"linear": "Click 2 points for the path",
               "elliptical": "Click 1 point for orientation",
               "polygon": "Click points; press Finish when done"}
        self._set_status(tip.get(self.current_motion_type, "Click to define path"))

    def finish_path(self):
        self.clicking_enabled = False
        self.draw_path(close_polygon=(self.current_motion_type == "polygon"))
        self.store_motion()
        self._set_status("Path saved. Click Apply to push to simulation.")

    def eventFilter(self, obj, event):
        if (obj == self.view and
                event.type() == QEvent.MouseButtonPress and
                event.button() == Qt.LeftButton and
                self.clicking_enabled):
            point = self.snap_to_grid(self.view.mapToScene(event.pos()))
            self.points.append(point)
            if self.current_motion_type == "linear" and len(self.points) == 2:
                self.clicking_enabled = False
                self.draw_path()
                self.store_motion()
                self._set_status("Linear path saved.")
            elif self.current_motion_type == "elliptical" and len(self.points) == 1:
                self.clicking_enabled = False
                self.draw_path()
                self.store_motion()
                self._set_status("Ellipse saved.")
            elif self.current_motion_type == "polygon":
                self.draw_path()
                self._set_status(f"{len(self.points)} points — press Finish when done")
            return True
        return super().eventFilter(obj, event)

    def snap_to_grid(self, point, grid_spacing=10):
        return QPointF(
            round(point.x() / grid_spacing) * grid_spacing,
            round(point.y() / grid_spacing) * grid_spacing,
        )

    def clear_path(self):
        if (self.current_obstacle and
                self.current_obstacle in self.wizard().path_items):
            for pi in self.wizard().path_items.pop(self.current_obstacle):
                self.scene.removeItem(pi)

    def draw_path(self, close_polygon=False):
        self.clear_path()
        items = []
        color_map = {"linear": "#E74C3C", "elliptical": "#27AE60", "polygon": "#4A90E2"}
        color = color_map[self.current_motion_type]
        pen = QPen(QColor(color), 2)

        if self.current_motion_type == "linear" and len(self.points) == 2:
            ln = QGraphicsLineItem(QLineF(self.points[0], self.points[1]))
            ln.setPen(pen)
            self.scene.addItem(ln)
            items.append(ln)

        elif self.current_motion_type == "elliptical" and len(self.points) == 1:
            try:
                sm = float(self.semi_major_input.text() or 1.0)
                sn = float(self.semi_minor_input.text() or 0.5)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input",
                                    "Enter valid semi-major and semi-minor values.")
                return
            model = next(m for m in self.world_manager.models
                         if m["name"] == self.current_obstacle)
            cx, cy = model["properties"]["position"][:2]
            center = QPointF(cx*100, -cy*100)
            direction = self.points[0] - center
            angle = math.degrees(math.atan2(-direction.y(), direction.x()))
            ell = QGraphicsEllipseItem(QRectF(-sm*100, -sn*100, 2*sm*100, 2*sn*100))
            ell.setPos(center)
            ell.setRotation(-angle)
            ell.setPen(pen)
            self.scene.addItem(ell)
            items.append(ell)

        elif self.current_motion_type == "polygon" and len(self.points) >= 2:
            for i in range(len(self.points) - 1):
                ln = QGraphicsLineItem(QLineF(self.points[i], self.points[i+1]))
                ln.setPen(pen)
                self.scene.addItem(ln)
                items.append(ln)
            if close_polygon and len(self.points) >= 3:
                ln = QGraphicsLineItem(QLineF(self.points[-1], self.points[0]))
                ln.setPen(pen)
                self.scene.addItem(ln)
                items.append(ln)

        self.wizard().path_items[self.current_obstacle] = items

    def store_motion(self):
        if not self.current_obstacle or not self.current_motion_type or not self.points:
            return
        try:
            velocity = float(self.velocity_input.text() or 1.0)
            std = float(self.std_input.text() or 0.1)
            if velocity <= 0:
                raise ValueError("Velocity must be positive.")
            if std < 0:
                raise ValueError("Std dev must be non-negative.")
            if self.current_motion_type == "linear" and len(self.points) == 2:
                s, e = self.points[0], self.points[1]
                length = math.hypot((e.x() - s.x()) / 100, (e.y() - s.y()) / 100)
                max_v = length / 0.001 * 0.5
                if velocity > max_v:
                    QMessageBox.warning(
                        self, "Velocity Too High",
                        f"Path length {length:.2f} m — max recommended: {max_v:.1f} m/s"
                    )
                    return
        except ValueError as ex:
            QMessageBox.warning(self, "Invalid Input", str(ex))
            return

        model = next(m for m in self.world_manager.models
                     if m["name"] == self.current_obstacle)
        motion = {"type": self.current_motion_type, "velocity": velocity, "std": std}

        if self.current_motion_type in ("linear", "polygon"):
            motion["path"] = [(p.x()/100, -p.y()/100) for p in self.points]
        elif self.current_motion_type == "elliptical":
            sm = float(self.semi_major_input.text() or 1.0)
            sn = float(self.semi_minor_input.text() or 0.5)
            cx, cy = model["properties"]["position"][:2]
            center = QPointF(cx*100, -cy*100)
            direction = self.points[0] - center
            angle = math.atan2(-direction.y(), direction.x())
            motion["semi_major"] = sm
            motion["semi_minor"] = sn
            motion["angle"] = angle

        model["properties"]["motion"] = motion
        if model["status"] == "":
            model["status"] = "updated"

    def apply_changes(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error",
                                "Select a simulation and create/load a world first.")
            return
        self.apply_button.setEnabled(False)
        self.apply_button.setText("Applying…")
        self._worker = ApplyWorker(self.world_manager)
        self._worker.finished.connect(self._on_applied)
        self._worker.errored.connect(self._on_apply_error)
        self._worker.start()

    def _on_applied(self, errors):
        self.apply_button.setEnabled(True)
        self.apply_button.setText("Apply and Preview")
        self.wizard().refresh_canvas(self.scene)
        self._worker.deleteLater()
        self._worker = None
        if errors:
            detail = "\n".join(f"• {n}: {msg}" for n, msg in errors)
            QMessageBox.warning(
                self, "Partial Failure",
                f"{len(errors)} model(s) were not applied to Gazebo:\n\n{detail}\n\n"
                "Check the terminal for the raw Gazebo service output.\n"
                "You can click 'Apply and Preview' again to retry.",
            )
        else:
            QMessageBox.information(self, "Success", "All changes applied to Gazebo.")

    def _on_apply_error(self, msg):
        self.apply_button.setEnabled(True)
        self.apply_button.setText("Apply and Preview")
        self._worker.deleteLater()
        self._worker = None
        QMessageBox.critical(self, "Error", f"Failed to apply changes:\n{msg}")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None
