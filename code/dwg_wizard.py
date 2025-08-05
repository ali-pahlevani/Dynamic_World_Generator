#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
import math
from xml.etree import ElementTree as ET
from PyQt5.QtWidgets import QWizard, QWizardPage, QListWidget, QVBoxLayout, QHBoxLayout, QWidget, QApplication, QPushButton, QLabel, QLineEdit, QComboBox, QGraphicsView, QGraphicsScene, QMessageBox, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem
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

        layout = QVBoxLayout()

        gazebo_layout = QHBoxLayout()
        gazebo_label = QLabel("Gazebo")
        gazebo_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "gazebo.jpg")
        print(f"Looking for Gazebo image at: {gazebo_image_path}")
        gazebo_image_label = QLabel()
        if os.path.exists(gazebo_image_path):
            pixmap = QPixmap(gazebo_image_path).scaled(100, 100, Qt.KeepAspectRatio)
            gazebo_image_label.setPixmap(pixmap)
        else:
            gazebo_image_label.setText("Gazebo image not found")
        self.gazebo_button = QPushButton("Select Gazebo")
        self.gazebo_button.clicked.connect(self.show_gazebo_versions)
        gazebo_layout.addWidget(gazebo_label)
        gazebo_layout.addWidget(gazebo_image_label)
        gazebo_layout.addWidget(self.gazebo_button)
        layout.addLayout(gazebo_layout)

        self.fortress_button = QPushButton("Fortress")
        self.fortress_button.setVisible(False)
        self.fortress_button.clicked.connect(lambda: self.select_gazebo_version("fortress"))
        layout.addWidget(self.fortress_button)

        self.harmonic_button = QPushButton("Harmonic")
        self.harmonic_button.setVisible(False)
        self.harmonic_button.clicked.connect(lambda: self.select_gazebo_version("harmonic"))
        layout.addWidget(self.harmonic_button)

        isaac_layout = QHBoxLayout()
        isaac_label = QLabel("Isaac Sim (Under Development)")
        isaac_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "intro", "isaacsim.jpg")
        print(f"Looking for Isaac Sim image at: {isaac_image_path}")
        isaac_image_label = QLabel()
        if os.path.exists(isaac_image_path):
            pixmap = QPixmap(isaac_image_path).scaled(100, 100, Qt.KeepAspectRatio)
            isaac_image_label.setPixmap(pixmap)
        else:
            isaac_image_label.setText("Isaac Sim image not found")
        self.isaac_button = QPushButton("Select Isaac Sim")
        self.isaac_button.clicked.connect(lambda: self.select_simulation("isaac", None))
        isaac_layout.addWidget(isaac_label)
        isaac_layout.addWidget(isaac_image_label)
        isaac_layout.addWidget(self.isaac_button)
        layout.addLayout(isaac_layout)

        self.setLayout(layout)

    def show_gazebo_versions(self):
        self.fortress_button.setVisible(True)
        self.harmonic_button.setVisible(True)

    def select_gazebo_version(self, version):
        self._simulation = "gazebo"
        self._gazebo_version = version
        self.simulation_field.setText("gazebo")
        self.gazebo_version_field.setText(version)
        self.simulationSelected.emit("gazebo", version)
        self.completeChanged.emit()

    def select_simulation(self, sim_type, version=None):
        self._simulation = sim_type
        self.simulation_field.setText(sim_type)
        if version:
            self._gazebo_version = version
            self.gazebo_version_field.setText(version)
        else:
            self._gazebo_version = ""
            self.gazebo_version_field.setText("")
        self.simulationSelected.emit(sim_type, version)
        if sim_type == "isaac":
            QMessageBox.information(self, "Under Development", "Isaac Sim support is currently under development.")
        self.completeChanged.emit()

    def isComplete(self):
        return self._simulation == "gazebo" and self._gazebo_version in ["fortress", "harmonic"]

class WallsDesignPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Design Walls")

        self.registerField("world_name", self)
        self.registerField("wall_list", self)
        self.world_manager = None
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

        self.scene = QGraphicsScene()
        grid_spacing = 10
        for x in range(-1000, 1000, grid_spacing):
            self.scene.addLine(x, -1000, x, 1000, QPen(QColor("lightgray")))
        for y in range(-1000, 1000, grid_spacing):
            self.scene.addLine(-1000, y, 1000, y, QPen(QColor("lightgray")))
        self.view = QGraphicsView(self.scene)
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
                    self.wall_items[wall_name] = line
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
            # Use parent directory for worlds
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
                    self.wall_items[model["name"]] = line
            QMessageBox.information(self, "Success", f"Loaded world: {world_name}")
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
                self.scene.removeItem(self.wall_items[wall_name])
                del self.wall_items[wall_name]
            for model in self.world_manager.models:
                if model["name"] == wall_name:
                    model["status"] = "removed"
                    break
            self.wall_list.takeItem(self.wall_list.row(selected))

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
    def __init__(self):
        super().__init__()
        self.setTitle("Add Static Obstacles")
        self.world_manager = None
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

        self.scene = QGraphicsScene()
        grid_spacing = 10
        for x in range(-1000, 1000, grid_spacing):
            self.scene.addLine(x, -1000, x, 1000, QPen(QColor("lightgray")))
        for y in range(-1000, 1000, grid_spacing):
            self.scene.addLine(-1000, y, 1000, y, QPen(QColor("lightgray")))
        self.view = QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("white"))
        self.view.installEventFilter(self)
        layout.addWidget(self.view, 70)

        self.setLayout(layout)

        self.drawing = False
        self.start_point = None
        self.current_item = None

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
        if obj == self.view:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton and self.world_manager:
                self.drawing = True
                self.start_point = self.view.mapToScene(event.pos())
                obstacle_type = self.obstacle_type_combo.currentText()
                if obstacle_type == "Box":
                    self.current_item = QGraphicsRectItem(QRectF(self.start_point, self.start_point))
                    self.current_item.setPen(QPen(Qt.black, 2))
                    self.current_item.setBrush(QColor("lightgray"))
                elif obstacle_type in ["Cylinder", "Sphere"]:
                    self.current_item = QGraphicsEllipseItem(QRectF(self.start_point, self.start_point))
                    self.current_item.setPen(QPen(Qt.black, 2))
                    self.current_item.setBrush(QColor("lightgray"))
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
                center = self.snap_to_grid(self.current_item.rect().center())
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
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Move up one level to Dynamic_World_Generator

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

        # Launch the world
        if self.version == "fortress":
            cmd = ["ign", "gazebo", self.world_path]
        else:
            cmd = ["gz", "sim", self.world_path]
        self.process = subprocess.Popen(cmd)

        # Parse the SDF
        self.sdf_tree = ET.parse(self.world_path)
        self.sdf_root = self.sdf_tree.getroot()
        self.world_name = self.sdf_root.find("world").get("name")
        self.models = []

        # Iterate through models in the SDF
        for model_elem in self.sdf_root.findall(".//model"):
            name = model_elem.get("name")
            type_elem = model_elem.find("type")
            model_type = type_elem.text if type_elem is not None else "unknown"
            properties = {}
            
            if model_type == "wall":
                # Extract pose (x, y, z, roll, pitch, yaw)
                pose_str = model_elem.find("pose").text
                pose = [float(x) for x in pose_str.split()]
                x, y, z, _, _, yaw = pose
                
                # Extract size (length, width, height)
                size_str = model_elem.find(".//box/size").text
                size = [float(x) for x in size_str.split()]
                length, width, height = size
                
                # Calculate start and end points based on center, length, and yaw
                dx = (length / 2) * math.cos(yaw)
                dy = (length / 2) * math.sin(yaw)
                start_x = x - dx
                start_y = y - dy
                end_x = x + dx
                end_y = y + dy
                
                # Populate properties
                properties = {
                    "start": (start_x, start_y),
                    "end": (end_x, end_y),
                    "width": width,
                    "height": height,
                    "color": "Gray"  # Default color; adjust if stored in SDF
                }
            
            # Add model to the list
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
                sdf_snippet = self.generate_model_sdf(model)
                # Escape double quotes for command-line compatibility
                sdf_escaped = sdf_snippet.replace('"', '\\"')
                # Compact the SDF string by removing extra whitespace
                sdf_compact = ' '.join(sdf_escaped.split())
                # Construct the request string
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
                if result.returncode != 0:
                    print(f"Warning: Failed to add model {model['name']}: {result.stderr}")
                    continue
                # Add to SDF and save
                model_elem = ET.fromstring(sdf_snippet)
                self.sdf_root.find("world").append(model_elem)
                self.save_sdf(self.world_path)
            elif model["status"] == "removed":
                request_str = f'name: "{model["name"]}" type: 2'
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

    def generate_model_sdf(self, model):
        model_type = model["type"]
        props = model["properties"]
        color_rgb = get_color(props["color"])
        
        # Calculate pose and size based on model type
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
                size_str = f"{size[0]:.6f} {size[1]:.6f}"  # radius, height
            elif model_type == "sphere":
                size_str = f"{size[0]:.6f}"  # radius

        # Generate the SDF string without <sdf> wrapper
        sdf = f"""<model name='{model["name"]}'>
            <static>true</static>
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
        self.addPage(WallsDesignPage())
        print("Added WallsDesignPage")
        self.addPage(StaticObstaclesPage())
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