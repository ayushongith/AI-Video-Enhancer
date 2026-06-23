import logging
from typing import Optional

import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient

from app.utils.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_DISPLAY, FONT_BODY, FONT_MONO, COLOR_SUCCESS, COLOR_ERROR,
)
from app.core.video_loader import VideoMetadata
from app.gui.widgets.comparison_view import ComparisonView

logger = logging.getLogger(__name__)


class _MetaRow(QFrame):
    def __init__(self, label: str, before: str, after: str, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 8px; padding: 10px 16px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        label_w = QLabel(label)
        label_w.setFixedWidth(100)
        label_w.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 11px; font-weight: 500; "
            f"font-family: {FONT_BODY}; background: transparent;"
        )
        layout.addWidget(label_w)

        before_w = QLabel(before)
        before_w.setAlignment(Qt.AlignCenter)
        before_w.setStyleSheet(
            f"color: #6b7280; font-size: 12px; font-family: {FONT_MONO}; "
            f"background-color: #0a0a14; border-radius: 4px; padding: 4px 8px;"
        )
        layout.addWidget(before_w, 1)

        arrow = QLabel("\u2192")
        arrow.setStyleSheet(
            f"color: {COLOR_ACCENT}; font-size: 14px; background: transparent;"
        )
        arrow.setFixedWidth(24)
        arrow.setAlignment(Qt.AlignCenter)
        layout.addWidget(arrow)

        after_w = QLabel(after)
        after_w.setAlignment(Qt.AlignCenter)
        after_w.setStyleSheet(
            f"color: {COLOR_SUCCESS}; font-size: 12px; font-family: {FONT_MONO}; "
            f"background-color: #0a1a10; border-radius: 4px; padding: 4px 8px;"
        )
        layout.addWidget(after_w, 1)


class _ModeButton(QPushButton):
    def __init__(self, text: str, mode: int, parent=None) -> None:
        super().__init__(text, parent)
        self._mode = mode
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(32)
        self.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {COLOR_MUTED};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 6px;"
            f"  font-family: {FONT_BODY}; font-size: 11px; font-weight: 500;"
            f"  padding: 0 14px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  color: {COLOR_TEXT};"
            f"  border-color: {COLOR_ACCENT};"
            f"}}"
            f"QPushButton:checked {{"
            f"  background-color: {COLOR_ACCENT};"
            f"  color: #ffffff;"
            f"  border-color: {COLOR_ACCENT};"
            f"}}"
        )


class ResultScreen(QWidget):
    upscale_another = Signal()
    download_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._comparison: Optional[ComparisonView] = None
        self._mode_btns: list[_ModeButton] = []
        self._meta_rows: list[_MetaRow] = []
        self._meta_frame: Optional[QFrame] = None
        self._before_frame: Optional[np.ndarray] = None
        self._after_frame: Optional[np.ndarray] = None
        self._output_path: Optional[str] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 24, 48, 24)
        layout.setSpacing(16)

        header = QLabel("Comparison")
        header.setStyleSheet(
            f"font-family: {FONT_DISPLAY}; font-size: 24px; font-weight: 700; "
            f"color: {COLOR_TEXT}; background: transparent; letter-spacing: -0.3px;"
        )
        layout.addWidget(header)

        self._comparison = ComparisonView()
        self._comparison.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._comparison, stretch=1)

        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        mode_label = QLabel("View:")
        mode_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 11px; font-weight: 500; "
            f"background: transparent;"
        )
        mode_layout.addWidget(mode_label)

        modes = [
            ("Slider", ComparisonView.MODE_SLIDER),
            ("Side by Side", ComparisonView.MODE_SIDE_BY_SIDE),
            ("Overlay", ComparisonView.MODE_OVERLAY),
        ]
        for text, mode in modes:
            btn = _ModeButton(text, mode)
            btn.clicked.connect(lambda checked, m=mode: self._on_mode_changed(m))
            self._mode_btns.append(btn)
            mode_layout.addWidget(btn)

        self._mode_btns[0].setChecked(True)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        self._meta_frame = QFrame()
        self._meta_frame.setStyleSheet(
            f"background-color: transparent; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 12px; padding: 16px;"
        )
        meta_layout = QVBoxLayout(self._meta_frame)
        meta_layout.setSpacing(8)
        meta_layout.setContentsMargins(16, 16, 16, 16)

        meta_title = QLabel("METADATA COMPARISON")
        meta_title.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 1.2px; background: transparent;"
        )
        meta_layout.addWidget(meta_title)

        rows = [
            ("Resolution", "854x480", "3840x2160"),
            ("Bitrate", "2.1 Mbps", "18.4 Mbps"),
            ("File size", "48 MB", "312 MB"),
        ]
        for label, before, after in rows:
            row = _MetaRow(label, before, after)
            self._meta_rows.append(row)
            meta_layout.addWidget(row)

        layout.addWidget(self._meta_frame)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        download_btn = QPushButton("Download Upscaled Video")
        download_btn.setCursor(Qt.PointingHandCursor)
        download_btn.setFixedHeight(46)
        download_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 {COLOR_ACCENT}, stop:1 {COLOR_ACCENT_HOVER});"
            f"  color: #ffffff; border: none; border-radius: 23px;"
            f"  font-family: {FONT_BODY}; font-size: 14px; font-weight: 600;"
            f"  padding: 0 32px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 {COLOR_ACCENT_HOVER}, stop:1 #c4b5fd);"
            f"}}"
        )
        download_btn.clicked.connect(self._on_download)
        btn_layout.addWidget(download_btn)

        again_btn = QPushButton("Upscale Another")
        again_btn.setCursor(Qt.PointingHandCursor)
        again_btn.setFixedHeight(46)
        again_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {COLOR_MUTED};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 23px;"
            f"  font-family: {FONT_BODY}; font-size: 13px; font-weight: 500;"
            f"  padding: 0 24px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  color: {COLOR_TEXT};"
            f"  border-color: {COLOR_MUTED};"
            f"}}"
        )
        again_btn.clicked.connect(self.upscale_another.emit)
        btn_layout.addWidget(again_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _on_mode_changed(self, mode: int) -> None:
        if self._comparison:
            self._comparison.set_mode(mode)
        for btn in self._mode_btns:
            btn.setChecked(btn._mode == mode)

    def set_output_path(self, path: str) -> None:
        self._output_path = path

    def _on_download(self) -> None:
        if self._output_path:
            self.download_requested.emit(self._output_path)

    def show_comparison(
        self,
        before_frame: Optional[np.ndarray],
        after_frame: Optional[np.ndarray],
    ) -> None:
        self._before_frame = before_frame
        self._after_frame = after_frame
        if self._comparison:
            self._comparison.set_frames(before_frame, after_frame)

    def set_metadata(self, rows: list[tuple[str, str, str]]) -> None:
        meta_layout = self._meta_frame.layout()
        for old_row in self._meta_rows:
            meta_layout.removeWidget(old_row)
            old_row.deleteLater()
        self._meta_rows.clear()

        for label, before, after in rows:
            row = _MetaRow(label, before, after)
            self._meta_rows.append(row)
            meta_layout.addWidget(row)
