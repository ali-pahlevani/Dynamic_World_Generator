from PyQt5.QtWidgets import QWizardPage, QLineEdit, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from utils.config import INTRO_IMAGES_DIR
import os

class SimSelectionPage(QWizardPage):
    simulationSelected = pyqtSignal(str, str)

    def __init__(self):
        # Initialize wizard page with title and hidden fields
        super().__init__()
        self.setTitle("Select Simulation Platform")
        self._simulation = ""
        self._gazebo_version = ""

        # Register hidden fields for simulation and version
        self.simulation_field = QLineEdit()
        self.simulation_field.setVisible(False)
        self.gazebo_version_field = QLineEdit()
        self.gazebo_version_field.setVisible(False)
        self.registerField("simulation*", self.simulation_field)
        self.registerField("gazebo_version", self.gazebo_version_field)

        # Setup main layout with Gazebo and Isaac Sim sections
        layout = QHBoxLayout()

        # Gazebo section with Harmonic and Fortress options
        gazebo_widget = QWidget()
        gazebo_layout = QVBoxLayout()

        # Harmonic option
        harmonic_widget = QWidget()
        harmonic_layout = QVBoxLayout()
        harmonic_label = QLabel("Gazebo Harmonic (Recommended)")
        harmonic_label.setAlignment(Qt.AlignCenter)
        harmonic_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        harmonic_label.setStyleSheet("color: red;")
        harmonic_image_label = QLabel()
        harmonic_image_path = os.path.join(INTRO_IMAGES_DIR, "harmonic.png")
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

        # Horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        gazebo_layout.addWidget(separator)

        # Fortress option
        fortress_widget = QWidget()
        fortress_layout = QVBoxLayout()
        fortress_label = QLabel("Gazebo Fortress")
        fortress_label.setAlignment(Qt.AlignCenter)
        fortress_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        fortress_label.setStyleSheet("color: red;")
        fortress_image_label = QLabel()
        fortress_image_path = os.path.join(INTRO_IMAGES_DIR, "fortress.jpeg")
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

        gazebo_layout.addStretch(1)
        gazebo_widget.setLayout(gazebo_layout)
        layout.addWidget(gazebo_widget, stretch=1)

        # Vertical divider
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider, stretch=0)

        # Isaac Sim section (disabled)
        isaac_widget = QWidget()
        isaac_layout = QVBoxLayout()
        isaac_layout.addStretch(1)
        isaac_label = QLabel("Isaac Sim (Under Development)")
        isaac_label.setAlignment(Qt.AlignCenter)
        isaac_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        isaac_label.setStyleSheet("color: red;")
        isaac_image_label = QLabel()
        isaac_image_path = os.path.join(INTRO_IMAGES_DIR, "isaacsim_450_gray.png")
        if os.path.exists(isaac_image_path):
            pixmap = QPixmap(isaac_image_path).scaled(674, 1264, Qt.KeepAspectRatio)
            isaac_image_label.setPixmap(pixmap)
        else:
            isaac_image_label.setText("Isaac Sim image not found")
        isaac_image_label.setFixedSize(550, 400)
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
        isaac_layout.addStretch(1)
        isaac_widget.setLayout(isaac_layout)
        layout.addWidget(isaac_widget, stretch=1)

        self.setLayout(layout)

        # Apply button stylesheets
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
        # Select Gazebo version and emit signal
        self._simulation = "gazebo"
        self._gazebo_version = version
        self.simulation_field.setText("gazebo")
        self.gazebo_version_field.setText(version)
        self.simulationSelected.emit("gazebo", version)
        self.completeChanged.emit()

    def isComplete(self):
        # Check if a valid simulation and version are selected
        return self._simulation == "gazebo" and self._gazebo_version in ["fortress", "harmonic"]