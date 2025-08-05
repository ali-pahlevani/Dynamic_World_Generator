from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QLabel
from PyQt5.QtGui import QMovie
import os

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to the Dynamic World Generator Wizard!")

        layout = QVBoxLayout()

        title_label = QLabel("Welcome to the Dynamic World Generator Wizard!")
        title_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        layout.addWidget(title_label)

        # Construct the path to welcome.gif
        gif_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "images", "intro", "welcome.gif")
        print(f"Looking for GIF at: {gif_path}")  # Debug to verify path

        gif_label = QLabel()
        movie = QMovie(gif_path)
        if movie.isValid():
            gif_label.setMovie(movie)
            movie.start()
        else:
            gif_label.setText(f"Preview GIF not found at {gif_path}")
        layout.addWidget(gif_label)

        self.setLayout(layout)