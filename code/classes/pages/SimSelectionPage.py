from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtProperty
from PyQt5.QtCore import Qt
import os

class SimSelectionPage(QWizardPage):
    simulationSelected = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setTitle("Select Simulation Platform")

        self._simulation = ""
        self._gazebo_version = ""

        from PyQt5.QtWidgets import QLineEdit
        self.simulation_field = QLineEdit()
        self.simulation_field.setVisible(False)
        self.gazebo_version_field = QLineEdit()
        self.gazebo_version_field.setVisible(False)
        self.registerField("simulation*", self.simulation_field)
        self.registerField("gazebo_version", self.gazebo_version_field)

        layout = QVBoxLayout()

        # Gazebo section
        gazebo_layout = QHBoxLayout()
        gazebo_label = QLabel("Gazebo")
        gazebo_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "images", "intro", "gazebo.jpg")
        print(f"Looking for Gazebo image at: {gazebo_image_path}")  # Debug
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

        # Isaac Sim section
        isaac_layout = QHBoxLayout()
        isaac_label = QLabel("Isaac Sim (Under Development)")
        isaac_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "images", "intro", "isaacsim.jpg")
        print(f"Looking for Isaac Sim image at: {isaac_image_path}")  # Debug
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