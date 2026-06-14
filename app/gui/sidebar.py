import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QButtonGroup,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QFont

from app.utils.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_TEXT, COLOR_MUTED, COLOR_BORDER, FONT_DISPLAY, FONT_BODY,
    FONT_MONO,
)

logger = logging.getLogger(__name__)

NAV_ITEMS = [
    ("Home", "\u2302"),
    ("Enhance", "\u2728"),
    ("Export", "\u2913"),
]


class Sidebar(QWidget):
    navigation_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._buttons: list[QPushButton] = []
        self._button_group: Optional[QButtonGroup] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFixedWidth(200)
        self.setStyleSheet(
            f"background-color: {COLOR_SURFACE}; "
            f"border-right: 1px solid {COLOR_BORDER};"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(72)
        header.setStyleSheet(f"background-color: transparent; border: none;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(2)

        title = QLabel("AI Video\nEnhancer")
        title.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 16px; font-weight: 700; "
            f"font-family: {FONT_DISPLAY}; background: transparent; "
            f"letter-spacing: -0.2px; line-height: 1.2;"
        )
        header_layout.addWidget(title)

        subtitle = QLabel("Professional Edition")
        subtitle.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 10px; font-weight: 400; "
            f"font-family: {FONT_BODY}; background: transparent;"
        )
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        spacer = QFrame()
        spacer.setFixedHeight(1)
        spacer.setStyleSheet(f"background-color: {COLOR_BORDER}; border: none;")
        layout.addWidget(spacer)

        nav_container = QWidget()
        nav_container.setStyleSheet("background-color: transparent;")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(2)

        section = QLabel("NAVIGATION")
        section.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 9px; font-weight: 600; "
            f"letter-spacing: 1.2px; font-family: {FONT_BODY}; "
            f"background: transparent; padding: 4px 12px;"
        )
        nav_layout.addWidget(section)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._button_group.idClicked.connect(self._on_button_clicked)

        for i, (item_text, icon) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  {icon}   {item_text}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: transparent;"
                f"  color: {COLOR_MUTED};"
                f"  border: none;"
                f"  border-radius: 8px;"
                f"  font-family: {FONT_BODY}; font-size: 13px; font-weight: 500;"
                f"  text-align: left;"
                f"  padding: 0 12px;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background-color: {COLOR_ELEVATED};"
                f"  color: {COLOR_TEXT};"
                f"}}"
                f"QPushButton:checked {{"
                f"  background-color: #1a1a40;"
                f"  color: {COLOR_ACCENT};"
                f"}}"
            )
            self._button_group.addButton(btn, i)
            self._buttons.append(btn)
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        layout.addWidget(nav_container, stretch=1)

        bottom_frame = QFrame()
        bottom_frame.setStyleSheet(
            f"background-color: transparent; "
            f"border-top: 1px solid {COLOR_BORDER};"
        )
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(16, 10, 16, 10)

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 10px; font-family: {FONT_MONO}; "
            f"background: transparent;"
        )
        version_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(version_label)

        layout.addWidget(bottom_frame)

        if self._buttons:
            self._buttons[0].setChecked(True)

    def _on_button_clicked(self, button_id: int) -> None:
        if 0 <= button_id < len(NAV_ITEMS):
            self.navigation_changed.emit(NAV_ITEMS[button_id][0])

    def select_item(self, index: int) -> None:
        if self._button_group and 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)
