#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from classes.dynamic_world_wizard import DynamicWorldWizard

# ── Palette ────────────────────────────────────────────────────────────────
# BG_PAGE  #F4F6F9   light page background
# BG_WHITE #FFFFFF   input / list background
# ACCENT   #4A90E2   primary blue
# SUCCESS  #27AE60   green for Apply / Finish / Next
# DANGER   #E74C3C   red for Remove
# TEXT     #2C3E50   primary text
# MUTED    #7F8C8D   secondary / placeholder text
# BORDER   #C8D0DA   default border
# ──────────────────────────────────────────────────────────────────────────
APP_STYLESHEET = """
/* ── Base ── */
QWizard, QWizardPage {
    background-color: #F4F6F9;
    color: #2C3E50;
    font-family: Arial;
    font-size: 11pt;
}

/* ── Buttons – default (blue) ── */
QPushButton {
    background-color: #4A90E2;
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 7px 18px;
    font-size: 10pt;
    font-weight: bold;
    min-height: 34px;
    min-width: 80px;
}
QPushButton:hover  { background-color: #3578C7; }
QPushButton:pressed{ background-color: #2A62A8; }
QPushButton:disabled {
    background-color: #C8D0DA;
    color: #F4F6F9;
}

/* Remove / danger */
QPushButton[btnRole="danger"] {
    background-color: #E74C3C;
}
QPushButton[btnRole="danger"]:hover  { background-color: #C0392B; }
QPushButton[btnRole="danger"]:pressed{ background-color: #A93226; }

/* Apply / success */
QPushButton[btnRole="success"] {
    background-color: #27AE60;
}
QPushButton[btnRole="success"]:hover  { background-color: #1E8449; }
QPushButton[btnRole="success"]:pressed{ background-color: #186A3B; }

/* Secondary (Back button) */
QPushButton[btnRole="secondary"] {
    background-color: #ECF0F1;
    color: #2C3E50;
    border: 1.5px solid #BDC3C7;
}
QPushButton[btnRole="secondary"]:hover  { background-color: #D5D8DC; }
QPushButton[btnRole="secondary"]:pressed{ background-color: #C0C6CB; }
QPushButton[btnRole="secondary"]:disabled {
    background-color: #F0F0F0;
    color: #A0A0A0;
    border-color: #D0D0D0;
}

/* Cancel */
QPushButton[btnRole="cancel"] {
    background-color: transparent;
    color: #7F8C8D;
    border: 1.5px solid #C8D0DA;
}
QPushButton[btnRole="cancel"]:hover {
    background-color: #FDECEA;
    color: #E74C3C;
    border-color: #E74C3C;
}

/* ── Inputs ── */
QLineEdit {
    background-color: #FFFFFF;
    color: #2C3E50;
    border: 1.5px solid #C8D0DA;
    border-radius: 4px;
    padding: 5px 9px;
    font-size: 10pt;
    min-height: 30px;
    selection-background-color: #4A90E2;
    selection-color: #FFFFFF;
}
QLineEdit:focus   { border-color: #4A90E2; }
QLineEdit:disabled{
    background-color: #EAECEE;
    color: #95A5A6;
    border-color: #D5D8DC;
}

/* ── ComboBox ── */
QComboBox {
    background-color: #FFFFFF;
    color: #2C3E50;
    border: 1.5px solid #C8D0DA;
    border-radius: 4px;
    padding: 5px 9px;
    font-size: 10pt;
    min-height: 30px;
}
QComboBox:focus { border-color: #4A90E2; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #C8D0DA;
    selection-background-color: #4A90E2;
    selection-color: #FFFFFF;
    outline: none;
}

/* ── ListWidget ── */
QListWidget {
    background-color: #FFFFFF;
    color: #2C3E50;
    border: 1.5px solid #C8D0DA;
    border-radius: 4px;
    font-size: 10pt;
    outline: none;
}
QListWidget::item { padding: 6px 10px; }
QListWidget::item:selected {
    background-color: #4A90E2;
    color: #FFFFFF;
}
QListWidget::item:hover:!selected {
    background-color: #EBF3FB;
}

/* ── GroupBox ── */
QGroupBox {
    border: 1.5px solid #D5D8DC;
    border-radius: 6px;
    margin-top: 16px;
    padding: 10px 8px 8px 8px;
    font-size: 9pt;
    font-weight: bold;
    color: #2C3E50;
    background-color: #FFFFFF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 1px 5px;
    background-color: #FFFFFF;
    color: #4A90E2;
    font-size: 9pt;
}

/* ── Labels ── */
QLabel {
    color: #2C3E50;
    background-color: transparent;
    font-size: 10pt;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: #F4F6F9;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #BDC3C7;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #95A5A6; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #F4F6F9;
    height: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #BDC3C7;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #95A5A6; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Separators ── */
QFrame[frameShape="4"] { color: #D5D8DC; }
QFrame[frameShape="5"] { color: #D5D8DC; }

/* ── MessageBox ── */
QMessageBox { background-color: #FFFFFF; }
QMessageBox QLabel { font-size: 11pt; }
"""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 11))
    app.setStyleSheet(APP_STYLESHEET)
    wizard = DynamicWorldWizard()
    wizard.show()
    sys.exit(app.exec_())
