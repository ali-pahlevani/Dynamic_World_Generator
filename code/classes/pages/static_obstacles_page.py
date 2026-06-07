from PyQt5.QtWidgets import (
    QWizardPage, QHBoxLayout, QVBoxLayout, QFormLayout, QComboBox,
    QListWidget, QLineEdit, QMessageBox, QWidget, QGroupBox, QLabel,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QEvent, QPointF
from PyQt5.QtGui import QColor
from classes.zoomable_graphics_view import ZoomableGraphicsView
from classes.apply_worker import ApplyWorker
from classes.responsive_widgets import WrapButton


class StaticObstaclesPage(QWizardPage):
    def __init__(self, scene):
        super().__init__()
        self.setTitle("Add Static Obstacles")
        self.world_manager = None
        self.scene = scene

        # ── Left panel ─────────────────────────────────────────────
        self.left_widget = QWidget()
        self.left_widget.setFixedWidth(260)
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(10)

        # Type group
        type_group = QGroupBox("Obstacle Type")
        tg_layout = QVBoxLayout(type_group)
        tg_layout.setSpacing(6)
        self.obstacle_type_combo = QComboBox()
        self.obstacle_type_combo.addItems(["Box", "Cylinder", "Sphere"])
        self.obstacle_type_combo.currentTextChanged.connect(self.update_input_fields)
        tg_layout.addWidget(self.obstacle_type_combo)
        left_layout.addWidget(type_group)

        # Obstacle list group
        list_group = QGroupBox("Placed Obstacles")
        lg_layout = QVBoxLayout(list_group)
        lg_layout.setSpacing(6)
        self.obstacle_list = QListWidget()
        self.obstacle_list.setFixedHeight(110)
        lg_layout.addWidget(self.obstacle_list)
        self.remove_obstacle_button = WrapButton("Remove Selected", "danger")
        self.remove_obstacle_button.clicked.connect(self.remove_selected_obstacle)
        lg_layout.addWidget(self.remove_obstacle_button)
        left_layout.addWidget(list_group)

        # Dimensions group — QFormLayout keeps labels to the left of inputs
        dims_group = QGroupBox("Dimensions")
        dg_layout = QFormLayout(dims_group)
        dg_layout.setSpacing(6)
        dg_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self._lbl_w = QLabel("Width (m)")
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("0.5")
        dg_layout.addRow(self._lbl_w, self.width_input)

        self._lbl_l = QLabel("Length (m)")
        self.length_input = QLineEdit()
        self.length_input.setPlaceholderText("0.5")
        dg_layout.addRow(self._lbl_l, self.length_input)

        self._lbl_h = QLabel("Height (m)")
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("1.0")
        dg_layout.addRow(self._lbl_h, self.height_input)

        self._lbl_r = QLabel("Radius (m)")
        self.radius_input = QLineEdit()
        self.radius_input.setPlaceholderText("0.5")
        dg_layout.addRow(self._lbl_r, self.radius_input)

        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("Gray, Red, Blue …")
        dg_layout.addRow("Color", self.color_input)
        left_layout.addWidget(dims_group)

        hint = QLabel("Click on the canvas to place the obstacle")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #7F8C8D; font-size: 9pt;")
        left_layout.addWidget(hint)

        left_layout.addStretch(1)

        self.apply_button = WrapButton("Apply and Preview", "success")
        self.apply_button.clicked.connect(self.apply_changes)
        self.apply_button.setMinimumHeight(36)
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

        self.update_input_fields()

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error",
                                "Select a simulation and create/load a world first.")
            return
        self._refresh_list()

    def _refresh_list(self):
        self.obstacle_list.clear()
        self.wizard().refresh_canvas(self.scene)
        for m in self.world_manager.models:
            if m["type"] in ("box", "cylinder", "sphere"):
                self.obstacle_list.addItem(m["name"])

    # ── Input visibility ───────────────────────────────────────────────────

    def update_input_fields(self):
        otype = self.obstacle_type_combo.currentText()
        box = (otype == "Box")
        cyl = (otype == "Cylinder")
        sph = (otype == "Sphere")
        for w in (self._lbl_w, self.width_input, self._lbl_l, self.length_input):
            w.setVisible(box)
        for w in (self._lbl_h, self.height_input):
            w.setVisible(box or cyl)
        for w in (self._lbl_r, self.radius_input):
            w.setVisible(cyl or sph)

    # ── Grid snapping ──────────────────────────────────────────────────────

    def snap_to_grid(self, point, grid_spacing=10):
        return QPointF(
            round(point.x() / grid_spacing) * grid_spacing,
            round(point.y() / grid_spacing) * grid_spacing,
        )

    def _next_obstacle_name(self, obstacle_type):
        existing = {m["name"] for m in self.world_manager.models if m["status"] != "removed"}
        idx = 1
        while f"{obstacle_type}_{idx}" in existing:
            idx += 1
        return f"{obstacle_type}_{idx}"

    # ── Mouse interaction ──────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if (obj == self.view and self.world_manager and
                event.type() == QEvent.MouseButtonPress and
                event.button() == Qt.LeftButton):
            center = self.snap_to_grid(self.view.mapToScene(event.pos()))
            otype = self.obstacle_type_combo.currentText().lower()
            try:
                if otype == "box":
                    W = float(self.width_input.text() or 0.5)
                    L = float(self.length_input.text() or 0.5)
                    H = float(self.height_input.text() or 1.0)
                    size_m, position_z = (W, L, H), H / 2
                elif otype == "cylinder":
                    R = float(self.radius_input.text() or 0.5)
                    H = float(self.height_input.text() or 1.0)
                    size_m, position_z = (R, H), H / 2
                else:  # sphere
                    R = float(self.radius_input.text() or 0.5)
                    size_m, position_z = (R,), R
                color = self.color_input.text().strip() or "Gray"
                name = self._next_obstacle_name(otype)
                obstacle = {
                    "name": name,
                    "type": otype,
                    "properties": {
                        "position": (center.x() / 100, -center.y() / 100, position_z),
                        "size": size_m,
                        "color": color,
                    },
                    "status": "new",
                }
                self.world_manager.add_model(obstacle)
                self.obstacle_list.addItem(name)
                self.wizard().refresh_canvas(self.scene)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input",
                                    "Enter valid numeric values for dimensions.")
            return True
        return super().eventFilter(obj, event)

    # ── Obstacle actions ───────────────────────────────────────────────────

    def remove_selected_obstacle(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error",
                                "Select a simulation and create/load a world first.")
            return
        selected = self.obstacle_list.currentItem()
        if not selected:
            return
        name = selected.text()
        if name in self.wizard().obstacle_items:
            item, text = self.wizard().obstacle_items.pop(name)
            self.scene.removeItem(item)
            self.scene.removeItem(text)
        if name in self.wizard().path_items:
            for pi in self.wizard().path_items.pop(name):
                self.scene.removeItem(pi)
        for m in self.world_manager.models:
            if m["name"] == name:
                if m["status"] == "new":
                    # Never pushed to Gazebo — drop it outright so its name
                    # is immediately free for reuse by the next obstacle drawn.
                    self.world_manager.models.remove(m)
                else:
                    m["status"] = "removed"
                break
        self.obstacle_list.takeItem(self.obstacle_list.row(selected))

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
        # Apply may have renumbered obstacles to close gaps — rebuild the
        # list so displayed names match world_manager.models again.
        self.obstacle_list.clear()
        for m in self.world_manager.models:
            if m["type"] in ("box", "cylinder", "sphere") and m["status"] != "removed":
                self.obstacle_list.addItem(m["name"])
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
