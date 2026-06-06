from PyQt5.QtWidgets import (
    QWizardPage, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit,
    QListWidget, QMessageBox, QWidget, QGroupBox, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt, QEvent, QPointF
from PyQt5.QtGui import QColor, QFont
from classes.zoomable_graphics_view import ZoomableGraphicsView
import os
import re
import shutil
from xml.etree import ElementTree as ET
from utils.config import WORLDS_GAZEBO_DIR

_VALID_WORLD_NAME = re.compile(r'^[A-Za-z0-9_]+$')


def _btn(text, role=None):
    b = QPushButton(text)
    if role:
        b.setProperty("btnRole", role)
    return b


class WallsDesignPage(QWizardPage):
    def __init__(self, scene):
        super().__init__()
        self.setTitle("Design Walls")
        self.world_manager = None
        self.scene = scene

        # ── Left panel ─────────────────────────────────────────────
        self.left_widget = QWidget()
        self.left_widget.setFixedWidth(260)
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(10)

        # World group
        world_group = QGroupBox("World")
        wg_layout = QVBoxLayout(world_group)
        wg_layout.setSpacing(6)
        wg_layout.addWidget(QLabel("Name"))
        self.world_name_input = QLineEdit()
        self.world_name_input.setPlaceholderText("e.g. my_world")
        wg_layout.addWidget(self.world_name_input)
        btn_row = QHBoxLayout()
        self.create_world_button = _btn("Create New")
        self.create_world_button.clicked.connect(self.create_new_world)
        self.load_world_button = _btn("Load")
        self.load_world_button.clicked.connect(self.load_world)
        btn_row.addWidget(self.create_world_button)
        btn_row.addWidget(self.load_world_button)
        wg_layout.addLayout(btn_row)
        left_layout.addWidget(world_group)

        # Walls group
        walls_group = QGroupBox("Walls")
        wls_layout = QVBoxLayout(walls_group)
        wls_layout.setSpacing(6)
        self.wall_list = QListWidget()
        self.wall_list.setFixedHeight(120)
        wls_layout.addWidget(self.wall_list)
        self.remove_wall_button = _btn("Remove Selected", "danger")
        self.remove_wall_button.clicked.connect(self.remove_selected_wall)
        wls_layout.addWidget(self.remove_wall_button)
        left_layout.addWidget(walls_group)

        # Properties group
        props_group = QGroupBox("Wall Properties")
        pg_layout = QVBoxLayout(props_group)
        pg_layout.setSpacing(6)
        pg_layout.addWidget(QLabel("Width (m)"))
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("0.1")
        pg_layout.addWidget(self.width_input)
        pg_layout.addWidget(QLabel("Height (m)"))
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("1.0")
        pg_layout.addWidget(self.height_input)
        pg_layout.addWidget(QLabel("Color"))
        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("Gray, Black, Red …")
        pg_layout.addWidget(self.color_input)
        left_layout.addWidget(props_group)

        hint = QLabel("Click canvas: 1st point → 2nd point places a wall")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #7F8C8D; font-size: 9pt;")
        left_layout.addWidget(hint)

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

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def initializePage(self):
        self.world_manager = self.wizard().world_manager

    # ── Grid snapping ──────────────────────────────────────────────────────

    def snap_to_grid(self, point, grid_spacing=10):
        return QPointF(
            round(point.x() / grid_spacing) * grid_spacing,
            round(point.y() / grid_spacing) * grid_spacing,
        )

    def _next_wall_name(self):
        existing = {m["name"] for m in self.world_manager.models}
        idx = 1
        while f"wall_{idx}" in existing:
            idx += 1
        return f"wall_{idx}"

    # ── Mouse interaction ──────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj == self.view and self.world_manager:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                pt = self.snap_to_grid(self.view.mapToScene(event.pos()))
                if not hasattr(self, "_start_point"):
                    self._start_point = pt
                else:
                    name = self._next_wall_name()
                    wall = {
                        "name": name,
                        "type": "wall",
                        "properties": {
                            "start": (self._start_point.x() / 100, -self._start_point.y() / 100),
                            "end":   (pt.x() / 100, -pt.y() / 100),
                            "width": float(self.width_input.text() or 0.1),
                            "height": float(self.height_input.text() or 1.0),
                            "color": self.color_input.text().strip() or "Gray",
                        },
                        "status": "new",
                    }
                    self.world_manager.add_model(wall)
                    self.wall_list.addItem(name)
                    self.wizard().refresh_canvas(self.scene)
                    del self._start_point
                return True
        return super().eventFilter(obj, event)

    # ── World actions ──────────────────────────────────────────────────────

    def create_new_world(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        world_name = self.world_name_input.text().strip()
        if not world_name:
            QMessageBox.warning(self, "Error", "Please enter a world name.")
            return
        if not _VALID_WORLD_NAME.match(world_name):
            QMessageBox.warning(self, "Invalid Name",
                "World names may only contain letters, numbers, and underscores.\n"
                "Spaces and special characters are not allowed by Gazebo.\n\n"
                f"Try: {re.sub(r'[^A-Za-z0-9_]', '_', world_name)}")
            return
        try:
            empty = os.path.join(WORLDS_GAZEBO_DIR, self.world_manager.version, "empty_world.sdf")
            if not os.path.exists(empty):
                raise FileNotFoundError(f"Empty world template not found: {empty}")
            dest = os.path.join(WORLDS_GAZEBO_DIR, self.world_manager.version, f"{world_name}.sdf")
            shutil.copyfile(empty, dest)
            tree = ET.parse(dest)
            root = tree.getroot()
            world_elem = root.find("world")
            if world_elem is None:
                raise ValueError("SDF file has no <world> element")
            world_elem.set("name", world_name)
            tree.write(dest, encoding="utf-8", xml_declaration=True)
            self.world_manager.load_world(world_name)
            self.wall_list.clear()
            self.wizard().refresh_canvas(self.scene)
            QMessageBox.information(self, "Success", f"Created world: {world_name}")
            self.completeChanged.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create world:\n{e}")

    def load_world(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        world_name = self.world_name_input.text().strip()
        if not world_name:
            QMessageBox.warning(self, "Error", "Please enter a world name.")
            return
        if not _VALID_WORLD_NAME.match(world_name):
            QMessageBox.warning(self, "Invalid Name",
                "World names may only contain letters, numbers, and underscores.\n"
                "Spaces and special characters are not valid Gazebo service names.\n\n"
                f"Rename the SDF file and its <world name=''> attribute to: "
                f"{re.sub(r'[^A-Za-z0-9_]', '_', world_name)}")
            return
        try:
            self.world_manager.load_world(world_name)
            self.wall_list.clear()
            self.wizard().refresh_canvas(self.scene)
            for m in self.world_manager.models:
                if m["type"] == "wall":
                    self.wall_list.addItem(m["name"])
            QMessageBox.information(self, "Success", f"Loaded world: {world_name}")
            self.completeChanged.emit()
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load world:\n{e}")

    def remove_selected_wall(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        selected = self.wall_list.currentItem()
        if not selected:
            return
        name = selected.text()
        if name in self.wizard().wall_items:
            line, text = self.wizard().wall_items.pop(name)
            self.scene.removeItem(line)
            self.scene.removeItem(text)
        for m in self.world_manager.models:
            if m["name"] == name:
                m["status"] = "removed"
                break
        self.wall_list.takeItem(self.wall_list.row(selected))

    def apply_changes(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        try:
            errors = self.world_manager.apply_changes()
            self.wizard().refresh_canvas(self.scene)
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
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes:\n{e}")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None
