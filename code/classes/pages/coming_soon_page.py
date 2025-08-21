from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
from utils.config import FUTURE_IMAGES_DIR
import os

class ComingSoonPage(QWizardPage):
    def __init__(self):
        # Initialize wizard page with title
        super().__init__()
        self.setTitle("Coming Soon")
        self.world_manager = None

        # Setup main layout with vertical centering
        layout = QVBoxLayout()
        layout.addStretch(1)

        # Container for future feature images
        images_widget = QWidget()
        images_layout = QHBoxLayout()
        images_layout.setSpacing(20)

        # Gazebo Ionic feature
        feature1_widget = QWidget()
        feature1_layout = QVBoxLayout()
        feature1_label = QLabel("Gazebo Ionic")
        feature1_label.setAlignment(Qt.AlignCenter)
        feature1_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        feature1_label.setStyleSheet("color: red;")
        feature1_image_label = QLabel()
        feature1_image_path = os.path.join(FUTURE_IMAGES_DIR, "ionic.png")
        if os.path.exists(feature1_image_path):
            pixmap = QPixmap(feature1_image_path).scaled(350, 350, Qt.KeepAspectRatio)
            feature1_image_label.setPixmap(pixmap)
        else:
            feature1_image_label.setText("Future 1 image not found")
        feature1_image_label.setFixedSize(350, 350)
        feature1_image_label.setAlignment(Qt.AlignCenter)
        feature1_layout.addWidget(feature1_image_label, alignment=Qt.AlignCenter)
        feature1_layout.addSpacing(10)
        feature1_layout.addWidget(feature1_label)
        feature1_layout.addStretch(1)
        feature1_widget.setLayout(feature1_layout)
        images_layout.addWidget(feature1_widget)

        # Isaac Sim 4.5.0 feature
        feature2_widget = QWidget()
        feature2_layout = QVBoxLayout()
        feature2_label = QLabel("Isaac Sim 4.5.0")
        feature2_label.setAlignment(Qt.AlignCenter)
        feature2_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        feature2_label.setStyleSheet("color: red;")
        feature2_image_label = QLabel()
        feature2_image_path = os.path.join(FUTURE_IMAGES_DIR, "isaacsim_450.png")
        if os.path.exists(feature2_image_path):
            pixmap = QPixmap(feature2_image_path).scaled(674, 1264, Qt.KeepAspectRatio)
            feature2_image_label.setPixmap(pixmap)
        else:
            feature2_image_label.setText("Future 2 image not found")
        feature2_image_label.setFixedSize(350, 350)
        feature2_image_label.setAlignment(Qt.AlignCenter)
        feature2_layout.addWidget(feature2_image_label, alignment=Qt.AlignCenter)
        feature2_layout.addSpacing(10)
        feature2_layout.addWidget(feature2_label)
        feature2_layout.addStretch(1)
        feature2_widget.setLayout(feature2_layout)
        images_layout.addWidget(feature2_widget)

        # Isaac Sim 5.0.0 feature
        feature3_widget = QWidget()
        feature3_layout = QVBoxLayout()
        feature3_label = QLabel("Isaac Sim 5.0.0")
        feature3_label.setAlignment(Qt.AlignCenter)
        feature3_label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
        feature3_label.setStyleSheet("color: red;")
        feature3_image_label = QLabel()
        feature3_image_path = os.path.join(FUTURE_IMAGES_DIR, "isaacsim_500.png")
        if os.path.exists(feature3_image_path):
            pixmap = QPixmap(feature3_image_path).scaled(674, 1264, Qt.KeepAspectRatio)
            feature3_image_label.setPixmap(pixmap)
        else:
            feature3_image_label.setText("Future 3 image not found")
        feature3_image_label.setFixedSize(350, 350)
        feature3_image_label.setAlignment(Qt.AlignCenter)
        feature3_layout.addWidget(feature3_image_label, alignment=Qt.AlignCenter)
        feature3_layout.addSpacing(10)
        feature3_layout.addWidget(feature3_label)
        feature3_layout.addStretch(1)
        feature3_widget.setLayout(feature3_layout)
        images_layout.addWidget(feature3_widget)

        images_widget.setLayout(images_layout)
        layout.addWidget(images_widget, alignment=Qt.AlignCenter)
        layout.addStretch(1)
        self.setLayout(layout)

    def initializePage(self):
        # Set world manager and check initialization
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")

    def isComplete(self):
        # Check if world manager and world name are set
        return self.world_manager is not None and self.world_manager.world_name is not None