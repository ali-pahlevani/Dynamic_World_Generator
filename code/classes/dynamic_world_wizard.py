from PyQt5.QtWidgets import (
    QWizard, QListWidget, QVBoxLayout, QWidget, QLabel,
    QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem,
)
from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF
from PyQt5.QtGui import QFont, QPen, QColor
from classes.world_manager import WorldManager
from classes.pages.welcome_page import WelcomePage
from classes.pages.sim_selection_page import SimSelectionPage
from classes.pages.walls_design_page import WallsDesignPage
from classes.pages.static_obstacles_page import StaticObstaclesPage
from classes.pages.dynamic_obstacles_page import DynamicObstaclesPage
from classes.pages.map_generation_page import MapGenerationPage
from classes.pages.coming_soon_page import ComingSoonPage
from utils.color_utils import get_color
import math

_NAV_LABELS = [
    "  Welcome",
    "  Select Simulation",
    "  Design Walls",
    "  Static Obstacles",
    "  Dynamic Obstacles",
    "  Map Generation",
    "  Coming Soon",
]

_PAGE_NAMES = [
    "Welcome", "Select Simulation", "Design Walls",
    "Add Static Obstacles", "Add Dynamic Obstacles",
    "Generate Map", "Coming Soon",
]

_SIDEBAR_QSS = """
QListWidget {
    background-color: #1E2D3D;
    color: #8FA8C0;
    border: none;
    padding: 6px 4px;
    outline: none;
    font-size: 10pt;
}
QListWidget::item {
    padding: 11px 10px;
    border-radius: 6px;
    margin: 2px 6px;
}
QListWidget::item:selected {
    background-color: #4A90E2;
    color: #FFFFFF;
    font-weight: bold;
}
QListWidget::item:hover:!selected {
    background-color: #2D4057;
    color: #FFFFFF;
}
"""


class DynamicWorldWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.Window | Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
        )
        self.setWindowTitle("Dynamic World Generator")
        self.setWizardStyle(QWizard.ModernStyle)
        self.resize(1600, 860)
        self.setMinimumSize(1000, 600)

        self.world_manager = None
        self.scene = QGraphicsScene()
        self.wall_items = {}
        self.obstacle_items = {}
        self.path_items = {}

        # ── Sidebar ────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("dwgSidebar")
        sidebar.setStyleSheet("QWidget#dwgSidebar { background-color: #1E2D3D; }")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        header = QLabel("DWG Wizard")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background-color: #152330;
                color: #FFFFFF;
                font-family: Arial;
                font-size: 14pt;
                font-weight: bold;
                padding: 20px 10px;
                border-bottom: 2px solid #4A90E2;
            }
        """)
        sidebar_layout.addWidget(header)

        self.nav_list = QListWidget()
        self.nav_list.addItems(_NAV_LABELS)
        self.nav_list.setFont(QFont("Arial", 10))
        self.nav_list.setStyleSheet(_SIDEBAR_QSS)
        self.nav_list.setCurrentRow(0)
        self.nav_list.itemClicked.connect(self.navigate_to_page)
        sidebar_layout.addWidget(self.nav_list, 1)

        version_label = QLabel("v2.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                color: #4A6680;
                font-size: 9pt;
                padding: 8px;
                background-color: #152330;
                border-top: 1px solid #2D4057;
            }
        """)
        sidebar_layout.addWidget(version_label)
        self.setSideWidget(sidebar)

        # ── Pages ──────────────────────────────────────────────────
        self.addPage(WelcomePage())
        sim_selection_page = SimSelectionPage()
        self.addPage(sim_selection_page)
        self.walls_page = WallsDesignPage(self.scene)
        self.addPage(self.walls_page)
        self.static_obstacles_page = StaticObstaclesPage(self.scene)
        self.addPage(self.static_obstacles_page)
        self.dynamic_obstacles_page = DynamicObstaclesPage(self.scene)
        self.addPage(self.dynamic_obstacles_page)
        self.map_generation_page = MapGenerationPage()
        self.addPage(self.map_generation_page)
        self.addPage(ComingSoonPage())

        sim_selection_page.simulationSelected.connect(self.initialize_world_manager)
        self.currentIdChanged.connect(self.update_navigation)

    # ── Size management ────────────────────────────────────────────────────

    def adjustSize(self):
        # Suppress automatic resizing so page transitions don't jump the window
        pass

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_buttons_styled", False):
            self._buttons_styled = True
            self._style_wizard_buttons()
            # Trigger initial layout pass with the correct window size
            self._apply_responsive_layout()

    # ── Wizard button styling ──────────────────────────────────────────────

    def _style_wizard_buttons(self):
        back = self.button(QWizard.BackButton)
        nxt = self.button(QWizard.NextButton)
        fin = self.button(QWizard.FinishButton)
        cancel = self.button(QWizard.CancelButton)
        for btn, role in [(back, "secondary"), (nxt, "success"),
                          (fin, "success"), (cancel, "cancel")]:
            if btn:
                btn.setProperty("btnRole", role)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                btn.setMinimumWidth(100)
                btn.setMinimumHeight(36)

    # ── Responsive layout ──────────────────────────────────────────────────

    def _apply_responsive_layout(self):
        w = max(self.width(), 1000)
        # Sidebar nav list: 15-20 % of window, clamped [180, 240]
        nav_w = max(min(int(w * 0.17), 240), 180)
        self.nav_list.setFixedWidth(nav_w)

        content_w = w - nav_w
        canvas_w = int(content_w * 0.73)
        left_w = content_w - canvas_w

        for page in (self.walls_page, self.static_obstacles_page,
                     self.dynamic_obstacles_page):
            page.view.setFixedWidth(canvas_w)
            if hasattr(page, "left_widget"):
                page.left_widget.setFixedWidth(left_w)

        # Map page has a preview panel instead of a QGraphicsView
        if hasattr(self, "map_generation_page"):
            self.map_generation_page.left_widget.setFixedWidth(left_w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_responsive_layout()

    # ── Canvas rendering ───────────────────────────────────────────────────

    def refresh_canvas(self, scene):
        scene.clear()
        self.wall_items.clear()
        self.obstacle_items.clear()
        self.path_items.clear()

        grid_spacing = 10
        grid_pen = QPen(QColor("#E0E0E0"), 0.5)
        for x in range(-1000, 1001, grid_spacing):
            scene.addLine(x, -1000, x, 1000, grid_pen)
        for y in range(-1000, 1001, grid_spacing):
            scene.addLine(-1000, y, 1000, y, grid_pen)

        if not self.world_manager:
            return

        for model in self.world_manager.models:
            if model.get("status") == "removed":
                continue
            mtype = model["type"]
            props = model["properties"]

            if mtype == "wall":
                start = QPointF(props["start"][0] * 100, -props["start"][1] * 100)
                end   = QPointF(props["end"][0]   * 100, -props["end"][1]   * 100)
                color_rgb = get_color(props["color"])
                thickness = max(int(props["width"] * 100), 2)
                line = QGraphicsLineItem(QLineF(start, end))
                line.setPen(QPen(QColor.fromRgbF(*color_rgb), thickness))
                scene.addItem(line)
                text = QGraphicsTextItem(model["name"])
                text.setDefaultTextColor(QColor("#2C3E50"))
                text.setFont(QFont("Arial", 7))
                text.setPos((start + end) / 2)
                scene.addItem(text)
                self.wall_items[model["name"]] = (line, text)

            elif mtype in ("box", "cylinder", "sphere"):
                position = props["position"]
                size = props["size"]
                center = QPointF(position[0] * 100, -position[1] * 100)
                if mtype == "box":
                    W, L, _ = size
                    hw = round((W / 2) * 100 / 10) * 10
                    hl = round((L / 2) * 100 / 10) * 10
                    item = QGraphicsRectItem(QRectF(center.x() - hw, center.y() - hl, 2*hw, 2*hl))
                else:
                    R = size[0] * 100
                    item = QGraphicsEllipseItem(QRectF(center.x() - R, center.y() - R, 2*R, 2*R))
                item.setPen(QPen(QColor("#2C3E50"), 1.5))
                item.setBrush(QColor.fromRgbF(*get_color(props["color"])))
                scene.addItem(item)
                text = QGraphicsTextItem(model["name"])
                text.setDefaultTextColor(QColor("#2C3E50"))
                text.setFont(QFont("Arial", 7))
                text.setPos(center)
                scene.addItem(text)
                self.obstacle_items[model["name"]] = (item, text)

            motion = props.get("motion")
            if motion:
                type_ = motion["type"]
                color = {"linear": "#E74C3C", "elliptical": "#27AE60", "polygon": "#4A90E2"}[type_]
                items = []
                if type_ == "linear":
                    p1 = QPointF(motion["path"][0][0]*100, -motion["path"][0][1]*100)
                    p2 = QPointF(motion["path"][1][0]*100, -motion["path"][1][1]*100)
                    ln = QGraphicsLineItem(QLineF(p1, p2))
                    ln.setPen(QPen(QColor(color), 2))
                    scene.addItem(ln)
                    items.append(ln)
                elif type_ == "elliptical":
                    cx, cy = props["position"][:2]
                    c = QPointF(cx*100, -cy*100)
                    sm, sn, ang = motion["semi_major"], motion["semi_minor"], motion["angle"]
                    ell = QGraphicsEllipseItem(QRectF(-sm*100, -sn*100, 2*sm*100, 2*sn*100))
                    ell.setPos(c)
                    ell.setRotation(-math.degrees(ang))
                    ell.setPen(QPen(QColor(color), 2))
                    scene.addItem(ell)
                    items.append(ell)
                elif type_ == "polygon":
                    pts = [QPointF(p[0]*100, -p[1]*100) for p in motion["path"]]
                    for i in range(len(pts)):
                        ln = QGraphicsLineItem(QLineF(pts[i], pts[(i+1) % len(pts)]))
                        ln.setPen(QPen(QColor(color), 2))
                        scene.addItem(ln)
                        items.append(ln)
                self.path_items[model["name"]] = items

    # ── Window close ───────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self.world_manager:
            self.world_manager.cleanup()
        event.accept()

    # ── Helpers ────────────────────────────────────────────────────────────

    def initialize_world_manager(self, sim_type, version):
        if sim_type == "gazebo" and version in ("fortress", "harmonic"):
            self.world_manager = WorldManager(sim_type, version)
        else:
            self.world_manager = None

    def update_navigation(self, page_id):
        if page_id == -1:
            return
        idx = self.pageIds().index(page_id)
        if self.nav_list.currentRow() != idx:
            self.nav_list.setCurrentRow(idx)

    def navigate_to_page(self, item):
        target = _NAV_LABELS.index(item.text())
        current = self.pageIds().index(self.currentId())
        while current < target:
            if self.currentPage().isComplete():
                self.next()
                current += 1
            else:
                break
        while current > target:
            self.back()
            current -= 1
