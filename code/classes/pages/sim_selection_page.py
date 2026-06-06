from PyQt5.QtWidgets import (
    QWizardPage, QLineEdit, QHBoxLayout, QVBoxLayout, QWidget,
    QLabel, QPushButton, QFrame, QSizePolicy,
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from utils.config import INTRO_IMAGES_DIR
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

_CARD_BASE = """
    QWidget {{
        background-color: {bg};
        border-radius: 10px;
        border: 2px solid {border};
    }}
"""

_BUTTON_ACTIVE = """
    QPushButton {
        background-color: #4A90E2;
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        font-size: 11pt;
        font-weight: bold;
        padding: 10px 20px;
        min-height: 40px;
    }
    QPushButton:hover { background-color: #3578C7; }
"""

_BUTTON_DISABLED = """
    QPushButton {
        background-color: #BDC3C7;
        color: #ECEFF1;
        border: none;
        border-radius: 6px;
        font-size: 11pt;
        font-weight: bold;
        padding: 10px 20px;
        min-height: 40px;
    }
"""


def _make_card(image_path, scale_w, scale_h, title_text, button_text,
               enabled=True, badge=None):
    """Return (card_widget, button)."""
    card = QWidget()
    card.setStyleSheet(
        _CARD_BASE.format(bg="#FFFFFF", border="#D5D8DC")
    )
    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    card.setMaximumHeight(440)
    vbox = QVBoxLayout(card)
    vbox.setContentsMargins(20, 16, 20, 16)
    vbox.setSpacing(10)

    img_label = _ScaledPixmapLabel()
    if os.path.exists(image_path):
        img_label.setSourcePixmap(QPixmap(image_path))
    else:
        img_label.setText("Image not found")
        img_label.setStyleSheet("color: #95A5A6;")
    vbox.addWidget(img_label, 1)  # stretch=1: image fills most of card

    title = QLabel(title_text)
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(
        "font-size: 15pt; font-weight: bold; color: #2C3E50; "
        "background-color: transparent; border: none;"
    )
    vbox.addWidget(title)

    if badge:
        badge_label = QLabel(badge)
        badge_label.setAlignment(Qt.AlignCenter)
        badge_label.setStyleSheet(
            "font-size: 11pt; color: #27AE60; "
            "background-color: transparent; border: none;"
        )
        vbox.addWidget(badge_label)

    btn = QPushButton(button_text)
    btn.setEnabled(enabled)
    btn.setStyleSheet(_BUTTON_ACTIVE if enabled else _BUTTON_DISABLED)
    vbox.addWidget(btn)

    return card, btn


class SimSelectionPage(QWizardPage):
    simulationSelected = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setTitle("Select Simulation Platform")
        self._simulation = ""
        self._gazebo_version = ""

        # Hidden fields for wizard validation
        self.simulation_field = QLineEdit()
        self.simulation_field.setVisible(False)
        self.gazebo_version_field = QLineEdit()
        self.gazebo_version_field.setVisible(False)
        self.registerField("simulation*", self.simulation_field)
        self.registerField("gazebo_version", self.gazebo_version_field)

        # ── Page header ────────────────────────────────────────────
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(30, 20, 30, 20)
        root_layout.setSpacing(16)

        header = QLabel("Choose a simulation backend to continue")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 13pt; color: #7F8C8D;")
        root_layout.addWidget(header)

        # ── Cards row ──────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)

        # Ionic card
        ionic_img = os.path.join(INTRO_IMAGES_DIR, "ionic.png")
        ionic_card, self.ionic_button = _make_card(
            ionic_img, 220, 220,
            "Gazebo Ionic",
            "Select Ionic",
            enabled=True,
        )
        self.ionic_button.clicked.connect(
            lambda: self.select_gazebo_version("ionic"))
        cards_row.addWidget(ionic_card)

        # Vertical divider
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setFrameShadow(QFrame.Sunken)
        div.setStyleSheet("color: #D5D8DC;")
        cards_row.addWidget(div)

        # Harmonic card
        harmonic_img = os.path.join(INTRO_IMAGES_DIR, "harmonic.png")
        harmonic_card, self.harmonic_button = _make_card(
            harmonic_img, 220, 220,
            "Gazebo Harmonic",
            "Select Harmonic",
            enabled=True,
            badge="★ Recommended",
        )
        self.harmonic_button.clicked.connect(
            lambda: self.select_gazebo_version("harmonic"))
        cards_row.addWidget(harmonic_card)

        # Vertical divider
        div2 = QFrame()
        div2.setFrameShape(QFrame.VLine)
        div2.setFrameShadow(QFrame.Sunken)
        div2.setStyleSheet("color: #D5D8DC;")
        cards_row.addWidget(div2)

        # Fortress card
        fortress_img = os.path.join(INTRO_IMAGES_DIR, "fortress.jpeg")
        fortress_card, self.fortress_button = _make_card(
            fortress_img, 220, 220,
            "Gazebo Fortress",
            "Select Fortress",
            enabled=True,
        )
        self.fortress_button.clicked.connect(
            lambda: self.select_gazebo_version("fortress"))
        cards_row.addWidget(fortress_card)

        root_layout.addStretch(1)
        root_layout.addLayout(cards_row)
        root_layout.addStretch(1)

        # Selection status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 12pt; color: #27AE60; font-weight: bold;"
        )
        root_layout.addWidget(self.status_label)

    # ── Card highlight helper ──────────────────────────────────────────────

    def _highlight_card(self, selected_btn):
        for btn in (self.ionic_button, self.harmonic_button, self.fortress_button):
            is_selected = (btn is selected_btn)
            parent = btn.parent()
            parent.setStyleSheet(
                _CARD_BASE.format(
                    bg="#EBF3FB" if is_selected else "#FFFFFF",
                    border="#4A90E2" if is_selected else "#D5D8DC",
                )
            )

    # ── Selection ──────────────────────────────────────────────────────────

    def select_gazebo_version(self, version):
        self._simulation = "gazebo"
        self._gazebo_version = version
        self.simulation_field.setText("gazebo")
        self.gazebo_version_field.setText(version)
        self.simulationSelected.emit("gazebo", version)
        btn_map = {
            "ionic": self.ionic_button,
            "harmonic": self.harmonic_button,
            "fortress": self.fortress_button,
        }
        self._highlight_card(btn_map[version])
        self.status_label.setText(f"✔  Gazebo {version.capitalize()} selected")
        self.completeChanged.emit()

    def isComplete(self):
        return self._simulation == "gazebo" and self._gazebo_version in ("fortress", "harmonic", "ionic")
