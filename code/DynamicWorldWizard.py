#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QWizard, QListWidget, QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Import classes
from classes.pages.WelcomePage import WelcomePage
from classes.pages.SimSelectionPage import SimSelectionPage
from classes.pages.WallsDesignPage import WallsDesignPage
from classes.pages.StaticObstaclesPage import StaticObstaclesPage
from classes.pages.DynamicObstaclesPage import DynamicObstaclesPage
from classes.pages.SaveResultsPage import SaveResultsPage
from classes.WorldManager import WorldManager

class DynamicWorldWizard(QWizard):
    def __init__(self):
        print("Entering DynamicWorldWizard.__init__")  # Debug
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Dynamic World Generator Wizard")
        self.resize(1200, 800)
        print("Window flags and size set")  # Debug

        # Initialize WorldManager as None; set after simulation selection
        self.world_manager = None

        # Navigation list
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
        print("Navigation list initialized")  # Debug

        # Add pages
        self.addPage(WelcomePage())
        print("Added WelcomePage")  # Debug
        sim_selection_page = SimSelectionPage()
        self.addPage(sim_selection_page)
        print("Added SimSelectionPage")  # Debug
        self.addPage(WallsDesignPage())
        print("Added WallsDesignPage")  # Debug
        self.addPage(StaticObstaclesPage())
        print("Added StaticObstaclesPage")  # Debug
        self.addPage(DynamicObstaclesPage())
        print("Added DynamicObstaclesPage")  # Debug
        self.addPage(SaveResultsPage())
        print("Added SaveResultsPage")  # Debug

        # Connect simulation selection to WorldManager initialization
        sim_selection_page.simulationSelected.connect(self.initialize_world_manager)
        print("Connected simulationSelected signal")  # Debug

        # Set side widget
        side_widget = QWidget()
        side_layout = QVBoxLayout()
        side_layout.addWidget(self.nav_list)
        side_layout.addStretch()
        side_widget.setLayout(side_layout)
        self.setSideWidget(side_widget)
        print("Side widget set")  # Debug

        self.currentIdChanged.connect(self.update_navigation)
        print("Connected currentIdChanged signal")  # Debug

    def initialize_world_manager(self, sim_type, version):
        print(f"Initializing WorldManager with sim_type={sim_type}, version={version}")  # Debug
        if sim_type == "gazebo" and version in ["fortress", "harmonic"]:
            self.world_manager = WorldManager(sim_type, version)
        else:
            self.world_manager = None  # Isaac Sim or invalid selection

    def update_navigation(self, page_id):
        print(f"Updating navigation to page_id={page_id}")  # Debug
        page_index = self.pageIds().index(page_id)
        if self.nav_list.currentRow() != page_index:
            self.nav_list.setCurrentRow(page_index)

    def navigate_to_page(self, item):
        print(f"Navigating to page: {item.text()}")  # Debug
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
    print("Entering main block")  # Debug
    app = QApplication(sys.argv)
    print("QApplication created")  # Debug
    wizard = DynamicWorldWizard()
    print("DynamicWorldWizard instance created")  # Debug
    wizard.show()
    print("Wizard shown")  # Debug
    sys.exit(app.exec_())