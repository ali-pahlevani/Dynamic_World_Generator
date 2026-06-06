import math
import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import (
    QBrush, QColor, QFont, QImage, QPainter, QPen, QPixmap,
)
from PyQt5.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QSizePolicy, QVBoxLayout, QWidget, QWizardPage,
)
from classes.responsive_widgets import WrapButton

from utils.config import MAPS_DIR



class MapGenerationPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Generate Map")
        self.world_manager = None
        self._current_qimage = None

        # ── Left panel ─────────────────────────────────────────────
        self.left_widget = QWidget()
        self.left_widget.setFixedWidth(260)
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        # Map name
        name_group = QGroupBox("Map Name")
        ng_layout = QVBoxLayout(name_group)
        ng_layout.setSpacing(4)
        self.map_name_input = QLineEdit("my_map")
        self.map_name_input.setPlaceholderText("my_map")
        self.map_name_input.textChanged.connect(self._on_map_name_changed)
        ng_layout.addWidget(self.map_name_input)
        left_layout.addWidget(name_group)

        # YAML settings — QFormLayout keeps labels to the left of inputs
        yaml_group = QGroupBox("Map Settings (YAML)")
        yg_layout = QFormLayout(yaml_group)
        yg_layout.setSpacing(5)
        yg_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.image_name_label = QLabel("my_map.pgm")
        self.image_name_label.setStyleSheet("color: #7F8C8D; font-size: 9pt; padding: 2px 4px;")
        yg_layout.addRow("Image (auto)", self.image_name_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["trinary", "scale", "raw"])
        yg_layout.addRow("Mode", self.mode_combo)

        self.resolution_input = QLineEdit("0.05")
        self.resolution_input.textChanged.connect(self._schedule_preview)
        yg_layout.addRow("Res. (m/px)", self.resolution_input)

        origin_widget = QWidget()
        origin_row = QHBoxLayout(origin_widget)
        origin_row.setContentsMargins(0, 0, 0, 0)
        origin_row.setSpacing(4)
        self.origin_x_input = QLineEdit()
        self.origin_x_input.setPlaceholderText("X")
        self.origin_x_input.textChanged.connect(self._schedule_preview)
        self.origin_y_input = QLineEdit()
        self.origin_y_input.setPlaceholderText("Y")
        self.origin_y_input.textChanged.connect(self._schedule_preview)
        origin_row.addWidget(self.origin_x_input)
        origin_row.addWidget(self.origin_y_input)
        yg_layout.addRow("Origin X/Y", origin_widget)

        self.negate_combo = QComboBox()
        self.negate_combo.addItems(["0", "1"])
        yg_layout.addRow("Negate", self.negate_combo)

        self.occ_thresh_input = QLineEdit("0.65")
        yg_layout.addRow("Occ. thresh", self.occ_thresh_input)

        self.free_thresh_input = QLineEdit("0.25")
        yg_layout.addRow("Free thresh", self.free_thresh_input)

        left_layout.addWidget(yaml_group)
        left_layout.addStretch(1)

        self.generate_button = WrapButton("Generate Map", "success")
        self.generate_button.clicked.connect(self._generate_map)
        self.generate_button.setMinimumHeight(36)
        left_layout.addWidget(self.generate_button)

        # ── Preview panel ──────────────────────────────────────────
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(
            "background-color: #F4F6F9;"
            "border: 1px solid #D5D8DC;"
        )
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setText("No world loaded — map preview will appear here")
        self.preview_label.setFont(QFont("Arial", 10))

        # ── Main layout ────────────────────────────────────────────
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.left_widget)
        layout.addWidget(self.preview_label, 1)

        # 400 ms debounce for live preview refresh
        self._refresh_timer = QTimer()
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(400)
        self._refresh_timer.timeout.connect(self._refresh_preview)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if self.world_manager:
            self._auto_set_origin()
            self._refresh_preview()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _on_map_name_changed(self, name):
        name = name.strip() or "my_map"
        self.image_name_label.setText(f"{name}.pgm")

    def _schedule_preview(self):
        self._refresh_timer.start()

    def _parse_resolution(self):
        try:
            r = float(self.resolution_input.text())
            return r if r > 0 else 0.05
        except ValueError:
            return 0.05

    def _parse_origin(self):
        try:
            ox = float(self.origin_x_input.text())
        except ValueError:
            ox = -10.0
        try:
            oy = float(self.origin_y_input.text())
        except ValueError:
            oy = -10.0
        return ox, oy

    def _static_models(self):
        """Yield models that should appear on the 2-D map (no dynamics, not removed)."""
        if not self.world_manager:
            return
        for m in self.world_manager.models:
            if m.get("status") == "removed":
                continue
            if "motion" in m.get("properties", {}):
                continue
            yield m

    # ── Auto-origin ────────────────────────────────────────────────────────

    def _auto_set_origin(self):
        """Set origin_x/y so all static objects fit in the map with 2 m padding."""
        min_x = min_y = float("inf")
        for m in self._static_models():
            props = m["properties"]
            mtype = m["type"]
            if mtype == "wall":
                for pt in (props["start"], props["end"]):
                    min_x = min(min_x, pt[0])
                    min_y = min(min_y, pt[1])
            elif mtype in ("box", "cylinder", "sphere"):
                x, y = props["position"][:2]
                r = max(props["size"]) / 2
                min_x = min(min_x, x - r)
                min_y = min(min_y, y - r)

        if math.isinf(min_x):
            min_x, min_y = -10.0, -10.0
        else:
            min_x = math.floor(min_x - 2)
            min_y = math.floor(min_y - 2)

        self.origin_x_input.setText(str(float(min_x)))
        self.origin_y_input.setText(str(float(min_y)))

    # ── Map size ───────────────────────────────────────────────────────────

    def _compute_map_size(self, resolution, ox, oy):
        """Return (width_px, height_px) covering all static objects + 2 m padding."""
        max_x = ox + 20
        max_y = oy + 20

        for m in self._static_models():
            props = m["properties"]
            mtype = m["type"]
            if mtype == "wall":
                for pt in (props["start"], props["end"]):
                    max_x = max(max_x, pt[0])
                    max_y = max(max_y, pt[1])
            elif mtype in ("box", "cylinder", "sphere"):
                x, y = props["position"][:2]
                r = max(props["size"]) / 2
                max_x = max(max_x, x + r)
                max_y = max(max_y, y + r)

        pad = 2.0
        width_px  = max(10, int((max_x - ox + pad) / resolution) + 1)
        height_px = max(10, int((max_y - oy + pad) / resolution) + 1)
        return width_px, height_px

    # ── Rendering ──────────────────────────────────────────────────────────

    def _render_map(self, resolution, ox, oy, width_px, height_px):
        """Return a QImage (Grayscale8) of the occupancy map.

        Convention (ROS nav_msgs/OccupancyGrid):
          254 = free space (light)
            0 = occupied  (dark)
          The origin [ox, oy] is the bottom-left corner of the image.
        """
        img = QImage(width_px, height_px, QImage.Format_Grayscale8)
        img.fill(254)  # free

        if not self.world_manager:
            return img

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, False)
        occupied = QColor(0, 0, 0)

        def to_px(wx, wy):
            col = (wx - ox) / resolution
            row = height_px - 1 - (wy - oy) / resolution
            return col, row

        for m in self._static_models():
            props = m["properties"]
            mtype = m["type"]

            if mtype == "wall":
                x1, y1 = to_px(*props["start"])
                x2, y2 = to_px(*props["end"])
                thickness = max(1, int(props.get("width", 0.1) / resolution))
                pen = QPen(occupied, thickness, Qt.SolidLine, Qt.FlatCap)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(int(round(x1)), int(round(y1)),
                                 int(round(x2)), int(round(y2)))

            elif mtype == "box":
                x, y = props["position"][:2]
                W, L = props["size"][0], props["size"][1]
                cx, cy = to_px(x, y)
                hw = W / (2 * resolution)
                hl = L / (2 * resolution)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(occupied))
                painter.drawRect(
                    int(round(cx - hw)), int(round(cy - hl)),
                    max(1, int(round(2 * hw))), max(1, int(round(2 * hl)))
                )

            elif mtype in ("cylinder", "sphere"):
                x, y = props["position"][:2]
                r = props["size"][0]
                cx, cy = to_px(x, y)
                r_px = r / resolution
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(occupied))
                painter.drawEllipse(
                    int(round(cx - r_px)), int(round(cy - r_px)),
                    max(1, int(round(2 * r_px))), max(1, int(round(2 * r_px)))
                )

        painter.end()
        return img

    def _refresh_preview(self):
        if not self.world_manager:
            return
        resolution = self._parse_resolution()
        ox, oy = self._parse_origin()
        w, h = self._compute_map_size(resolution, ox, oy)
        self._current_qimage = self._render_map(resolution, ox, oy, w, h)
        self._update_preview_display()

    def _update_preview_display(self):
        if self._current_qimage is None:
            return
        pixmap = QPixmap.fromImage(self._current_qimage)
        available = self.preview_label.size()
        scaled = pixmap.scaled(available, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_preview_display()

    # ── Map generation ────────────────────────────────────────────────────

    def _generate_map(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "No world loaded.")
            return

        map_name = self.map_name_input.text().strip()
        if not map_name:
            QMessageBox.warning(self, "Error", "Please enter a map name.")
            return

        resolution = self._parse_resolution()
        ox, oy = self._parse_origin()
        width_px, height_px = self._compute_map_size(resolution, ox, oy)

        qimage = self._render_map(resolution, ox, oy, width_px, height_px)
        self._current_qimage = qimage
        self._update_preview_display()

        # Determine output folder
        simulation = getattr(self.world_manager, "simulation", "gazebo")
        version    = getattr(self.world_manager, "version",    "harmonic")
        out_dir = os.path.join(MAPS_DIR, simulation, version, map_name)
        os.makedirs(out_dir, exist_ok=True)

        pgm_path  = os.path.join(out_dir, f"{map_name}.pgm")
        yaml_path = os.path.join(out_dir, f"{map_name}.yaml")

        self._save_pgm(qimage, pgm_path)
        self._save_yaml(yaml_path, map_name, resolution, ox, oy)

        QMessageBox.information(
            self, "Map Generated",
            f"Map saved to:\n{out_dir}\n\n"
            f"  {map_name}.pgm  ({width_px} × {height_px} px)\n"
            f"  {map_name}.yaml",
        )

    def _save_yaml(self, path, map_name, resolution, ox, oy):
        try:
            occ  = float(self.occ_thresh_input.text())
        except ValueError:
            occ = 0.65
        try:
            free = float(self.free_thresh_input.text())
        except ValueError:
            free = 0.25
        negate = int(self.negate_combo.currentText())
        mode   = self.mode_combo.currentText()

        content = (
            f"image: {map_name}.pgm\n"
            f"mode: {mode}\n"
            f"resolution: {resolution}\n"
            f"origin: [{ox}, {oy}, 0]\n"
            f"negate: {negate}\n"
            f"occupied_thresh: {occ}\n"
            f"free_thresh: {free}\n"
        )
        with open(path, "w") as f:
            f.write(content)

    @staticmethod
    def _save_pgm(qimage, path):
        """Write QImage as a binary PGM (P5) file — no external dependencies."""
        if qimage.format() != QImage.Format_Grayscale8:
            qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
        w, h   = qimage.width(), qimage.height()
        stride = qimage.bytesPerLine()
        bits   = qimage.bits()
        bits.setsize(h * stride)
        with open(path, "wb") as f:
            f.write(f"P5\n{w} {h}\n255\n".encode())
            for row in range(h):
                f.write(bytes(bits[row * stride: row * stride + w]))

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None
