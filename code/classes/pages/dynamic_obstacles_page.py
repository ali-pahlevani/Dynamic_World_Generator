from PyQt5.QtWidgets import QWizardPage, QHBoxLayout, QVBoxLayout, QComboBox, QListWidget, QPushButton, QLineEdit, QMessageBox, QWidget
from PyQt5.QtCore import Qt, QEvent, QPointF, QLineF, QRectF
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QWizardPage, QHBoxLayout, QVBoxLayout, QComboBox, QListWidget, QPushButton, QLineEdit, QMessageBox, QGraphicsLineItem, QGraphicsEllipseItem
from classes.zoomable_graphics_view import ZoomableGraphicsView
import math

class DynamicObstaclesPage(QWizardPage):
    def __init__(self, scene):
        super().__init__()
        self.setTitle("Add Dynamic Obstacles")
        self.world_manager = None
        self.scene = scene
        self.obstacle_list = QListWidget()
        self.motion_type_combo = QComboBox()
        self.motion_type_combo.addItems(["Linear", "Elliptical", "Polygon"])
        self.velocity_input = QLineEdit()
        self.velocity_input.setPlaceholderText("Velocity (m/s)")
        self.std_input = QLineEdit()
        self.std_input.setPlaceholderText("Std of randomness in velocity")
        self.semi_major_input = QLineEdit()
        self.semi_major_input.setPlaceholderText("Semi-major axis for Elliptical")
        self.semi_major_input.setEnabled(False)
        self.semi_minor_input = QLineEdit()
        self.semi_minor_input.setPlaceholderText("Semi-minor axis for Elliptical")
        self.semi_minor_input.setEnabled(False)
        self.start_button = QPushButton("Start Defining Path")
        self.start_button.clicked.connect(self.start_path)
        self.finish_button = QPushButton("Finish Path")
        self.finish_button.clicked.connect(self.finish_path)
        self.apply_button = QPushButton("Apply and Preview")
        self.apply_button.clicked.connect(self.apply_changes)

        layout = QHBoxLayout()

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.motion_type_combo)
        left_layout.addWidget(self.obstacle_list)
        left_layout.addWidget(self.velocity_input)
        left_layout.addWidget(self.std_input)
        left_layout.addWidget(self.semi_major_input)
        left_layout.addWidget(self.semi_minor_input)
        left_layout.addWidget(self.start_button)
        left_layout.addWidget(self.finish_button)
        left_layout.addWidget(self.apply_button)
        left_widget.setLayout(left_layout)

        self.view = ZoomableGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("white"))
        self.view.installEventFilter(self)

        # Set size constraints: canvas at 70% of content width, left panel takes the rest
        window_width = 1500  # Default wizard width
        canvas_width = int(window_width * 0.7)  # 70% of window width
        self.view.setMinimumWidth(int(800 * 0.7))  # Minimum canvas width (70% of 800px window)
        self.view.setMaximumWidth(canvas_width)  # Initial canvas width
        left_widget.setMinimumWidth(150)  # Minimum left panel width for usability
        left_widget.setMaximumWidth(window_width - canvas_width - 260)  # Initial left panel width

        layout.addWidget(left_widget)
        layout.addWidget(self.view)

        self.setLayout(layout)

        self.current_obstacle = None
        self.current_motion_type = None
        self.points = []
        self.clicking_enabled = False

        # Initialize motion type and input field states after widget creation
        self.current_motion_type = self.motion_type_combo.currentText().lower()
        self.semi_major_input.setEnabled(self.current_motion_type == "elliptical")
        self.semi_minor_input.setEnabled(self.current_motion_type == "elliptical")

        self.motion_type_combo.currentTextChanged.connect(self.update_motion_type)
        self.obstacle_list.itemClicked.connect(self.select_obstacle)

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")
            return
        self.obstacle_list.clear()
        for model in self.world_manager.models:
            if model["type"] in ["box", "cylinder", "sphere"]:
                self.obstacle_list.addItem(model["name"])
        self.wizard().refresh_canvas(self.scene)

    def update_motion_type(self, text):
        self.current_motion_type = text.lower()
        self.clear_path()
        self.points = []
        self.semi_major_input.setEnabled(self.current_motion_type == "elliptical")
        self.semi_minor_input.setEnabled(self.current_motion_type == "elliptical")

    def select_obstacle(self, item):
        self.current_obstacle = item.text()
        model = next((m for m in self.world_manager.models if m["name"] == self.current_obstacle), None)
        if model and "motion" in model["properties"]:
            motion = model["properties"]["motion"]
            self.motion_type_combo.blockSignals(True)
            self.motion_type_combo.setCurrentText(motion["type"].capitalize())
            self.motion_type_combo.blockSignals(False)
            self.current_motion_type = motion["type"]
            self.velocity_input.setText(str(motion["velocity"]))
            self.std_input.setText(str(motion["std"]))
            if motion["type"] == "elliptical":
                self.semi_major_input.setText(str(motion["semi_major"]))
                self.semi_minor_input.setText(str(motion["semi_minor"]))
            if motion["type"] in ["linear", "polygon"]:
                self.points = [QPointF(x * 100, y * 100) for x, y in motion["path"]]
            elif motion["type"] == "elliptical":
                center_m = model["properties"]["position"][:2]
                center = QPointF(center_m[0] * 100, -center_m[1] * 100)
                angle = motion["angle"]
                dx = motion["semi_major"] * 100 * math.cos(angle)
                dy = -motion["semi_major"] * 100 * math.sin(angle)
                self.points = [center + QPointF(dx, dy)]
            self.draw_path(close_polygon=(motion["type"] == "polygon"))
        else:
            self.clear_path()
            self.points = []
            self.velocity_input.clear()
            self.std_input.clear()
            self.semi_major_input.clear()
            self.semi_minor_input.clear()

    def start_path(self):
        if self.current_obstacle and self.current_motion_type:
            self.clicking_enabled = True
            self.points = []
            self.clear_path()

    def finish_path(self):
        self.clicking_enabled = False
        self.draw_path(close_polygon=True if self.current_motion_type == "polygon" else False)
        self.store_motion()

    def eventFilter(self, obj, event):
        if obj == self.view and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton and self.clicking_enabled:
            clicked_point = self.view.mapToScene(event.pos())
            point = self.snap_to_grid(clicked_point)
            self.points.append(point)
            if self.current_motion_type == "linear" and len(self.points) == 2:
                self.clicking_enabled = False
                self.draw_path()
                self.store_motion()
            elif self.current_motion_type == "elliptical" and len(self.points) == 1:
                self.clicking_enabled = False
                self.draw_path()
                self.store_motion()
            elif self.current_motion_type == "polygon":
                self.draw_path()
            return True
        return super().eventFilter(obj, event)

    def snap_to_grid(self, point, grid_spacing=10):
        x = round(point.x() / grid_spacing) * grid_spacing
        y = round(point.y() / grid_spacing) * grid_spacing
        return QPointF(x, y)

    def clear_path(self):
        if self.current_obstacle and self.current_obstacle in self.wizard().path_items:
            for item in self.wizard().path_items[self.current_obstacle]:
                self.scene.removeItem(item)
            del self.wizard().path_items[self.current_obstacle]

    def draw_path(self, close_polygon=False):
        self.clear_path()
        items = []
        color = {"linear": "red", "elliptical": "green", "polygon": "blue"}[self.current_motion_type]
        if self.current_motion_type == "linear" and len(self.points) == 2:
            line = QGraphicsLineItem(QLineF(self.points[0], self.points[1]))
            line.setPen(QPen(QColor(color), 2))
            self.scene.addItem(line)
            items.append(line)
        elif self.current_motion_type == "elliptical" and len(self.points) == 1:
            try:
                semi_major = float(self.semi_major_input.text() or 1.0)
                semi_minor = float(self.semi_minor_input.text() or 0.5)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter valid semi-major and semi-minor axes.")
                return
            model = next(m for m in self.world_manager.models if m["name"] == self.current_obstacle)
            center_m = model["properties"]["position"][:2]
            center = QPointF(center_m[0] * 100, -center_m[1] * 100)
            direction = self.points[0] - center
            angle = math.degrees(math.atan2(-direction.y(), direction.x()))
            ellipse = QGraphicsEllipseItem(QRectF(-semi_major * 100, -semi_minor * 100, 2 * semi_major * 100, 2 * semi_minor * 100))
            ellipse.setPos(center)
            ellipse.setRotation(-angle)
            ellipse.setPen(QPen(QColor(color), 2))
            self.scene.addItem(ellipse)
            items.append(ellipse)
        elif self.current_motion_type == "polygon" and len(self.points) >= 2:
            for i in range(len(self.points) - 1):
                line = QGraphicsLineItem(QLineF(self.points[i], self.points[i+1]))
                line.setPen(QPen(QColor(color), 2))
                self.scene.addItem(line)
                items.append(line)
            if close_polygon and len(self.points) >= 3:
                line = QGraphicsLineItem(QLineF(self.points[-1], self.points[0]))
                line.setPen(QPen(QColor(color), 2))
                self.scene.addItem(line)
                items.append(line)
        self.wizard().path_items[self.current_obstacle] = items

    def store_motion(self):
        if not self.current_obstacle or not self.current_motion_type or not self.points:
            return
        try:
            velocity = float(self.velocity_input.text() or 1.0)
            std = float(self.std_input.text() or 0.1)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid velocity and std.")
            return
        model = next(m for m in self.world_manager.models if m["name"] == self.current_obstacle)
        motion = {"type": self.current_motion_type, "velocity": velocity, "std": std}
        if self.current_motion_type in ["linear", "polygon"]:
            path_m = [(p.x() / 100, -p.y() / 100) for p in self.points]
            motion["path"] = path_m
        elif self.current_motion_type == "elliptical":
            semi_major = float(self.semi_major_input.text() or 1.0)
            semi_minor = float(self.semi_minor_input.text() or 0.5)
            center_m = model["properties"]["position"][:2]
            center = QPointF(center_m[0] * 100, -center_m[1] * 100)
            direction = self.points[0] - center
            angle = math.atan2(-direction.y(), direction.x())
            motion["semi_major"] = semi_major
            motion["semi_minor"] = semi_minor
            motion["angle"] = angle
        model["properties"]["motion"] = motion
        model["status"] = "updated" if model.get("status") else "new"

    def apply_changes(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")
            return
        try:
            self.world_manager.apply_changes()
            self.wizard().refresh_canvas(self.scene)
            QMessageBox.information(self, "Success", "Changes applied successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {str(e)}")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None