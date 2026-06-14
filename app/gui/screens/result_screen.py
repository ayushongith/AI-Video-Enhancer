import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QLinearGradient,
)

from app.utils.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_DISPLAY, FONT_BODY, FONT_MONO, COLOR_SUCCESS, COLOR_ERROR,
)
from app.core.video_loader import VideoMetadata

logger = logging.getLogger(__name__)


class CompareSlider(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(240)
        self.setMinimumWidth(400)
        self.setCursor(Qt.SplitHCursor)
        self.setMouseTracking(True)
        self._split_pos: float = 0.5
        self._dragging: bool = False

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        split_x = int(w * self._split_pos)

        left_rect = QRect(0, 0, split_x, h)
        p.save()
        p.setClipRect(left_rect)
        p.fillRect(left_rect, QColor("#0d0d15"))
        p.setFont(QFont(FONT_MONO.split(",")[0].strip(), 10))
        p.setPen(QColor(COLOR_MUTED))
        p.drawText(left_rect.adjusted(16, 0, -16, -12), Qt.AlignLeft | Qt.AlignBottom, "ORIGINAL")
        p.setFont(QFont(FONT_DISPLAY.split(",")[0].strip(), 14, QFont.Bold))
        p.setPen(QColor("#2a2a3a"))
        p.drawText(left_rect, Qt.AlignCenter, "854x480")
        for y in range(0, h, 3):
            p.setPen(QColor(255, 255, 255, 4))
            p.drawLine(0, y, split_x, y)
        p.restore()

        right_rect = QRect(split_x, 0, w - split_x, h)
        p.save()
        p.setClipRect(right_rect)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(COLOR_SURFACE).lighter(108))
        grad.setColorAt(1.0, QColor(COLOR_SURFACE))
        p.fillRect(right_rect, grad)
        p.setFont(QFont(FONT_MONO.split(",")[0].strip(), 10))
        p.setPen(QColor(COLOR_ACCENT_HOVER))
        p.drawText(right_rect.adjusted(16, 0, -16, -12), Qt.AlignLeft | Qt.AlignBottom, "UPSCALED")
        p.setFont(QFont(FONT_DISPLAY.split(",")[0].strip(), 14, QFont.Bold))
        p.setPen(QColor(COLOR_ACCENT).lighter(130))
        p.drawText(right_rect, Qt.AlignCenter, "3840x2160")
        p.restore()

        p.setPen(QPen(QColor(COLOR_ACCENT), 2))
        p.drawLine(split_x, 0, split_x, h)
        glow = QColor(COLOR_ACCENT)
        glow.setAlpha(35)
        p.setPen(QPen(glow, 10))
        p.drawLine(split_x, 0, split_x, h)

        handle_size = 36
        hx, hy = split_x, h // 2
        handle_grad = QLinearGradient(hx - handle_size // 2, hy - handle_size // 2,
                                       hx + handle_size // 2, hy + handle_size // 2)
        handle_grad.setColorAt(0.0, QColor(COLOR_ACCENT))
        handle_grad.setColorAt(1.0, QColor(COLOR_ACCENT_HOVER))
        p.setBrush(handle_grad)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(hx - 18, hy - 18, 36, 36, 18, 18)
        p.setPen(QPen(QColor("#ffffff"), 1.5))
        p.drawLine(hx - 7, hy, hx + 7, hy)
        p.drawLine(hx - 5, hy - 4, hx - 7, hy)
        p.drawLine(hx - 5, hy + 4, hx - 7, hy)
        p.drawLine(hx + 5, hy - 4, hx + 7, hy)
        p.drawLine(hx + 5, hy + 4, hx + 7, hy)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = True
            x = event.position().x()
            self._split_pos = max(0.1, min(0.9, x / self.width()))
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._dragging:
            x = event.position().x()
            self._split_pos = max(0.1, min(0.9, x / self.width()))
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        self._dragging = False


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


class ResultScreen(QWidget):
    upscale_another = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 24, 48, 24)
        layout.setSpacing(20)

        header = QLabel("Comparison")
        header.setStyleSheet(
            f"font-family: {FONT_DISPLAY}; font-size: 24px; font-weight: 700; "
            f"color: {COLOR_TEXT}; background: transparent; letter-spacing: -0.3px;"
        )
        layout.addWidget(header)

        slider = CompareSlider()
        layout.addWidget(slider)

        meta_frame = QFrame()
        meta_frame.setStyleSheet(
            f"background-color: transparent; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 12px; padding: 16px;"
        )
        meta_layout = QVBoxLayout(meta_frame)
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
            meta_layout.addWidget(row)

        layout.addWidget(meta_frame)

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

        layout.addStretch()
