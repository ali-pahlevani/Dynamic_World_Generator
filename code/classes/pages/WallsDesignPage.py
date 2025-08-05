from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PyQt5.QtCore import Qt, QLineF, QPointF, QEvent
from PyQt5.QtGui import QPen, QColor
import os
import shutil
from xml.etree import ElementTree as ET

class WallsDesignPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Design Walls")

        self.registerField("world_name", self)
        self.registerField("wall_list", self)
        self.world_manager = None
        self.wall_items = {}

        layout = QHBoxLayout()

        # Left section (30%)
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

        # Right section (70%) - Canvas
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("white"))
        self.view.installEventFilter(self)
        layout.addWidget(self.view, 70)

        self.setLayout(layout)

        # Canvas interaction
        self.drawing = False
        self.start_point = None
        self.current_line = None

    def initializePage(self):
        self.world_manager = self.wizard().world_manager

    def eventFilter(self, obj, event):
        if obj == self.view:
            print("Event:", event.type())
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton and self.world_manager:
                self.drawing = True
                self.start_point = self.view.mapToScene(event.pos())
                self.current_line = QGraphicsLineItem(QLineF(self.start_point, self.start_point))
                self.current_line.setPen(QPen(Qt.black, 2))
                self.scene.addItem(self.current_line)
                return True
            elif event.type() == QEvent.MouseMove and self.drawing and self.current_line:
                end_point = self.view.mapToScene(event.pos())
                self.current_line.setLine(QLineF(self.start_point, end_point))
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton and self.drawing and self.world_manager:
                self.drawing = False
                end_point = self.view.mapToScene(event.pos())
                try:
                    width = float(self.width_input.text() or 0.1)
                    height = float(self.height_input.text() or 1.0)
                except ValueError:
                    width, height = 0.1, 1.0
                color = self.color_input.text() or "Gray"
                wall_name = f"wall_{len(self.world_manager.models) + 1}"
                wall = {
                    "name": wall_name,
                    "type": "wall",
                    "properties": {
                        "start": (self.start_point.x() / 100, self.start_point.y() / 100),
                        "end": (end_point.x() / 100, end_point.y() / 100),
                        "width": width,
                        "height": height,
                        "color": color
                    },
                    "status": "new"
                }
                self.world_manager.add_model(wall)
                self.wall_list.addItem(wall_name)
                self.wall_items[wall_name] = self.current_line
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
            # Use WorldManager's path for empty_world.sdf
            empty_world_path = os.path.join(self.world_manager.base_dir, "worlds", "gazebo", self.world_manager.version, "empty_world.sdf")
            print(f"Copying empty world from: {empty_world_path}")  # Debug
            if not os.path.exists(empty_world_path):
                raise FileNotFoundError(f"Empty world file not found: {empty_world_path}")
            new_world_path = os.path.join(self.world_manager.base_dir, "worlds", "gazebo", self.world_manager.version, f"{world_name}.sdf")
            print(f"Creating new world at: {new_world_path}")  # Debug

            # Copy the empty_world.sdf to the new world file
            shutil.copyfile(empty_world_path, new_world_path)

            # Update the world name in the SDF file
            tree = ET.parse(new_world_path)
            root = tree.getroot()
            world_elem = root.find("world")
            if world_elem is not None:
                world_elem.set("name", world_name)
            else:
                raise ValueError("SDF file does not contain a <world> element")
            tree.write(new_world_path, encoding="utf-8", xml_declaration=True)

            # Load the new world using WorldManager
            self.world_manager.load_world(world_name)

            self.wall_list.clear()
            self.scene.clear()
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