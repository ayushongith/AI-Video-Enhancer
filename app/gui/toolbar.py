import logging
from PySide6.QtWidgets import QToolBar, QPushButton, QWidget, QSizePolicy, QLabel
from PySide6.QtCore import Signal, Qt

from app.utils.constants import (
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_MUTED,
    COLOR_BORDER, COLOR_SURFACE, COLOR_BG, FONT_BODY,
)

logger = logging.getLogger(__name__)


class MainToolbar(QToolBar):
    open_clicked = Signal()
    settings_clicked = Signal()
    about_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__("Main Toolbar", parent)
        self.setMovable(False)
        self._setup_ui()

    def _setup_ui(self) -> None:
        open_btn = QPushButton("\u25B6  Open Video")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(self.open_clicked.emit)
        open_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 {COLOR_ACCENT}, stop:1 #7c5cff);"
            f"  color: #ffffff; border: none; border-radius: 8px;"
            f"  font-family: {FONT_BODY}; font-size: 12px; font-weight: 600;"
            f"  padding: 6px 18px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 {COLOR_ACCENT_HOVER}, stop:1 {COLOR_ACCENT});"
            f"}}"
        )
        self.addWidget(open_btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)

        settings_btn = QPushButton("\u2699")
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setFixedSize(32, 32)
        settings_btn.clicked.connect(self.settings_clicked.emit)
        settings_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent; color: {COLOR_MUTED};"
            f"  border: none; border-radius: 6px; font-size: 16px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {COLOR_SURFACE}; color: {COLOR_TEXT};"
            f"}}"
        )
        self.addWidget(settings_btn)

        about_btn = QPushButton("?")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.setFixedSize(32, 32)
        about_btn.clicked.connect(self.about_clicked.emit)
        about_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent; color: {COLOR_MUTED};"
            f"  border: none; border-radius: 6px; font-size: 14px; font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {COLOR_SURFACE}; color: {COLOR_TEXT};"
            f"}}"
        )
        self.addWidget(about_btn)
