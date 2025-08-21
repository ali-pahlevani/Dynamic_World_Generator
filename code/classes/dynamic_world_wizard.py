from PyQt5.QtWidgets import QWizard, QListWidget, QVBoxLayout, QWidget, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF, pyqtProperty
from PyQt5.QtGui import QFont, QPen, QColor
from classes.world_manager import WorldManager
from classes.pages.welcome_page import WelcomePage
from classes.pages.sim_selection_page import SimSelectionPage
from classes.pages.walls_design_page import WallsDesignPage
from classes.pages.static_obstacles_page import StaticObstaclesPage
from classes.pages.dynamic_obstacles_page import DynamicObstaclesPage
from classes.pages.coming_soon_page import ComingSoonPage
from utils.color_utils import get_color
import math

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
        self.wall_items = {}
        self.obstacle_items = {}
        self.path_items = {}

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

    def refresh_canvas(self, scene):
        scene.clear()
        self.path_items.clear()  # Add this to ensure path_items is reset
        grid_spacing = 10
        for x in range(-1000, 1000, grid_spacing):
            scene.addLine(x, -1000, x, 1000, QPen(QColor("lightgray")))
        for y in range(-1000, 1000, grid_spacing):
            scene.addLine(-1000, y, 1000, y, QPen(QColor("lightgray")))
        self.wall_items.clear()
        self.obstacle_items.clear()
        self.path_items.clear()
        if self.world_manager:
            for model in self.world_manager.models:
                if model.get("status") == "removed":
                    continue
                if model["type"] == "wall":
                    start = QPointF(model["properties"]["start"][0] * 100, -model["properties"]["start"][1] * 100)
                    end = QPointF(model["properties"]["end"][0] * 100, -model["properties"]["end"][1] * 100)
                    color_rgb = get_color(model["properties"]["color"])
                    qcolor = QColor.fromRgbF(*color_rgb)
                    thickness = max(int(model["properties"]["width"] * 100), 2)
                    line = QGraphicsLineItem(QLineF(start, end))
                    line.setPen(QPen(qcolor, thickness))
                    scene.addItem(line)
                    text = QGraphicsTextItem(model["name"])
                    text.setPos((start + end) / 2)
                    scene.addItem(text)
                    self.wall_items[model["name"]] = (line, text)
                elif model["type"] in ["box", "cylinder", "sphere"]:
                    position = model["properties"]["position"]
                    size = model["properties"]["size"]
                    center = QPointF(position[0] * 100, -position[1] * 100)
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
                    color_rgb = get_color(model["properties"]["color"])
                    item.setBrush(QColor.fromRgbF(*color_rgb))
                    scene.addItem(item)
                    text = QGraphicsTextItem(model["name"])
                    text.setPos(center)
                    scene.addItem(text)
                    self.obstacle_items[model["name"]] = (item, text)
                motion = model["properties"].get("motion")
                if motion:
                    type_ = motion["type"]
                    color = {"linear": "red", "elliptical": "green", "polygon": "blue"}[type_]
                    items = []
                    if type_ == "linear":
                        p1 = QPointF(motion["path"][0][0] * 100, -motion["path"][0][1] * 100)
                        p2 = QPointF(motion["path"][1][0] * 100, -motion["path"][1][1] * 100)
                        line = QGraphicsLineItem(QLineF(p1, p2))
                        line.setPen(QPen(QColor(color), 2))
                        scene.addItem(line)
                        items.append(line)
                    elif type_ == "elliptical":
                        center_m = model["properties"]["position"][:2]
                        center = QPointF(center_m[0] * 100, -center_m[1] * 100)
                        semi_major = motion["semi_major"]
                        semi_minor = motion["semi_minor"]
                        angle = motion["angle"]
                        ellipse = QGraphicsEllipseItem(QRectF(-semi_major * 100, -semi_minor * 100, 2 * semi_major * 100, 2 * semi_minor * 100))
                        ellipse.setPos(center)
                        ellipse.setRotation(-math.degrees(angle))
                        ellipse.setPen(QPen(QColor(color), 2))
                        scene.addItem(ellipse)
                        items.append(ellipse)
                    elif type_ == "polygon":
                        points = [QPointF(p[0] * 100, -p[1] * 100) for p in motion["path"]]
                        for i in range(len(points)):
                            line = QGraphicsLineItem(QLineF(points[i], points[(i + 1) % len(points)]))
                            line.setPen(QPen(QColor(color), 2))
                            scene.addItem(line)
                            items.append(line)
                    self.path_items[model["name"]] = items

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
        if page_id != -1:
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