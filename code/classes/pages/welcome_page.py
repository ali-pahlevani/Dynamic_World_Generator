from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QLabel
from PyQt5.QtGui import QMovie, QFont
from PyQt5.QtCore import Qt, QSize
from utils.config import INTRO_IMAGES_DIR
import os


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")  # title rendered in content, not wizard banner

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(12)

        title = QLabel("Welcome to the Dynamic World Generator")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 22pt; font-weight: bold; color: #2C3E50;"
        )
        layout.addWidget(title)

        subtitle = QLabel("Design simulation worlds with static and dynamic obstacles — visually, step by step.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12pt; color: #7F8C8D;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        gif_path = os.path.join(INTRO_IMAGES_DIR, "welcome.gif")
        self._gif_label = QLabel()
        self._gif_label.setAlignment(Qt.AlignCenter)
        movie = QMovie(gif_path)
        if movie.isValid():
            # Scale to fit comfortably; actual canvas is ~1350 × 700 px at 1600×860
            movie.setScaledSize(QSize(880, 520))
            self._gif_label.setMovie(movie)
            movie.start()
        else:
            self._gif_label.setText("(Preview animation not found)")
            self._gif_label.setStyleSheet("color: #95A5A6; font-size: 12pt;")
        layout.addWidget(self._gif_label, 1)

        footer = QLabel("Press  Next  to get started →")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 10pt; color: #95A5A6;")
        layout.addWidget(footer)
