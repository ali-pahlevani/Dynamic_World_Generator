from PyQt5.QtWidgets import QLabel, QWizardPage, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QListWidget, QMessageBox, QWidget
from PyQt5.QtCore import Qt, QEvent, QPointF
from PyQt5.QtGui import QColor
from classes.zoomable_graphics_view import ZoomableGraphicsView
import os
import shutil
from xml.etree import ElementTree as ET
from utils.config import WORLDS_GAZEBO_DIR

class WallsDesignPage(QWizardPage):
    def __init__(self, scene):
        # Initialize wizard page with title and layout
        super().__init__()
        self.setTitle("Design Walls")
        self.registerField("world_name", self)
        self.registerField("world_list", self)
        self.registerField("wall_list", self)
        self.world_manager = None
        self.scene = scene

        self.world_list = QListWidget()

        # Setup main layout with left panel and canvas
        layout = QHBoxLayout()
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Add buttons and input fields to left panel
        self.create_world_button = QPushButton("Create New World")
        self.create_world_button.clicked.connect(self.create_new_world)
        left_layout.addWidget(self.create_world_button)

        self.load_world_button = QPushButton("Load World")
        self.load_world_button.clicked.connect(self.load_world)
        left_layout.addWidget(self.load_world_button)

        self.world_name_input = QLineEdit()
        self.world_name_input.setPlaceholderText("World Name")
        left_layout.addWidget(self.world_name_input)

        worlds_label = QLabel("Worlds:")
        left_layout.addWidget(worlds_label)
        left_layout.addWidget(self.world_list)
        self.world_list.itemSelectionChanged.connect(self.update_world_name)       

        walls_label = QLabel("Walls:")
        left_layout.addWidget(walls_label)
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

        # Setup zoomable canvas
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("white"))
        self.view.installEventFilter(self)

        # Set size constraints for canvas and left panel
        window_width = 1500
        canvas_width = int(window_width * 0.7)
        self.view.setMinimumWidth(int(800 * 0.7))
        self.view.setMaximumWidth(canvas_width)
        left_widget.setMinimumWidth(150)
        left_widget.setMaximumWidth(window_width - canvas_width - 260)

        layout.addWidget(left_widget)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def initializePage(self):
        # Set world manager from wizard
        self.world_manager = self.wizard().world_manager
        self.refresh_worlds_list()

    def snap_to_grid(self, point, grid_spacing=10):
        # Snap point to grid for wall placement
        x = round(point.x() / grid_spacing) * grid_spacing
        y = round(point.y() / grid_spacing) * grid_spacing
        return QPointF(x, y)

    def eventFilter(self, obj, event):
        # Handle mouse clicks to add walls
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
                            "start": (self.start_point.x() / 100, -self.start_point.y() / 100),
                            "end": (end_point.x() / 100, -end_point.y() / 100),
                            "width": float(self.width_input.text() or 0.1),
                            "height": float(self.height_input.text() or 1.0),
                            "color": self.color_input.text() or "Gray"
                        },
                        "status": "new"
                    }
                    self.world_manager.add_model(wall)
                    self.wall_list.addItem(wall_name)
                    self.wizard().refresh_canvas(self.scene)
                    del self.start_point
                return True
        return super().eventFilter(obj, event)
    
    def update_world_name(self):
        selected_items = self.world_list.selectedItems()
        if selected_items:
            self.world_name_input.setText(selected_items[0].text()) 

    def create_new_world(self):
        # Create a new world from empty template
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        world_name = self.world_name_input.text().strip()
        if not world_name:
            QMessageBox.warning(self, "Error", "Please enter a valid world name.")
            return
        try:
            empty_world_path = os.path.join(WORLDS_GAZEBO_DIR, self.world_manager.version, "empty_world.sdf")
            if not os.path.exists(empty_world_path):
                raise FileNotFoundError(f"Empty world file not found: {empty_world_path}")
            new_world_path = os.path.join(WORLDS_GAZEBO_DIR, self.world_manager.version, f"{world_name}.sdf")
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
            self.refresh_worlds_list()
            self.wizard().refresh_canvas(self.scene)
            QMessageBox.information(self, "Success", f"Created and loaded new world: {world_name}")
            self.completeChanged.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create world: {str(e)}")

    def load_world(self):
        # Load an existing world
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        world_name = self.world_name_input.text().strip()
        if not world_name:
            QMessageBox.warning(self, "Error", "Please enter a valid world name.")
            return
        try:
            self.refresh_worlds_list()
            self.world_manager.load_world(world_name)
            self.wall_list.clear()
            self.wizard().refresh_canvas(self.scene)
            for model in self.world_manager.models:
                if model["type"] == "wall":
                    self.wall_list.addItem(model["name"])
            QMessageBox.information(self, "Success", f"Loaded world: {world_name}")
            self.completeChanged.emit()
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load world: {str(e)}")

    def refresh_worlds_list(self):
        self.world_list.clear()
        self.world_manager.refresh_worlds_list()
        for world in self.world_manager.worlds:
            self.world_list.addItem(world)

    def remove_selected_wall(self):
        # Remove selected wall from scene and world
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        selected = self.wall_list.currentItem()
        if selected:
            wall_name = selected.text()
            if wall_name in self.wizard().wall_items:
                line, text = self.wizard().wall_items[wall_name]
                self.scene.removeItem(line)
                self.scene.removeItem(text)
                del self.wizard().wall_items[wall_name]
            for model in self.world_manager.models:
                if model["name"] == wall_name:
                    model["status"] = "removed"
                    break
            self.wall_list.takeItem(self.wall_list.row(selected))

    def apply_changes(self):
        # Apply changes to the world and refresh canvas
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform first.")
            return
        try:
            self.world_manager.apply_changes()
            self.wizard().refresh_canvas(self.scene)
            QMessageBox.information(self, "Success", "Changes applied successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {str(e)}")

    def isComplete(self):
        # Check if world manager and world name are set
        return self.world_manager is not None and self.world_manager.world_name is not None