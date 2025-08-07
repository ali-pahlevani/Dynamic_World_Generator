#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
import math
from xml.etree import ElementTree as ET
from PyQt5.QtWidgets import QWizard, QWizardPage, QListWidget, QVBoxLayout, QHBoxLayout, QWidget, QApplication, QPushButton, QLabel, QLineEdit, QComboBox, QGraphicsView, QGraphicsScene, QMessageBox, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QFrame
from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF, QEvent, pyqtSignal, pyqtProperty
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
        self.scale_label = QLabel("1 pixel = 0.01 m", self)
        self.scale_label.setStyleSheet("background: transparent; color: black;")
        self.scale_label.setGeometry(10, self.height() - 30, 100, 20)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale_label.move(10, self.height() - 30)

    def wheelEvent(self, event):
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(zoom_factor, zoom_factor)

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to the Dynamic World Generator Wizard!")

        layout = QVBoxLayout()

        title_label = QLabel("Welcome to the Dynamic World Generator Wizard!")
        title_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        layout.addWidget(title_label)

        gif_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "welcome.gif")
        print(f"Looking for GIF at: {gif_path}")

        gif_label = QLabel()
        movie = QMovie(gif_path)
        if movie.isValid():
            gif_label.setMovie(movie)
            movie.start()
        else:
            gif_label.setText(f"Preview GIF not found at {gif_path}")
        layout.addWidget(gif_label)

        self.setLayout(layout)

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
        fortress_image_label = QLabel()
        fortress_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "fortress.jpg")
        if os.path.exists(fortress_image_path):
            pixmap = QPixmap(fortress_image_path).scaled(400, 400, Qt.KeepAspectRatio)
            fortress_image_label.setPixmap(pixmap)
        else:
            fortress_image_label.setText("Fortress image not found")
        fortress_image_label.setFixedSize(400, 400)
        self.fortress_button = QPushButton("Select Fortress")
        self.fortress_button.clicked.connect(lambda: self.select_gazebo_version("fortress"))
        fortress_layout.addWidget(fortress_label)
        fortress_layout.addWidget(fortress_image_label)
        fortress_layout.addWidget(self.fortress_button)
        fortress_widget.setLayout(fortress_layout)
        gazebo_layout.addWidget(fortress_widget)

        # Harmonic
        harmonic_widget = QWidget()
        harmonic_layout = QVBoxLayout()
        harmonic_label = QLabel("Gazebo Harmonic")
        harmonic_image_label = QLabel()
        harmonic_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "harmonic.jpg")
        if os.path.exists(harmonic_image_path):
            pixmap = QPixmap(harmonic_image_path).scaled(400, 400, Qt.KeepAspectRatio)
            harmonic_image_label.setPixmap(pixmap)
        else:
            harmonic_image_label.setText("Harmonic image not found")
        harmonic_image_label.setFixedSize(400, 400)
        self.harmonic_button = QPushButton("Select Harmonic")
        self.harmonic_button.clicked.connect(lambda: self.select_gazebo_version("harmonic"))
        harmonic_layout.addWidget(harmonic_label)
        harmonic_layout.addWidget(harmonic_image_label)
        harmonic_layout.addWidget(self.harmonic_button)
        harmonic_widget.setLayout(harmonic_layout)
        gazebo_layout.addWidget(harmonic_widget)

        gazebo_widget.setLayout(gazebo_layout)
        layout.addWidget(gazebo_widget)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider)

        # Isaac Sim section
        isaac_widget = QWidget()
        isaac_layout = QVBoxLayout()
        isaac_label = QLabel("Isaac Sim (Under Development)")
        isaac_image_label = QLabel()
        isaac_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "isaacsim_gray.jpg")
        if os.path.exists(isaac_image_path):
            pixmap = QPixmap(isaac_image_path).scaled(400, 400, Qt.KeepAspectRatio)
            isaac_image_label.setPixmap(pixmap)
        else:
            isaac_image_label.setText("Isaac Sim image not found")
        isaac_image_label.setFixedSize(400, 400)
        self.isaac_button = QPushButton("Select Isaac Sim")
        self.isaac_button.setEnabled(False)
        isaac_layout.addWidget(isaac_label)
        isaac_layout.addWidget(isaac_image_label)
        isaac_layout.addWidget(self.isaac_button)
        isaac_widget.setLayout(isaac_layout)
        layout.addWidget(isaac_widget)

        self.setLayout(layout)

        # Apply stylesheets for hover effects
        button_style = """
            QPushButton {
                background-color: #4A90E2;
                color: white;
                padding: 10px;
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
                padding: 10px;
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

        layout.addLayout(left_layout, 30)

        self.view = ZoomableGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("white"))
        self.view.installEventFilter(self)
        layout.addWidget(self.view, 70)

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
            self.scene.clear()
            grid_spacing = 10
            for x in range(-1000, 1000, grid_spacing):
                self.scene.addLine(x, -1000, x, 1000, QPen(QColor("lightgray")))
            for y in range(-1000, 1000, grid_spacing):
                self.scene.addLine(-1000, y, 1000, y, QPen(QColor("lightgray")))
            self.wall_items = {}
            for model in self.world_manager.models:
                if model["type"] == "wall":
                    self.wall_list.addItem(model["name"])
                    start = QPointF(model["properties"]["start"][0] * 100, model["properties"]["start"][1] * 100)
                    end = QPointF(model["properties"]["end"][0] * 100, model["properties"]["end"][1] * 100)
                    line = QGraphicsLineItem(QLineF(start, end))
                    self.scene.addItem(line)
                    text = QGraphicsTextItem(model["name"])
                    text.setPos((start + end) / 2)
                    self.scene.addItem(text)
                    self.wall_items[model["name"]] = (line, text)
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

        self.view = ZoomableGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("white"))
        self.view.installEventFilter(self)
        layout.addWidget(self.view, 70)

        self.setLayout(layout)

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
    def __init__(self):
        super().__init__()
        self.setTitle("Add Dynamic Obstacles")
        self.world_manager = None

        layout = QVBoxLayout()
        layout.addWidget(QLabel("This page is under development."))
        self.setLayout(layout)

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None

class SaveResultsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Save Results")
        self.world_manager = None

        layout = QVBoxLayout()
        self.save_button = QPushButton("Save World")
        self.save_button.clicked.connect(self.save_world)
        layout.addWidget(self.save_button)
        layout.addWidget(QLabel("Preview of future features..."))
        self.setLayout(layout)

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")

    def save_world(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")
            return
        try:
            self.world_manager.save_sdf(self.world_manager.world_path)
            QMessageBox.information(self, "Success", f"World saved to {self.world_manager.world_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save world: {str(e)}")

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
                geometry = model_elem.find(".//geometry/box")
                if geometry is not None:
                    model_type = "wall"
                else:
                    model_type = "unknown"

            properties = {}
            if model_type == "wall":
                pose_str = model_elem.find("pose").text
                pose = [float(x) for x in pose_str.split()]
                x, y, z, _, _, yaw = pose

                size_str = model_elem.find(".//box/size").text
                size = [float(x) for x in size_str.split()]
                length, width, height = size

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

        for model in self.models:
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

        self.models = [m for m in self.models if m["status"] != "removed"]
        for model in self.models:
            model["status"] = ""

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

        sdf = f"""<model name='{model["name"]}'>
            <static>true</static>
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
        self.setWindowTitle("Dynamic World Generator Wizard")
        self.resize(1200, 800)
        print("Window flags and size set")

        self.world_manager = None
        self.scene = QGraphicsScene()

        self.nav_list = QListWidget()
        self.nav_list.addItems(["Welcome", "Select Simulation", "Design Walls", "Add Static Obstacles",
                                "Add Dynamic Obstacles", "Save Results"])
        self.nav_list.setFixedWidth(200)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                font-size: 16pt;
                font-weight: bold;
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
        self.addPage(WallsDesignPage(self.scene))
        print("Added WallsDesignPage")
        self.addPage(StaticObstaclesPage(self.scene))
        print("Added StaticObstaclesPage")
        self.addPage(DynamicObstaclesPage())
        print("Added DynamicObstaclesPage")
        self.addPage(SaveResultsPage())
        print("Added SaveResultsPage")

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
                      "Add Dynamic Obstacles", "Save Results"]
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