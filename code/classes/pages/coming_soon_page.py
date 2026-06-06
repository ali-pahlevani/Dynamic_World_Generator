from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
from utils.config import FUTURE_IMAGES_DIR
import os


class ComingSoonPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Coming Soon")
        self.world_manager = None

        layout = QVBoxLayout()
        layout.addStretch(1)

        images_widget = QWidget()
        images_layout = QHBoxLayout()
        images_layout.setSpacing(20)

        def make_feature(label_text, image_path, scale_w, scale_h):
            widget = QWidget()
            vbox = QVBoxLayout()
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignCenter)
            label.setFont(QFont("Arial", 18, QFont.Bold | QFont.StyleItalic))
            label.setStyleSheet("color: red;")
            img_label = QLabel()
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path).scaled(scale_w, scale_h, Qt.KeepAspectRatio)
                img_label.setPixmap(pixmap)
            else:
                img_label.setText(f"Image not found: {os.path.basename(image_path)}")
            img_label.setFixedSize(350, 350)
            img_label.setAlignment(Qt.AlignCenter)
            vbox.addWidget(img_label, alignment=Qt.AlignCenter)
            vbox.addSpacing(10)
            vbox.addWidget(label)
            vbox.addStretch(1)
            widget.setLayout(vbox)
            return widget

        images_layout.addWidget(make_feature(
            "Gazebo Ionic",
            os.path.join(FUTURE_IMAGES_DIR, "ionic.png"),
            350, 350
        ))
        images_layout.addWidget(make_feature(
            "Isaac Sim 4.5.0",
            os.path.join(FUTURE_IMAGES_DIR, "isaacsim_450.png"),
            674, 1264
        ))
        images_layout.addWidget(make_feature(
            "Isaac Sim 5.0.0",
            os.path.join(FUTURE_IMAGES_DIR, "isaacsim_500.png"),
            674, 1264
        ))

        images_widget.setLayout(images_layout)
        layout.addWidget(images_widget, alignment=Qt.AlignCenter)
        layout.addStretch(1)
        self.setLayout(layout)

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None
