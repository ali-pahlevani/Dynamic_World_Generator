from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QLabel
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QSize
from utils.config import INTRO_IMAGES_DIR
import os

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Let's make a 'Dynamic World' together!")

        # Main layout for vertical centering
        main_layout = QVBoxLayout()
        main_layout.addStretch(1)  # Stretch above to center vertically

        # Nested layout for title and GIF
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)  # Preserve 10-pixel spacing between title and GIF

        title_label = QLabel("Welcome to the Dynamic World Generator Wizard!")
        title_label.setStyleSheet("font-size: 26pt; font-weight: bold; color: red;")
        title_label.setAlignment(Qt.AlignCenter)  # Center horizontally
        content_layout.addWidget(title_label)

        gif_path = os.path.join(INTRO_IMAGES_DIR, "welcome.gif")
        print(f"Looking for GIF at: {gif_path}")

        gif_label = QLabel()
        movie = QMovie(gif_path)
        if movie.isValid():
            movie.setScaledSize(QSize(1200, 750))  # Set GIF size to 1200x750 pixels
            gif_label.setMovie(movie)
            movie.start()
        else:
            gif_label.setText(f"Preview GIF not found at {gif_path}")
        gif_label.setAlignment(Qt.AlignCenter)  # Center horizontally
        content_layout.addWidget(gif_label)

        main_layout.addLayout(content_layout)
        main_layout.addStretch(1)  # Stretch below to center vertically

        self.setLayout(main_layout)