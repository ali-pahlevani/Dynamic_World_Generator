from PyQt5.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox,
    QSizePolicy,
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QSize
from utils.config import FUTURE_IMAGES_DIR
import os


class _ScaledPixmapLabel(QLabel):
    """QLabel that rescales its pixmap to fill available space on every resize."""
    def __init__(self):
        super().__init__()
        self._source = None
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(80)

    def setSourcePixmap(self, pixmap):
        self._source = pixmap
        self._refresh()

    def sizeHint(self):
        return QSize(280, 260)

    def minimumSizeHint(self):
        return QSize(80, 100)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self):
        if self._source and self.width() > 0 and self.height() > 0:
            scaled = self._source.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            super().setPixmap(scaled)


def _feature_card(image_path, scale_w, scale_h, title_text, badge=None):
    card = QWidget()
    card.setStyleSheet("""
        QWidget {
            background-color: #FFFFFF;
            border: 1.5px solid #D5D8DC;
            border-radius: 10px;
        }
    """)
    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    card.setMaximumHeight(400)

    vbox = QVBoxLayout(card)
    vbox.setContentsMargins(20, 16, 20, 16)
    vbox.setSpacing(10)

    img_label = _ScaledPixmapLabel()
    if os.path.exists(image_path):
        img_label.setSourcePixmap(QPixmap(image_path))
    else:
        img_label.setText("Image not found")
        img_label.setStyleSheet("color: #95A5A6; border: none;")
    vbox.addWidget(img_label, 1)  # stretch=1: image fills most of card

    title = QLabel(title_text)
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(
        "font-size: 13pt; font-weight: bold; color: #2C3E50; "
        "border: none; background-color: transparent;"
    )
    vbox.addWidget(title)

    if badge:
        b = QLabel(badge)
        b.setAlignment(Qt.AlignCenter)
        b.setStyleSheet(
            "font-size: 9pt; color: #FFFFFF; background-color: #E67E22; "
            "border-radius: 4px; padding: 3px 10px; border: none;"
        )
        vbox.addWidget(b)

    return card


class ComingSoonPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Coming Soon")
        self.world_manager = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        header = QLabel("What's next for DWG Wizard")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2C3E50;")
        layout.addWidget(header)

        sub = QLabel("These simulation platforms and features are currently under development.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 11pt; color: #7F8C8D;")
        layout.addWidget(sub)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)
        cards_row.addWidget(_feature_card(
            os.path.join(FUTURE_IMAGES_DIR, "isaacsim_450.png"),
            300, 260, "Isaac Sim 4.5.0", badge="In Progress"
        ))
        cards_row.addWidget(_feature_card(
            os.path.join(FUTURE_IMAGES_DIR, "isaacsim_500.png"),
            300, 260, "Isaac Sim 5.0.0", badge="Planned"
        ))
        cards_row.addWidget(_feature_card(
            os.path.join(FUTURE_IMAGES_DIR, "isaacsim_510.png"),
            300, 260, "Isaac Sim 5.1.0", badge="Planned"
        ))
        layout.addStretch(1)
        layout.addLayout(cards_row)
        layout.addStretch(1)

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Notice",
                                "No world loaded — this page is for preview only.")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None
