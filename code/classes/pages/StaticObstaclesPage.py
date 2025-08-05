from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QComboBox, QGraphicsView, QGraphicsScene, QMessageBox, QGraphicsRectItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QEvent
from PyQt5.QtGui import QPen, QColor

class StaticObstaclesPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Add Static Obstacles")
        self.world_manager = None
        self.obstacle_items = {}  # Dictionary to store obstacle items

        layout = QHBoxLayout()

        # Left section (30%)
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

        layout.addLayout(left_layout, 30)

        # Right section (70%) - Canvas
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("white"))
        self.view.installEventFilter(self)  # Install event filter
        layout.addWidget(self.view, 70)

        self.setLayout(layout)

        # Canvas interaction
        self.drawing = False
        self.start_point = None
        self.current_item = None

        # Initialize input fields based on default obstacle妆type
        self.update_input_fields()

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")

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

    def eventFilter(self, obj, event):
        if obj == self.view:
            print("Event:", event.type())
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton and self.world_manager:
                self.drawing = True
                self.start_point = self.view.mapToScene(event.pos())
                obstacle_type = self.obstacle_type_combo.currentText()
                if obstacle_type == "Box":
                    self.current_item = QGraphicsRectItem(QRectF(self.start_point, self.start_point))
                    self.current_item.setPen(QPen(Qt.black, 2))  # Add this line
                    self.current_item.setBrush(QColor("lightgray"))  # Optional: Add fill
                elif obstacle_type in ["Cylinder", "Sphere"]:
                    self.current_item = QGraphicsEllipseItem(QRectF(self.start_point, self.start_point))
                    self.current_item.setPen(QPen(Qt.black, 2))  # Add this line
                    self.current_item.setBrush(QColor("lightgray"))  # Optional: Add fill
                self.scene.addItem(self.current_item)
                return True
            elif event.type() == QEvent.MouseMove and self.drawing and self.current_item:
                end_point = self.view.mapToScene(event.pos())
                if isinstance(self.current_item, QGraphicsRectItem):
                    rect = QRectF(self.start_point, end_point).normalized()
                    self.current_item.setRect(rect)
                elif isinstance(self.current_item, QGraphicsEllipseItem):
                    radius = (end_point - self.start_point).manhattanLength() / 2
                    center = self.start_point + (end_point - self.start_point) / 2
                    self.current_item.setRect(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton and self.drawing and self.world_manager:
                self.drawing = False
                obstacle_type = self.obstacle_type_combo.currentText()
                obstacle_name = f"{obstacle_type.lower()}_{len(self.world_manager.models) + 1}"
                center = self.current_item.rect().center()
                x = center.x() / 100
                y = center.y() / 100
                if obstacle_type == "Box":
                    rect = self.current_item.rect()
                    width_m = rect.width() / 100
                    depth_m = rect.height() / 100
                    try:
                        height_m = float(self.height_input.text() or 1.0)
                    except ValueError:
                        height_m = 1.0
                    position_z = height_m / 2
                    size = (width_m, depth_m, height_m)
                elif obstacle_type == "Cylinder":
                    rect = self.current_item.rect()
                    radius_m = rect.width() / 2 / 100
                    try:
                        height_m = float(self.height_input.text() or 1.0)
                    except ValueError:
                        height_m = 1.0
                    position_z = height_m / 2
                    size = (radius_m, height_m)
                elif obstacle_type == "Sphere":
                    rect = self.current_item.rect()
                    radius_m = rect.width() / 2 / 100
                    position_z = radius_m
                    size = (radius_m,)

                color = self.color_input.text() or "Gray"
                obstacle = {
                    "name": obstacle_name,
                    "type": obstacle_type.lower(),
                    "properties": {
                        "position": (x, y, position_z),
                        "size": size,
                        "color": color
                    },
                    "status": "new"
                }
                self.world_manager.add_model(obstacle)
                self.obstacle_list.addItem(obstacle_name)
                self.obstacle_items[obstacle_name] = self.current_item
                return True
        return super().eventFilter(obj, event)

    def remove_selected_obstacle(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")
            return
        selected = self.obstacle_list.currentItem()
        if selected:
            obstacle_name = selected.text()
            if obstacle_name in self.obstacle_items:
                self.scene.removeItem(self.obstacle_items[obstacle_name])
                del self.obstacle_items[obstacle_name]
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
            QMessageBox.information(self, "Success", "Changes applied successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {str(e)}")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None