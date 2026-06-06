from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QSize
from utils.config import INTRO_IMAGES_DIR
import os

# Native resolution of welcome.gif
_GIF_W, _GIF_H = 880, 520


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self._movie = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(12)

        title = QLabel("Welcome to the Dynamic World Generator")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
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
        self._gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        movie = QMovie(gif_path)
        if movie.isValid():
            self._movie = movie
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale_gif()

    def showEvent(self, event):
        super().showEvent(event)
        self._rescale_gif()

    def _rescale_gif(self):
        if not self._movie:
            return
        w = self._gif_label.width()
        h = self._gif_label.height()
        if w < 10 or h < 10:
            return
        ratio = min(w / _GIF_W, h / _GIF_H)
        self._movie.setScaledSize(QSize(max(int(_GIF_W * ratio), 100),
                                        max(int(_GIF_H * ratio), 60)))
