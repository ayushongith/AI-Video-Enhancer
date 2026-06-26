import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal, QSize

from app.utils.constants import (
    COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_DISPLAY, FONT_BODY, FONT_MONO, COLOR_ERROR,
)
from app.core.history_manager import HistoryEntry

logger = logging.getLogger(__name__)


class _HistoryCard(QFrame):
    clicked = Signal(str)

    def __init__(self, entry: HistoryEntry, parent=None) -> None:
        super().__init__(parent)
        self._entry = entry
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            f"background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 10px; padding: 14px 18px;"
        )
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        top = QHBoxLayout()
        name = QLabel(self._entry.filename)
        name.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 13px; font-weight: 600; "
            f"font-family: {FONT_BODY}; background: transparent;"
        )
        top.addWidget(name)

        badge = QLabel(self._entry.timestamp.split()[0] if self._entry.timestamp else "")
        badge.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 10px; font-family: {FONT_MONO}; "
            f"background-color: {COLOR_ELEVATED}; border-radius: 4px; "
            f"padding: 2px 8px;"
        )
        top.addWidget(badge)
        top.addStretch()
        layout.addLayout(top)

        detail = QHBoxLayout()
        detail.setSpacing(16)

        if self._entry.source_resolution:
            detail.addWidget(_detail_label(f"In: {self._entry.source_resolution}"))
        if self._entry.output_resolution:
            detail.addWidget(_detail_label(f"Out: {self._entry.output_resolution}"))
        if self._entry.duration_s:
            mins = int(self._entry.duration_s) // 60
            secs = int(self._entry.duration_s) % 60
            detail.addWidget(_detail_label(f"{mins}:{secs:02d}"))

        detail.addStretch()
        layout.addLayout(detail)

    def mousePressEvent(self, event) -> None:
        if self._entry.output_path:
            self.clicked.emit(self._entry.output_path)


def _detail_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {COLOR_MUTED}; font-size: 11px; font-family: {FONT_MONO}; "
        f"background: transparent;"
    )
    return lbl


class HistoryScreen(QWidget):
    open_result = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._list: Optional[QListWidget] = None
        self._empty_label: Optional[QLabel] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Processing History")
        title.setStyleSheet(
            f"font-family: {FONT_DISPLAY}; font-size: 24px; font-weight: 700; "
            f"color: {COLOR_TEXT}; background: transparent; letter-spacing: -0.3px;"
        )
        header.addWidget(title)

        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedHeight(32)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: transparent; color: {COLOR_MUTED};"
            f"  border: 1px solid {COLOR_BORDER}; border-radius: 6px;"
            f"  font-size: 11px; font-family: {FONT_BODY}; padding: 0 14px;"
            f"}}"
            f"QPushButton:hover {{ color: {COLOR_ERROR}; border-color: {COLOR_ERROR}; }}"
        )
        clear_btn.clicked.connect(self._on_clear)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        self._list = QListWidget()
        self._list.setFrameShape(QFrame.NoFrame)
        self._list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self._list.setSpacing(8)
        self._list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; }}"
        )
        layout.addWidget(self._list, stretch=1)

        self._empty_label = QLabel("No processing history yet.\nComplete an enhancement to see it here.")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 13px; font-family: {FONT_BODY}; "
            f"background: transparent; padding: 40px;"
        )
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)

    def load_entries(self, entries: list[HistoryEntry]) -> None:
        self._list.clear()
        if not entries:
            self._empty_label.setVisible(True)
            self._list.setVisible(False)
            return

        self._empty_label.setVisible(False)
        self._list.setVisible(True)
        for entry in entries:
            item = QListWidgetItem()
            card = _HistoryCard(entry)
            card.clicked.connect(self.open_result.emit)
            item.setSizeHint(card.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, card)

    def _on_clear(self) -> None:
        self._list.clear()
        self._empty_label.setVisible(True)
        self._list.setVisible(False)
