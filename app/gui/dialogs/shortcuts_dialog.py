import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.utils.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
)

logger = logging.getLogger(__name__)

SHORTCUTS = [
    ("Ctrl+O", "Open video file"),
    ("Ctrl+S", "Open settings panel"),
    ("Space", "Play / Pause preview"),
    ("Ctrl+E", "Start enhancement"),
    ("Ctrl+B", "Open batch processing"),
    ("Ctrl+D", "Export / download result"),
    ("Escape", "Cancel / go home"),
    ("Ctrl+Q", "Quit application"),
    ("F11", "Toggle fullscreen"),
    ("?", "Show this help"),
]


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setFixedSize(420, 420)
        self.setStyleSheet(
            f"QDialog {{ background-color: {COLOR_BG}; }}"
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet(
            f"font-family: {FONT_DISPLAY}; font-size: 18px; font-weight: 700; "
            f"color: {COLOR_TEXT}; background: transparent;"
        )
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(16)

        for row, (key, desc) in enumerate(SHORTCUTS):
            key_label = QLabel(key)
            key_label.setStyleSheet(
                f"background-color: {COLOR_ELEVATED}; color: {COLOR_ACCENT}; "
                f"font-family: {FONT_MONO}; font-size: 11px; font-weight: 600; "
                f"padding: 4px 10px; border-radius: 4px;"
            )
            key_label.setAlignment(Qt.AlignCenter)
            key_label.setFixedWidth(90)
            grid.addWidget(key_label, row, 0)

            desc_label = QLabel(desc)
            desc_label.setStyleSheet(
                f"color: {COLOR_TEXT}; font-family: {FONT_BODY}; font-size: 12px; "
                f"background: transparent;"
            )
            grid.addWidget(desc_label, row, 1)

        layout.addLayout(grid)
        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {COLOR_SURFACE}; color: {COLOR_TEXT};"
            f"  border: 1px solid {COLOR_BORDER}; border-radius: 8px;"
            f"  font-family: {FONT_BODY}; font-size: 12px; padding: 8px 24px;"
            f"}}"
            f"QPushButton:hover {{ background-color: {COLOR_ELEVATED}; }}"
        )
        layout.addWidget(close_btn, 0, Qt.AlignCenter)
