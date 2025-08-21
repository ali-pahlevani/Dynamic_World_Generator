from PyQt5.QtWidgets import QWizardPage, QHBoxLayout, QVBoxLayout, QComboBox, QListWidget, QPushButton, QLineEdit, QMessageBox, QWidget
from PyQt5.QtCore import Qt, QEvent, QPointF
from PyQt5.QtGui import QColor
from classes.zoomable_graphics_view import ZoomableGraphicsView

class StaticObstaclesPage(QWizardPage):
    def __init__(self, scene):
        super().__init__()
        self.setTitle("Add Static Obstacles")
        self.world_manager = None
        self.scene = scene

        layout = QHBoxLayout()

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        self.obstacle_type_combo = QComboBox()
        self.obstacle_type_combo.addItems(["Box", "Cylinder", "Sphere"])
        self.obstacle_type_combo.currentTextChanged.connect(self.update_input_fields)
        left_layout.addWidget(self.obstacle_type_combo)

        self.obstacle_list = QListWidget()
        left_layout.addWidget(self.obstacle_list)

        self.remove_obstacle_button = QPushButton("Remove Selected Obstacle")
        self.remove_obstacle_button.clicked.connect(self.remove_selected_obstacle)
        left_layout.addWidget(self.remove_obstacle_button)

        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("Width (m) for Box")
        left_layout.addWidget(self.width_input)

        self.length_input = QLineEdit()
        self.length_input.setPlaceholderText("Length (m) for Box")
        left_layout.addWidget(self.length_input)

        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("Height (m)")
        left_layout.addWidget(self.height_input)

        self.radius_input = QLineEdit()
        self.radius_input.setPlaceholderText("Radius (m) for Cylinder/Sphere")
        left_layout.addWidget(self.radius_input)

        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("Color (e.g., Red)")
        left_layout.addWidget(self.color_input)

        self.apply_button = QPushButton("Apply and Preview")
        self.apply_button.clicked.connect(self.apply_changes)
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

        self.update_input_fields()

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")
            return
        self.refresh_obstacles()

    def refresh_obstacles(self):
        self.obstacle_list.clear()
        self.wizard().refresh_canvas(self.scene)
        for model in self.world_manager.models:
            if model["type"] in ["box", "cylinder", "sphere"]:
                self.obstacle_list.addItem(model["name"])

    def update_input_fields(self):
        obstacle_type = self.obstacle_type_combo.currentText()
        if obstacle_type == "Box":
            self.width_input.setEnabled(True)
            self.length_input.setEnabled(True)
            self.height_input.setEnabled(True)
            self.radius_input.setEnabled(False)
        elif obstacle_type == "Cylinder":
            self.width_input.setEnabled(False)
            self.length_input.setEnabled(False)
            self.height_input.setEnabled(True)
            self.radius_input.setEnabled(True)
        elif obstacle_type == "Sphere":
            self.width_input.setEnabled(False)
            self.length_input.setEnabled(False)
            self.height_input.setEnabled(False)
            self.radius_input.setEnabled(True)

    def snap_to_grid(self, point, grid_spacing=10):
        x = round(point.x() / grid_spacing) * grid_spacing
        y = round(point.y() / grid_spacing) * grid_spacing
        return QPointF(x, y)

    def eventFilter(self, obj, event):
        if obj == self.view and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton and self.world_manager:
            clicked_point = self.view.mapToScene(event.pos())
            center = self.snap_to_grid(clicked_point)
            obstacle_type = self.obstacle_type_combo.currentText().lower()
            try:
                if obstacle_type == "box":
                    W = float(self.width_input.text() or 0.1)
                    L = float(self.length_input.text() or 0.1)
                    H = float(self.height_input.text() or 1.0)
                    size_m = (W, L, H)
                    position_z = H / 2
                elif obstacle_type == "cylinder":
                    R = float(self.radius_input.text() or 0.5)
                    H = float(self.height_input.text() or 1.0)
                    size_m = (R, H)
                    position_z = H / 2
                elif obstacle_type == "sphere":
                    R = float(self.radius_input.text() or 0.5)
                    size_m = (R,)
                    position_z = R
                color = self.color_input.text() or "Gray"
                obstacle_name = f"{obstacle_type}_{len(self.world_manager.models) + 1}"
                x_m = center.x() / 100
                y_m = -center.y() / 100
                obstacle = {
                    "name": obstacle_name,
                    "type": obstacle_type,
                    "properties": {
                        "position": (x_m, y_m, position_z),
                        "size": size_m,
                        "color": color
                    },
                    "status": "new"
                }
                self.world_manager.add_model(obstacle)
                self.obstacle_list.addItem(obstacle_name)
                self.wizard().refresh_canvas(self.scene)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values for dimensions.")
            return True
        return super().eventFilter(obj, event)

    def remove_selected_obstacle(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")
            return
        selected = self.obstacle_list.currentItem()
        if selected:
            obstacle_name = selected.text()
            if obstacle_name in self.wizard().obstacle_items:
                item, text = self.wizard().obstacle_items[obstacle_name]
                self.scene.removeItem(item)
                self.scene.removeItem(text)
                del self.wizard().obstacle_items[obstacle_name]
            if obstacle_name in self.wizard().path_items:
                for path_item in self.wizard().path_items[obstacle_name]:
                    self.scene.removeItem(path_item)
                del self.wizard().path_items[obstacle_name]
            for model in self.world_manager.models:
                if model["name"] == obstacle_name:
                    model["status"] = "removed"
                    break
            self.obstacle_list.takeItem(self.obstacle_list.row(selected))

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