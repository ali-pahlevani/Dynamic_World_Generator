#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
import math
from xml.etree import ElementTree as ET
from PyQt5.QtWidgets import QWizard, QWizardPage, QListWidget, QVBoxLayout, QHBoxLayout, QWidget, QApplication, QPushButton, QLabel, QLineEdit, QComboBox, QGraphicsView, QGraphicsScene, QMessageBox, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QFrame
from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF, QEvent, pyqtSignal, QSize, pyqtProperty
from PyQt5.QtGui import QFont, QPen, QColor, QPixmap, QMovie
import shlex
import time

def get_color(color_name):
    colors = {
        "Black": (0, 0, 0),
        "Gray": (0.5, 0.5, 0.5),
        "White": (1, 1, 1),
        "Red": (1, 0, 0),
        "Blue": (0, 0, 1),
        "Green": (0, 1, 0)
    }
    return colors.get(color_name, (0.5, 0.5, 0.5))

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.scale_label = QLabel("1 pixel = 1 cm", self)
        self.scale_label.setStyleSheet("background: transparent; font-size: 11pt; font-weight: bold; color: red;")
        self.scale_label.setGeometry(10, self.height() - 38, 100, 20)
        self.is_panning = False
        self.last_pan_point = QPointF()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale_label.move(10, self.height() - 38)

    def wheelEvent(self, event):
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_panning:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self.last_pan_point)
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
            self.last_pan_point = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Let's make a 'Dynamic World' together!")

        # Main layout for vertical centering
        main_layout = QVBoxLayout()
        main_layout.addStretch(1)  # Stretch above to center vertically

        # Nested layout for title and GIF
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)  # Preserve 10-pixel spacing between title and GIF

        title_label = QLabel("Welcome to the Dynamic World Generator Wizard!")
        title_label.setStyleSheet("font-size: 26pt; font-weight: bold; color: red;")
        title_label.setAlignment(Qt.AlignCenter)  # Center horizontally
        content_layout.addWidget(title_label)

        gif_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "welcome.gif")
        print(f"Looking for GIF at: {gif_path}")

        gif_label = QLabel()
        movie = QMovie(gif_path)
        if movie.isValid():
            movie.setScaledSize(QSize(1200, 750))  # Set GIF size to 1200x750 pixels
            gif_label.setMovie(movie)
            movie.start()
        else:
            gif_label.setText(f"Preview GIF not found at {gif_path}")
        gif_label.setAlignment(Qt.AlignCenter)  # Center horizontally
        content_layout.addWidget(gif_label)

        main_layout.addLayout(content_layout)
        main_layout.addStretch(1)  # Stretch below to center vertically

        self.setLayout(main_layout)

class SimSelectionPage(QWizardPage):
    simulationSelected = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setTitle("Select Simulation Platform")

        self._simulation = ""
        self._gazebo_version = ""

        self.simulation_field = QLineEdit()
        self.simulation_field.setVisible(False)
        self.gazebo_version_field = QLineEdit()
        self.gazebo_version_field.setVisible(False)
        self.registerField("simulation*", self.simulation_field)
        self.registerField("gazebo_version", self.gazebo_version_field)

        layout = QHBoxLayout()

        # Gazebo section
        gazebo_widget = QWidget()
        gazebo_layout = QVBoxLayout()

        # Fortress
        fortress_widget = QWidget()
        fortress_layout = QVBoxLayout()
        fortress_label = QLabel("Gazebo Fortress")
        fortress_label.setAlignment(Qt.AlignCenter)
        fortress_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        fortress_label.setStyleSheet("color: red;")
        fortress_image_label = QLabel()
        fortress_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "fortress.jpg")
        if os.path.exists(fortress_image_path):
            pixmap = QPixmap(fortress_image_path).scaled(290, 290, Qt.KeepAspectRatio)
            fortress_image_label.setPixmap(pixmap)
        else:
            fortress_image_label.setText("Fortress image not found")
        fortress_image_label.setFixedSize(290, 290)
        fortress_image_label.setAlignment(Qt.AlignCenter)
        self.fortress_button = QPushButton("Select Fortress")
        self.fortress_button.setFont(QFont("Arial", 14))
        self.fortress_button.setFixedHeight(50)
        self.fortress_button.clicked.connect(lambda: self.select_gazebo_version("fortress"))
        fortress_layout.addWidget(fortress_label)
        fortress_layout.addSpacing(10)
        fortress_layout.addWidget(fortress_image_label, alignment=Qt.AlignCenter)
        fortress_layout.addSpacing(10)
        fortress_layout.addWidget(self.fortress_button, alignment=Qt.AlignCenter)
        fortress_layout.addStretch(1)
        fortress_widget.setLayout(fortress_layout)
        gazebo_layout.addWidget(fortress_widget)

        # Horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        gazebo_layout.addWidget(separator)

        # Harmonic
        harmonic_widget = QWidget()
        harmonic_layout = QVBoxLayout()
        harmonic_label = QLabel("Gazebo Harmonic")
        harmonic_label.setAlignment(Qt.AlignCenter)
        harmonic_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        harmonic_label.setStyleSheet("color: red;")
        harmonic_image_label = QLabel()
        harmonic_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "harmonic.jpg")
        if os.path.exists(harmonic_image_path):
            pixmap = QPixmap(harmonic_image_path).scaled(290, 290, Qt.KeepAspectRatio)
            harmonic_image_label.setPixmap(pixmap)
        else:
            harmonic_image_label.setText("Harmonic image not found")
        harmonic_image_label.setFixedSize(290, 290)
        harmonic_image_label.setAlignment(Qt.AlignCenter)
        self.harmonic_button = QPushButton("Select Harmonic")
        self.harmonic_button.setFont(QFont("Arial", 14))
        self.harmonic_button.setFixedHeight(50)
        self.harmonic_button.clicked.connect(lambda: self.select_gazebo_version("harmonic"))
        harmonic_layout.addWidget(harmonic_label)
        harmonic_layout.addSpacing(10)
        harmonic_layout.addWidget(harmonic_image_label, alignment=Qt.AlignCenter)
        harmonic_layout.addSpacing(10)
        harmonic_layout.addWidget(self.harmonic_button, alignment=Qt.AlignCenter)
        harmonic_layout.addStretch(1)
        harmonic_widget.setLayout(harmonic_layout)
        gazebo_layout.addWidget(harmonic_widget)
        gazebo_layout.addStretch(1)
        gazebo_widget.setLayout(gazebo_layout)
        layout.addWidget(gazebo_widget, stretch=1)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider, stretch=0)

        # Isaac Sim section
        isaac_widget = QWidget()
        isaac_layout = QVBoxLayout()
        isaac_layout.addStretch(1)  # Add stretch above for vertical centering
        isaac_label = QLabel("Isaac Sim (Under Development)")
        isaac_label.setAlignment(Qt.AlignCenter)
        isaac_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        isaac_label.setStyleSheet("color: red;")
        isaac_image_label = QLabel()
        isaac_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "isaacsim_gray.jpg")
        if os.path.exists(isaac_image_path):
            pixmap = QPixmap(isaac_image_path).scaled(400, 400, Qt.KeepAspectRatio)
            isaac_image_label.setPixmap(pixmap)
        else:
            isaac_image_label.setText("Isaac Sim image not found")
        isaac_image_label.setFixedSize(400, 400)
        isaac_image_label.setAlignment(Qt.AlignCenter)
        self.isaac_button = QPushButton("Select Isaac Sim")
        self.isaac_button.setFont(QFont("Arial", 14))
        self.isaac_button.setFixedHeight(50)
        self.isaac_button.setEnabled(False)
        isaac_layout.addWidget(isaac_label)
        isaac_layout.addSpacing(10)
        isaac_layout.addWidget(isaac_image_label, alignment=Qt.AlignCenter)
        isaac_layout.addSpacing(10)
        isaac_layout.addWidget(self.isaac_button, alignment=Qt.AlignCenter)
        isaac_layout.addStretch(1)  # Add stretch below for vertical centering
        isaac_widget.setLayout(isaac_layout)
        layout.addWidget(isaac_widget, stretch=1)

        self.setLayout(layout)

        # Apply stylesheets for hover effects
        button_style = """
            QPushButton {
                background-color: #4A90E2;
                color: white;
                padding: 15px;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #6AB0F3;
                transform: scale(1.05);
            }
        """
        self.fortress_button.setStyleSheet(button_style)
        self.harmonic_button.setStyleSheet(button_style)
        self.isaac_button.setStyleSheet("""
            QPushButton {
                background-color: #A9A9A9;
                color: white;
                padding: 15px;
                font-size: 14pt;
            }
        """)

    def select_gazebo_version(self, version):
        self._simulation = "gazebo"
        self._gazebo_version = version
        self.simulation_field.setText("gazebo")
        self.gazebo_version_field.setText(version)
        self.simulationSelected.emit("gazebo", version)
        self.completeChanged.emit()

    def isComplete(self):
        return self._simulation == "gazebo" and self._gazebo_version in ["fortress", "harmonic"]

class WallsDesignPage(QWizardPage):
    def __init__(self, scene):
        super().__init__()
        self.setTitle("Design Walls")

        self.registerField("world_name", self)
        self.registerField("wall_list", self)
        self.world_manager = None
        self.scene = scene
        self.wall_items = {}

        layout = QHBoxLayout()

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        self.create_world_button = QPushButton("Create New World")
        self.create_world_button.clicked.connect(self.create_new_world)
        left_layout.addWidget(self.create_world_button)

        self.load_world_button = QPushButton("Load World")
        self.load_world_button.clicked.connect(self.load_world)
        left_layout.addWidget(self.load_world_button)

        self.world_name_input = QLineEdit()
        self.world_name_input.setPlaceholderText("World Name")
        left_layout.addWidget(self.world_name_input)

        self.wall_list = QListWidget()
        left_layout.addWidget(self.wall_list)

        self.remove_wall_button = QPushButton("Remove Selected Wall")
        self.remove_wall_button.clicked.connect(self.remove_selected_wall)
        left_layout.addWidget(self.remove_wall_button)

        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("Width (m)")
        left_layout.addWidget(self.width_input)

        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("Height (m)")
        left_layout.addWidget(self.height_input)

        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("Color (e.g., Black)")
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

    def initializePage(self):
        self.world_manager = self.wizard().world_manager

    def snap_to_grid(self, point, grid_spacing=10):
        x = round(point.x() / grid_spacing) * grid_spacing
        y = round(point.y() / grid_spacing) * grid_spacing
        return QPointF(x, y)

    def eventFilter(self, obj, event):
        if obj == self.view and self.world_manager:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                if not hasattr(self, 'start_point'):
                    clicked_point = self.view.mapToScene(event.pos())
                    self.start_point = self.snap_to_grid(clicked_point)
                else:
                    clicked_point = self.view.mapToScene(event.pos())
                    end_point = self.snap_to_grid(clicked_point)
                    wall_name = f"wall_{len(self.world_manager.models) + 1}"
                    wall = {
                        "name": wall_name,
                        "type": "wall",
                        "properties": {
                            "start": (self.start_point.x() / 100, self.start_point.y() / 100),
                            "end": (end_point.x() / 100, end_point.y() / 100),
                            "width": float(self.width_input.text() or 0.1),
                            "height": float(self.height_input.text() or 1.0),
                            "color": self.color_input.text() or "Gray"
                        },
                        "status": "new"
                    }
                    self.world_manager.add_model(wall)
                    self.wall_list.addItem(wall_name)
                    line = QGraphicsLineItem(QLineF(self.start_point, end_point))
                    line.setPen(QPen(Qt.black, 2))
                    self.scene.addItem(line)
                    text = QGraphicsTextItem(wall_name)
                    text.setPos((self.start_point + end_point) / 2)
                    self.scene.addItem(text)
                    self.wall_items[wall_name] = (line, text)
                    del self.start_point
                return True
        return super().eventFilter(obj, event)

    def create_new_world(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        world_name = self.world_name_input.text().strip()
        if not world_name:
            QMessageBox.warning(self, "Error", "Please enter a valid world name.")
            return
        try:
            empty_world_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "worlds", "gazebo", self.world_manager.version, "empty_world.sdf")
            print(f"Copying empty world from: {empty_world_path}")
            if not os.path.exists(empty_world_path):
                raise FileNotFoundError(f"Empty world file not found: {empty_world_path}")
            new_world_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "worlds", "gazebo", self.world_manager.version, f"{world_name}.sdf")
            print(f"Creating new world at: {new_world_path}")

            shutil.copyfile(empty_world_path, new_world_path)

            tree = ET.parse(new_world_path)
            root = tree.getroot()
            world_elem = root.find("world")
            if world_elem is not None:
                world_elem.set("name", world_name)
            else:
                raise ValueError("SDF file does not contain a <world> element")
            tree.write(new_world_path, encoding="utf-8", xml_declaration=True)

            self.world_manager.load_world(world_name)

            self.wall_list.clear()
            self.scene.clear()
            grid_spacing = 10
            for x in range(-1000, 1000, grid_spacing):
                self.scene.addLine(x, -1000, x, 1000, QPen(QColor("lightgray")))
            for y in range(-1000, 1000, grid_spacing):
                self.scene.addLine(-1000, y, 1000, y, QPen(QColor("lightgray")))
            self.wall_items = {}
            QMessageBox.information(self, "Success", f"Created and loaded new world: {world_name}")
            self.completeChanged.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create world: {str(e)}")

    def load_world(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        world_name = self.world_name_input.text().strip()
        if not world_name:
            QMessageBox.warning(self, "Error", "Please enter a valid world name.")
            return
        try:
            self.world_manager.load_world(world_name)
            self.wall_list.clear()
            self.wizard().refresh_canvas(self.scene, self.wall_items, {})  # Refresh with all models
            for model in self.world_manager.models:
                if model["type"] == "wall":
                    self.wall_list.addItem(model["name"])
            QMessageBox.information(self, "Success", f"Loaded world: {world_name}")
            self.completeChanged.emit()
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load world: {str(e)}")

    def remove_selected_wall(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        selected = self.wall_list.currentItem()
        if selected:
            wall_name = selected.text()
            if wall_name in self.wall_items:
                line, text = self.wall_items[wall_name]
                self.scene.removeItem(line)
                self.scene.removeItem(text)
                del self.wall_items[wall_name]
            for model in self.world_manager.models:
                if model["name"] == wall_name:
                    model["status"] = "removed"
                    break
            self.wall_list.takeItem(self.wall_list.row(selected))
            for item in self.scene.items():
                if isinstance(item, QGraphicsLineItem):
                    if item.pen().color() != QColor("lightgray"):
                        print(f"Remaining wall line: {item.line()}")

    def apply_changes(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        try:
            self.world_manager.apply_changes()
            QMessageBox.information(self, "Success", "Changes applied successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {str(e)}")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None

class StaticObstaclesPage(QWizardPage):
    def __init__(self, scene):
        super().__init__()
        self.setTitle("Add Static Obstacles")
        self.world_manager = None
        self.scene = scene
        self.obstacle_items = {}

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
        self.wizard().refresh_canvas(self.scene, {}, self.obstacle_items)  # Refresh with all models
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
                    half_width_pixels = (W / 2) * 100
                    half_length_pixels = (L / 2) * 100
                    rounded_half_width_pixels = round(half_width_pixels / 10) * 10
                    rounded_half_length_pixels = round(half_length_pixels / 10) * 10
                    rect_pixels = QRectF(center.x() - rounded_half_width_pixels, center.y() - rounded_half_length_pixels,
                                         2 * rounded_half_width_pixels, 2 * rounded_half_length_pixels)
                    item = QGraphicsRectItem(rect_pixels)
                    size_m = (W, L, H)
                    position_z = H / 2
                elif obstacle_type == "cylinder":
                    R = float(self.radius_input.text() or 0.5)
                    H = float(self.height_input.text() or 1.0)
                    radius_pixels = R * 100
                    rect_pixels = QRectF(center.x() - radius_pixels, center.y() - radius_pixels, 2 * radius_pixels, 2 * radius_pixels)
                    item = QGraphicsEllipseItem(rect_pixels)
                    size_m = (R, H)
                    position_z = H / 2
                elif obstacle_type == "sphere":
                    R = float(self.radius_input.text() or 0.5)
                    radius_pixels = R * 100
                    rect_pixels = QRectF(center.x() - radius_pixels, center.y() - radius_pixels, 2 * radius_pixels, 2 * radius_pixels)
                    item = QGraphicsEllipseItem(rect_pixels)
                    size_m = (R,)
                    position_z = R
                color = self.color_input.text() or "Gray"
                obstacle_name = f"{obstacle_type}_{len(self.world_manager.models) + 1}"
                x_m = center.x() / 100
                y_m = center.y() / 100
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
                item.setPen(QPen(Qt.black, 2))
                item.setBrush(QColor("lightgray"))
                self.scene.addItem(item)
                text = QGraphicsTextItem(obstacle_name)
                text.setPos(center)
                self.scene.addItem(text)
                self.obstacle_items[obstacle_name] = (item, text)
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
            if obstacle_name in self.obstacle_items:
                item, text = self.obstacle_items[obstacle_name]
                self.scene.removeItem(item)
                self.scene.removeItem(text)
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
        self.path_items = {}  # obstacle_name: list of graphics items
        self.points = []
        self.clicking_enabled = False

        self.motion_type_combo.currentTextChanged.connect(self.update_motion_type)
        self.obstacle_list.itemClicked.connect(self.select_obstacle)

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")
            return
        static_page = self.wizard().page(3)  # Assuming StaticObstaclesPage is the 4th page (index 3)
        self.obstacle_list.clear()
        for i in range(static_page.obstacle_list.count()):
            self.obstacle_list.addItem(static_page.obstacle_list.item(i).text())

    def update_motion_type(self, text):
        self.current_motion_type = text.lower()
        self.clear_path()
        self.points = []
        self.semi_major_input.setEnabled(self.current_motion_type == "elliptical")
        self.semi_minor_input.setEnabled(self.current_motion_type == "elliptical")

    def select_obstacle(self, item):
        self.current_obstacle = item.text()
        self.clear_path()
        self.points = []
        self.clicking_enabled = False

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
        if self.current_obstacle in self.path_items:
            for item in self.path_items[self.current_obstacle]:
                self.scene.removeItem(item)
            del self.path_items[self.current_obstacle]

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
            center = QPointF(center_m[0] * 100, center_m[1] * 100)
            direction = self.points[0] - center
            angle = math.degrees(math.atan2(direction.y(), direction.x()))
            ellipse = QGraphicsEllipseItem(QRectF(-semi_major * 100, -semi_minor * 100, 2 * semi_major * 100, 2 * semi_minor * 100))
            ellipse.setPos(center)
            ellipse.setRotation(angle)
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
        self.path_items[self.current_obstacle] = items

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
            path_m = [(p.x() / 100, p.y() / 100) for p in self.points]
            motion["path"] = path_m
        elif self.current_motion_type == "elliptical":
            semi_major = float(self.semi_major_input.text() or 1.0)
            semi_minor = float(self.semi_minor_input.text() or 0.5)
            center_m = model["properties"]["position"][:2]
            center = QPointF(center_m[0] * 100, center_m[1] * 100)
            direction = self.points[0] - center
            angle = math.atan2(direction.y(), direction.x())
            motion["semi_major"] = semi_major
            motion["semi_minor"] = semi_minor
            motion["angle"] = angle
        model["properties"]["motion"] = motion
        if "status" in model:
            model["status"] = "updated"
        else:
            model["status"] = "new"

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

class ComingSoonPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Coming Soon")
        self.world_manager = None

        layout = QVBoxLayout()
        layout.addStretch(1)  # Stretch above for vertical centering

        # Container for images
        images_widget = QWidget()
        images_layout = QHBoxLayout()
        images_layout.setSpacing(20)  # Space between image widgets

        # Future 1
        feature1_widget = QWidget()
        feature1_layout = QVBoxLayout()
        feature1_label = QLabel("Future 1")
        feature1_label.setAlignment(Qt.AlignCenter)
        feature1_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        feature1_label.setStyleSheet("color: red;")
        feature1_image_label = QLabel()
        feature1_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "future", "future_1.jpg")
        if os.path.exists(feature1_image_path):
            pixmap = QPixmap(feature1_image_path).scaled(350, 350, Qt.KeepAspectRatio)
            feature1_image_label.setPixmap(pixmap)
        else:
            feature1_image_label.setText("Future 1 image not found")
        feature1_image_label.setFixedSize(350, 350)
        feature1_image_label.setAlignment(Qt.AlignCenter)
        feature1_layout.addWidget(feature1_image_label, alignment=Qt.AlignCenter)
        feature1_layout.addSpacing(10)  # 10px spacing between image and label
        feature1_layout.addWidget(feature1_label)
        feature1_layout.addStretch(1)
        feature1_widget.setLayout(feature1_layout)
        images_layout.addWidget(feature1_widget)

        # Future 2
        feature2_widget = QWidget()
        feature2_layout = QVBoxLayout()
        feature2_label = QLabel("Future 2")
        feature2_label.setAlignment(Qt.AlignCenter)
        feature2_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        feature2_label.setStyleSheet("color: red;")
        feature2_image_label = QLabel()
        feature2_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "future", "future_2.jpg")
        if os.path.exists(feature2_image_path):
            pixmap = QPixmap(feature2_image_path).scaled(350, 350, Qt.KeepAspectRatio)
            feature2_image_label.setPixmap(pixmap)
        else:
            feature2_image_label.setText("Future 2 image not found")
        feature2_image_label.setFixedSize(350, 350)
        feature2_image_label.setAlignment(Qt.AlignCenter)
        feature2_layout.addWidget(feature2_image_label, alignment=Qt.AlignCenter)
        feature2_layout.addSpacing(10)  # 10px spacing between image and label
        feature2_layout.addWidget(feature2_label)
        feature2_layout.addStretch(1)
        feature2_widget.setLayout(feature2_layout)
        images_layout.addWidget(feature2_widget)

        # Future 3
        feature3_widget = QWidget()
        feature3_layout = QVBoxLayout()
        feature3_label = QLabel("Future 3")
        feature3_label.setAlignment(Qt.AlignCenter)
        feature3_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        feature3_label.setStyleSheet("color: red;")
        feature3_image_label = QLabel()
        feature3_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "future", "future_3.jpg")
        if os.path.exists(feature3_image_path):
            pixmap = QPixmap(feature3_image_path).scaled(350, 350, Qt.KeepAspectRatio)
            feature3_image_label.setPixmap(pixmap)
        else:
            feature3_image_label.setText("Future 3 image not found")
        feature3_image_label.setFixedSize(350, 350)
        feature3_image_label.setAlignment(Qt.AlignCenter)
        feature3_layout.addWidget(feature3_image_label, alignment=Qt.AlignCenter)
        feature3_layout.addSpacing(10)  # 10px spacing between image and label
        feature3_layout.addWidget(feature3_label)
        feature3_layout.addStretch(1)
        feature3_widget.setLayout(feature3_layout)
        images_layout.addWidget(feature3_widget)

        images_widget.setLayout(images_layout)
        layout.addWidget(images_widget, alignment=Qt.AlignCenter)
        layout.addStretch(1)  # Stretch below for vertical centering
        self.setLayout(layout)

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None
class WorldManager:
    def __init__(self, simulation, version):
        self.simulation = simulation
        self.version = version
        self.sdf_version = "1.8" if version == "fortress" else "1.9"
        self.world_path = None
        self.world_name = None
        self.models = []
        self.sdf_tree = None
        self.sdf_root = None
        self.process = None
        self.script_process = None
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def create_new_world(self, world_name):
        self.world_name = world_name
        empty_world_path = os.path.join(self.base_dir, "worlds", "gazebo", self.version, "empty_world.sdf")
        print(f"Looking for empty world at: {empty_world_path}")
        if not os.path.exists(empty_world_path):
            raise FileNotFoundError(f"Empty world file not found: {empty_world_path}")

        if self.version == "fortress":
            cmd = ["ign", "gazebo", empty_world_path]
        else:
            cmd = ["gz", "sim", empty_world_path]
        self.process = subprocess.Popen(cmd)
        self.world_path = os.path.join(self.base_dir, "worlds", "gazebo", self.version, f"{world_name}.sdf")
        print(f"Creating world at: {self.world_path}")
        self.models = []
        self.sdf_tree = ET.parse(empty_world_path)
        self.sdf_root = self.sdf_tree.getroot()
        self.world_name = self.sdf_root.find("world").get("name")

    def load_world(self, world_name):
        self.world_name = world_name
        self.world_path = os.path.join(self.base_dir, "worlds", "gazebo", self.version, f"{world_name}.sdf")
        print(f"Loading world at: {self.world_path}")
        if not os.path.exists(self.world_path):
            raise FileNotFoundError(f"World file not found: {self.world_path}")

        if self.version == "fortress":
            cmd = ["ign", "gazebo", self.world_path]
        else:
            cmd = ["gz", "sim", self.world_path]
        self.process = subprocess.Popen(cmd)

        self.sdf_tree = ET.parse(self.world_path)
        self.sdf_root = self.sdf_tree.getroot()
        self.world_name = self.sdf_root.find("world").get("name")
        self.models = []

        for model_elem in self.sdf_root.findall(".//model"):
            name = model_elem.get("name")
            type_elem = model_elem.find("type")
            model_type = type_elem.text if type_elem is not None else None

            if model_type is None:
                geometry = model_elem.find(".//geometry")
                if geometry is not None:
                    if geometry.find("box") is not None:
                        model_type = "wall" if "wall" in name else "box"
                    elif geometry.find("cylinder") is not None:
                        model_type = "cylinder"
                    elif geometry.find("sphere") is not None:
                        model_type = "sphere"
                    else:
                        model_type = "unknown"

            properties = {}
            pose_str = model_elem.find("pose").text
            pose = [float(x) for x in pose_str.split()]
            x, y, z, _, _, _ = pose  # Ignore orientation for obstacles

            geometry = model_elem.find(".//geometry")
            if geometry:
                if model_type in ["wall", "box"]:
                    size_str = geometry.find("box/size").text
                    size = [float(s) for s in size_str.split()]
                    if model_type == "wall":
                        length, width, height = size
                        yaw = pose[5]
                        dx = (length / 2) * math.cos(yaw)
                        dy = (length / 2) * math.sin(yaw)
                        start_x = x - dx
                        start_y = y - dy
                        end_x = x + dx
                        end_y = y + dy
                        properties = {
                            "start": (start_x, start_y),
                            "end": (end_x, end_y),
                            "width": width,
                            "height": height,
                            "color": "Gray"
                        }
                    else:
                        properties = {
                            "position": (x, y, z),
                            "size": size,
                            "color": "Gray"
                        }
                elif model_type == "cylinder":
                    radius = float(geometry.find("cylinder/radius").text)
                    length = float(geometry.find("cylinder/length").text)
                    properties = {
                        "position": (x, y, z),
                        "size": (radius, length),
                        "color": "Gray"
                    }
                elif model_type == "sphere":
                    radius = float(geometry.find("sphere/radius").text)
                    properties = {
                        "position": (x, y, z),
                        "size": (radius,),
                        "color": "Gray"
                    }

            self.models.append({
                "name": name,
                "type": model_type,
                "properties": properties,
                "status": ""
            })

    def add_model(self, model):
        self.models.append(model)

    def apply_changes(self):
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("Gazebo simulation is not running. Please create or load a world first.")

        time.sleep(2)

        prefix = "ign" if self.version == "fortress" else "gz"
        reqtype_prefix = "ignition.msgs" if self.version == "fortress" else "gz.msgs"

        for model in self.models[:]:  # Copy to avoid modification during iteration
            if model["status"] == "updated":
                # Remove the model first
                request_str = f'name: "{model["name"]}", type: 2'
                cmd = [prefix, "service", "-s", f"/world/{self.world_name}/remove",
                       "--reqtype", f"{reqtype_prefix}.Entity",
                       "--reptype", f"{reqtype_prefix}.Boolean",
                       "--timeout", "3000",
                       "--req", request_str]
                print("Executing command:", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True, text=True)
                print("Result stdout:", result.stdout)
                print("Result stderr:", result.stderr)
                if result.returncode != 0:
                    print(f"Warning: Failed to remove model {model['name']} for update: {result.stderr}")
                    continue
                for elem in self.sdf_root.findall(f".//model[@name='{model['name']}']"):
                    self.sdf_root.find("world").remove(elem)
                self.save_sdf(self.world_path)
                # Change status to new for re-adding
                model["status"] = "new"

            if model["status"] == "new":
                sdf_snippet_service = self.generate_model_sdf(model, for_service=True)
                sdf_escaped = sdf_snippet_service.replace('"', '\\"')
                sdf_compact = ' '.join(sdf_escaped.split())
                request_str = f'sdf: "{sdf_compact}"'
                cmd = [prefix, "service", "-s", f"/world/{self.world_name}/create",
                       "--reqtype", f"{reqtype_prefix}.EntityFactory",
                       "--reptype", f"{reqtype_prefix}.Boolean",
                       "--timeout", "3000",
                       "--req", request_str]
                print("Executing command:", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True, text=True)
                print("Result stdout:", result.stdout)
                print("Result stderr:", result.stderr)
                if result.returncode != 0 or "data: true" not in result.stdout:
                    print(f"Warning: Failed to add model {model['name']}: {result.stderr}")
                    continue
                time.sleep(1)
                sdf_snippet_file = self.generate_model_sdf(model, for_service=False)
                model_elem = ET.fromstring(sdf_snippet_file)
                self.sdf_root.find("world").append(model_elem)
                self.save_sdf(self.world_path)
            elif model["status"] == "removed":
                request_str = f'name: "{model["name"]}", type: 2'
                cmd = [prefix, "service", "-s", f"/world/{self.world_name}/remove",
                       "--reqtype", f"{reqtype_prefix}.Entity",
                       "--reptype", f"{reqtype_prefix}.Boolean",
                       "--timeout", "3000",
                       "--req", request_str]
                print("Executing command:", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True, text=True)
                print("Result stdout:", result.stdout)
                print("Result stderr:", result.stderr)
                if result.returncode != 0:
                    print(f"Warning: Failed to remove model {model['name']}: {result.stderr}")
                    continue
                for elem in self.sdf_root.findall(f".//model[@name='{model['name']}']"):
                    self.sdf_root.find("world").remove(elem)
                self.save_sdf(self.world_path)

        # Generate and run motion script if there are dynamic models
        dynamic_models = [m for m in self.models if "motion" in m["properties"]]
        if dynamic_models:
            move_code_dir = os.path.join(self.base_dir, "worlds", "gazebo", self.version, "move_code")
            os.makedirs(move_code_dir, exist_ok=True)
            script_path = os.path.join(move_code_dir, f"{self.world_name}_moveObstacles.py")
            with open(script_path, 'w') as f:
                f.write('#!/usr/bin/env python3\n')
                f.write('import subprocess\n')
                f.write('import time\n')
                f.write('import random\n')
                f.write('import math\n\n')
                f.write(f'prefix = "{"ign" if self.version == "fortress" else "gz"}\"\n')
                f.write(f'reqtype_prefix = "{"ignition.msgs" if self.version == "fortress" else "gz.msgs"}\"\n')
                f.write(f'world_name = "{self.world_name}"\n\n')
                f.write('def set_pose(model_name, x, y, z):\n')
                f.write('    request_str = f\'name: "{model_name}", position {{ x: {x} y: {y} z: {z} }}, orientation {{ w: 1 }}\'\n')
                f.write('    cmd = [prefix, "service", "-s", f"/world/{world_name}/set_pose", "--reqtype", f"{reqtype_prefix}.Pose", "--reptype", f"{reqtype_prefix}.Boolean", "--timeout", "500", "--req", request_str]\n')
                f.write('    result = subprocess.run(cmd, capture_output=True, text=True)\n')
                f.write('    if result.returncode != 0:\n')
                f.write('        print(f"Failed to set pose for {model_name}: {result.stderr}")\n')
                f.write('        return False\n')
                f.write('    return True\n\n')
                f.write('motions = {}\nstates = {}\n')
                for m in dynamic_models:
                    motion = m["properties"]["motion"]
                    z = m["properties"]["position"][2]
                    state = {}
                    if motion["type"] == "linear":
                        start, end = motion["path"]
                        state = {'current_pos': list(start), 'direction': 1, 'start': list(start), 'end': list(end), 'z': z}
                    elif motion["type"] == "elliptical":
                        state = {'theta': 0.0, 'center': list(m["properties"]["position"][:2]), 'semi_major': motion["semi_major"], 'semi_minor': motion["semi_minor"], 'angle': motion["angle"], 'z': z}
                    elif motion["type"] == "polygon":
                        state = {'current_segment': 0, 't': 0.0, 'path': [list(p) for p in motion["path"]], 'z': z}
                    f.write(f'motions["{m["name"]}"] = {motion}\n')
                    f.write(f'states["{m["name"]}"] = {state}\n')
                f.write('\ndt = 0.005\nwhile True:\n')
                f.write('    try:\n')
                f.write('        for model_name, motion in motions.items():\n')
                f.write('            state = states[model_name]\n')
                f.write('            velocity = random.gauss(motion["velocity"], motion["std"])\n')
                f.write('            delta = velocity * dt\n')
                f.write('            if motion["type"] == "linear":\n')
                f.write('                start = state["start"]\n')
                f.write('                end = state["end"]\n')
                f.write('                dx = end[0] - start[0]\n')
                f.write('                dy = end[1] - start[1]\n')
                f.write('                length = math.sqrt(dx**2 + dy**2)\n')
                f.write('                if length < 0.001: continue\n')  # Skip if path is too short
                f.write('                unit_x = dx / length\n')
                f.write('                unit_y = dy / length\n')
                f.write('                new_x = state["current_pos"][0] + delta * state["direction"] * unit_x\n')
                f.write('                new_y = state["current_pos"][1] + delta * state["direction"] * unit_y\n')
                f.write('                dist_to_end = math.hypot(new_x - end[0], new_y - end[1])\n')
                f.write('                dist_to_start = math.hypot(new_x - start[0], new_y - start[1])\n')
                f.write('                if state["direction"] > 0 and dist_to_end < 0.01:\n')
                f.write('                    new_x = end[0]\n')
                f.write('                    new_y = end[1]\n')
                f.write('                    state["direction"] = -state["direction"]\n')
                f.write('                elif state["direction"] < 0 and dist_to_start < 0.01:\n')
                f.write('                    new_x = start[0]\n')
                f.write('                    new_y = start[1]\n')
                f.write('                    state["direction"] = -state["direction"]\n')
                f.write('                state["current_pos"] = [new_x, new_y]\n')
                f.write('                if not set_pose(model_name, new_x, new_y, state["z"]):\n')
                f.write('                    print(f"Stopping script as set_pose failed for {model_name}")\n')
                f.write('                    exit(1)\n')
                f.write('            elif motion["type"] == "elliptical":\n')
                f.write('                delta_theta = velocity / (2 * math.pi * motion["semi_major"]) * 2 * math.pi * dt\n')
                f.write('                state["theta"] += delta_theta\n')
                f.write('                theta = state["theta"]\n')
                f.write('                x = state["center"][0] + motion["semi_major"] * math.cos(theta) * math.cos(motion["angle"]) - motion["semi_minor"] * math.sin(theta) * math.sin(motion["angle"])\n')
                f.write('                y = state["center"][1] + motion["semi_major"] * math.cos(theta) * math.sin(motion["angle"]) + motion["semi_minor"] * math.sin(theta) * math.cos(motion["angle"])\n')
                f.write('                if not set_pose(model_name, x, y, state["z"]):\n')
                f.write('                    print(f"Stopping script as set_pose failed for {model_name}")\n')
                f.write('                    exit(1)\n')
                f.write('            elif motion["type"] == "polygon":\n')
                f.write('                path = state["path"]\n')
                f.write('                start = path[state["current_segment"]]\n')
                f.write('                end = path[(state["current_segment"] + 1) % len(path)]\n')
                f.write('                dx = end[0] - start[0]\n')
                f.write('                dy = end[1] - start[1]\n')
                f.write('                length = math.sqrt(dx**2 + dy**2)\n')
                f.write('                if length < 0.001: continue\n')  # Skip if segment is too short
                f.write('                state["t"] += delta / length\n')
                f.write('                if state["t"] >= 1:\n')
                f.write('                    state["current_segment"] = (state["current_segment"] + 1) % len(path)\n')
                f.write('                    state["t"] = max(0, state["t"] - 1)\n')
                f.write('                t = min(1, state["t"])\n')
                f.write('                x = start[0] + t * dx\n')
                f.write('                y = start[1] + t * dy\n')
                f.write('                if not set_pose(model_name, x, y, state["z"]):\n')
                f.write('                    print(f"Stopping script as set_pose failed for {model_name}")\n')
                f.write('                    exit(1)\n')
                f.write('        time.sleep(dt)\n')
                f.write('    except KeyboardInterrupt:\n')
                f.write('        print("Motion script interrupted")\n')
                f.write('        exit(0)\n')
            os.chmod(script_path, 0o755)
            # Terminate any existing script process before starting a new one
            if self.script_process and self.script_process.poll() is None:
                self.script_process.terminate()
                try:
                    self.script_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.script_process.kill()
            # Run the script and store the process
            self.script_process = subprocess.Popen(['python3', script_path])

        self.models = [m for m in self.models if m["status"] != "removed"]
        for model in self.models:
            model["status"] = ""

    def cleanup(self):
        import signal
        print("Starting cleanup of WorldManager")
        
        # Save the current world state before closing
        if self.sdf_tree and self.world_path:
            try:
                self.save_sdf(self.world_path)
                print(f"Saved world state to {self.world_path}")
            except Exception as e:
                print(f"Warning: Failed to save world state: {str(e)}")

        # Terminate the motion script process
        if self.script_process and self.script_process.poll() is None:
            print(f"Terminating motion script process (PID: {self.script_process.pid})")
            try:
                # Send SIGINT first for graceful shutdown
                self.script_process.send_signal(signal.SIGINT)
                self.script_process.wait(timeout=2)
                print("Motion script process terminated gracefully")
            except subprocess.TimeoutExpired:
                print("Motion script process did not terminate gracefully, sending SIGTERM")
                self.script_process.terminate()
                try:
                    self.script_process.wait(timeout=2)
                    print("Motion script process terminated with SIGTERM")
                except subprocess.TimeoutExpired:
                    print("Motion script process still running, sending SIGKILL")
                    self.script_process.kill()
                    self.script_process.wait(timeout=2)
                    print("Motion script process killed")
            except Exception as e:
                print(f"Error terminating motion script process: {str(e)}")
            self.script_process = None

        # Terminate the Gazebo process
        if self.process and self.process.poll() is None:
            print(f"Terminating Gazebo process (PID: {self.process.pid})")
            try:
                # Send SIGINT first for graceful shutdown
                self.process.send_signal(signal.SIGINT)
                self.process.wait(timeout=2)
                print("Gazebo process terminated gracefully")
            except subprocess.TimeoutExpired:
                print("Gazebo process did not terminate gracefully, sending SIGTERM")
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                    print("Gazebo process terminated with SIGTERM")
                except subprocess.TimeoutExpired:
                    print("Gazebo process still running, sending SIGKILL")
                    self.process.kill()
                    self.process.wait(timeout=2)
                    print("Gazebo process killed")
            except Exception as e:
                print(f"Error terminating Gazebo process: {str(e)}")
            self.process = None
        print("Cleanup completed")

    def generate_model_sdf(self, model, for_service=False):
        model_type = model["type"]
        props = model["properties"]
        color_rgb = get_color(props["color"])

        if model_type == "wall":
            start = props["start"]
            end = props["end"]
            center_x = (start[0] + end[0]) / 2
            center_y = (start[1] + end[1]) / 2
            z = props["height"] / 2
            length = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
            yaw = math.atan2(end[1] - start[1], end[0] - start[0])
            pose = f"{center_x:.6f} {center_y:.6f} {z:.6f} 0 0 {yaw:.6f}"
            size = (length, props["width"], props["height"])
            size_str = f"{size[0]:.6f} {size[1]:.6f} {size[2]:.6f}"
        else:
            x, y, z = props["position"]
            pose = f"{x:.6f} {y:.6f} {z:.6f} 0 0 0"
            size = props["size"]
            if model_type == "box":
                size_str = f"{size[0]:.6f} {size[1]:.6f} {size[2]:.6f}"
            elif model_type == "cylinder":
                size_str = f"{size[0]:.6f} {size[1]:.6f}"
            elif model_type == "sphere":
                size_str = f"{size[0]:.6f}"

        static_str = "false" if "motion" in model["properties"] else "true"
        sdf = f"""<model name='{model["name"]}'>
            <static>{static_str}</static>
            <type>{model_type}</type>
            <pose>{pose}</pose>
            <link name='link'>
                <collision name='collision'>
                    <geometry>"""
        if model_type in ["wall", "box"]:
            sdf += f"""<box><size>{size_str}</size></box>"""
        elif model_type == "cylinder":
            sdf += f"""<cylinder><radius>{size[0]:.6f}</radius><length>{size[1]:.6f}</length></cylinder>"""
        elif model_type == "sphere":
            sdf += f"""<sphere><radius>{size[0]:.6f}</radius></sphere>"""
        sdf += f"""</geometry>
                </collision>
                <visual name='visual'>
                    <geometry>"""
        if model_type in ["wall", "box"]:
            sdf += f"""<box><size>{size_str}</size></box>"""
        elif model_type == "cylinder":
            sdf += f"""<cylinder><radius>{size[0]:.6f}</radius><length>{size[1]:.6f}</length></cylinder>"""
        elif model_type == "sphere":
            sdf += f"""<sphere><radius>{size[0]:.6f}</radius></sphere>"""
        sdf += f"""</geometry>
                    <material>
                        <diffuse>{color_rgb[0]} {color_rgb[1]} {color_rgb[2]} 1</diffuse>
                    </material>
                </visual>
            </link>
        </model>"""

        if for_service:
            sdf = f"""<sdf version='{self.sdf_version}'>{sdf}</sdf>"""
        return sdf

    def save_sdf(self, path):
        if self.sdf_tree:
            self.sdf_tree.write(path, encoding="utf-8", xml_declaration=True)

class DynamicWorldWizard(QWizard):
    def __init__(self):
        print("Entering DynamicWorldWizard.__init__")
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Dynamic World Generator Wizard (V1)")
        self.resize(1500, 900)
        self.setMinimumWidth(800)  # Set minimum window width to allow narrower resizing
        print("Window flags and size set")

        self.world_manager = None
        self.scene = QGraphicsScene()

        self.nav_list = QListWidget()
        self.nav_list.addItems(["Welcome", "Select Simulation", "Design Walls", "Add Static Obstacles",
                                "Add Dynamic Obstacles", "Coming Soon"])
        self.nav_list.setFont(QFont("Arial", 14, QFont.Bold))  # Default font size
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #4A90E2;
                color: #FFFFFF;
            }
            QListWidget::item:hover {
                background-color: #666666;
            }
        """)

        self.nav_list.setCurrentRow(0)
        self.nav_list.itemClicked.connect(self.navigate_to_page)
        print("Navigation list initialized")

        self.addPage(WelcomePage())
        print("Added WelcomePage")
        sim_selection_page = SimSelectionPage()
        self.addPage(sim_selection_page)
        print("Added SimSelectionPage")
        self.walls_page = WallsDesignPage(self.scene)
        self.addPage(self.walls_page)
        print("Added WallsDesignPage")
        self.static_obstacles_page = StaticObstaclesPage(self.scene)
        self.addPage(self.static_obstacles_page)
        print("Added StaticObstaclesPage")
        self.dynamic_obstacles_page = DynamicObstaclesPage(self.scene)
        self.addPage(self.dynamic_obstacles_page)
        print("Added DynamicObstaclesPage")
        self.addPage(ComingSoonPage())
        print("Added ComingSoonPage")


        sim_selection_page.simulationSelected.connect(self.initialize_world_manager)
        print("Connected simulationSelected signal")

        side_widget = QWidget()
        side_layout = QVBoxLayout()
        side_layout.addWidget(self.nav_list)
        side_layout.addStretch()
        side_widget.setLayout(side_layout)
        self.setSideWidget(side_widget)
        print("Side widget set")

        self.currentIdChanged.connect(self.update_navigation)
        print("Connected currentIdChanged signal")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        window_width = max(self.width(), 800)  # Respect minimum window width
        nav_width = max(min(int(window_width * 0.2), 300), 200)  # 20% of window width, clamped between 200-300px
        self.nav_list.setFixedWidth(nav_width)
        # Scale font size: 12pt at 200px, 16pt at 300px
        font_size = 12 + (nav_width - 200) * (16 - 12) / (300 - 200)
        self.nav_list.setFont(QFont("Arial", int(font_size), QFont.Bold))
        content_width = window_width - nav_width  # Width for canvas + left panel
        canvas_width = int(content_width * 0.7)  # 70% for canvas
        left_width = content_width - canvas_width  # Remaining for left panel
        
        # Update WallsDesignPage
        if hasattr(self, 'walls_page'):
            self.walls_page.view.setFixedWidth(canvas_width)
            for widget in self.walls_page.findChildren(QWidget):
                if widget.layout() and isinstance(widget.layout(), QVBoxLayout):
                    widget.setMaximumWidth(left_width)
                    widget.setMinimumWidth(150)  # Ensure usability
        
        # Update StaticObstaclesPage
        if hasattr(self, 'static_obstacles_page'):
            self.static_obstacles_page.view.setFixedWidth(canvas_width)
            for widget in self.static_obstacles_page.findChildren(QWidget):
                if widget.layout() and isinstance(widget.layout(), QVBoxLayout):
                    widget.setMaximumWidth(left_width)
                    widget.setMinimumWidth(150)
        
        # Update DynamicObstaclesPage
        if hasattr(self, 'dynamic_obstacles_page'):
            self.dynamic_obstacles_page.view.setFixedWidth(canvas_width)
            for widget in self.dynamic_obstacles_page.findChildren(QWidget):
                if widget.layout() and isinstance(widget.layout(), QVBoxLayout):
                    widget.setMaximumWidth(left_width)
                    widget.setMinimumWidth(150)

    def refresh_canvas(self, scene, wall_items, obstacle_items):
        scene.clear()
        grid_spacing = 10
        for x in range(-1000, 1000, grid_spacing):
            scene.addLine(x, -1000, x, 1000, QPen(QColor("lightgray")))
        for y in range(-1000, 1000, grid_spacing):
            scene.addLine(-1000, y, 1000, y, QPen(QColor("lightgray")))
        wall_items.clear()
        obstacle_items.clear()
        if self.world_manager:
            for model in self.world_manager.models:
                if model["type"] == "wall":
                    start = QPointF(model["properties"]["start"][0] * 100, model["properties"]["start"][1] * 100)
                    end = QPointF(model["properties"]["end"][0] * 100, model["properties"]["end"][1] * 100)
                    line = QGraphicsLineItem(QLineF(start, end))
                    line.setPen(QPen(Qt.black, 2))
                    scene.addItem(line)
                    text = QGraphicsTextItem(model["name"])
                    text.setPos((start + end) / 2)
                    scene.addItem(text)
                    wall_items[model["name"]] = (line, text)
                elif model["type"] in ["box", "cylinder", "sphere"]:
                    position = model["properties"]["position"]
                    size = model["properties"]["size"]
                    center = QPointF(position[0] * 100, position[1] * 100)
                    if model["type"] == "box":
                        W, L, _ = size
                        half_width_pixels = (W / 2) * 100
                        half_length_pixels = (L / 2) * 100
                        rounded_half_width_pixels = round(half_width_pixels / 10) * 10
                        rounded_half_length_pixels = round(half_length_pixels / 10) * 10
                        rect_pixels = QRectF(center.x() - rounded_half_width_pixels, center.y() - rounded_half_length_pixels,
                                            2 * rounded_half_width_pixels, 2 * rounded_half_length_pixels)
                        item = QGraphicsRectItem(rect_pixels)
                    else:  # cylinder or sphere
                        R = size[0]
                        radius_pixels = R * 100
                        rect_pixels = QRectF(center.x() - radius_pixels, center.y() - radius_pixels, 2 * radius_pixels, 2 * radius_pixels)
                        item = QGraphicsEllipseItem(rect_pixels)
                    item.setPen(QPen(Qt.black, 2))
                    item.setBrush(QColor("lightgray"))
                    scene.addItem(item)
                    text = QGraphicsTextItem(model["name"])
                    text.setPos(center)
                    scene.addItem(text)
                    obstacle_items[model["name"]] = (item, text)

    def closeEvent(self, event):
        print("Closing DynamicWorldWizard")
        if self.world_manager:
            self.world_manager.cleanup()
        event.accept()

    def initialize_world_manager(self, sim_type, version):
        print(f"Initializing WorldManager with sim_type={sim_type}, version={version}")
        if sim_type == "gazebo" and version in ["fortress", "harmonic"]:
            self.world_manager = WorldManager(sim_type, version)
        else:
            self.world_manager = None

    def update_navigation(self, page_id):
        print(f"Updating navigation to page_id={page_id}")
        page_index = self.pageIds().index(page_id)
        if self.nav_list.currentRow() != page_index:
            self.nav_list.setCurrentRow(page_index)

    def navigate_to_page(self, item):
        print(f"Navigating to page: {item.text()}")
        page_names = ["Welcome", "Select Simulation", "Design Walls", "Add Static Obstacles",
                    "Add Dynamic Obstacles", "Coming Soon"]
        target_index = page_names.index(item.text())
        current_index = self.pageIds().index(self.currentId())

        while current_index < target_index:
            if self.currentPage().isComplete():
                self.next()
                current_index += 1
            else:
                break
        while current_index > target_index:
            self.back()
            current_index -= 1

if __name__ == "__main__":
    print("Entering main block")
    app = QApplication(sys.argv)
    print("QApplication created")
    wizard = DynamicWorldWizard()
    print("DynamicWorldWizard instance created")
    wizard.show()
    print("Wizard shown")
    sys.exit(app.exec_())