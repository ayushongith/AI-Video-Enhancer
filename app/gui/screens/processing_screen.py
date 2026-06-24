import logging
import math
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer, QRect, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QConicalGradient, QBrush,
)

from app.utils.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_DISPLAY, FONT_BODY, FONT_MONO, COLOR_SUCCESS, COLOR_ERROR,
)

logger = logging.getLogger(__name__)


class CircularProgress(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self._progress: float = 0.0
        self._target: float = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_step)
        self._anim_timer.setInterval(16)

    def set_progress(self, value: float) -> None:
        self._target = max(0.0, min(1.0, value))
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def _animate_step(self) -> None:
        diff = self._target - self._progress
        if abs(diff) < 0.002:
            self._progress = self._target
            self._anim_timer.stop()
        else:
            self._progress += diff * 0.15
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        cx, cy = w // 2, h // 2
        outer_r = min(w, h) // 2 - 12
        inner_r = outer_r - 14
        angle = int(self._progress * 360 * 16)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(COLOR_SURFACE))
        p.drawEllipse(QPoint(cx, cy), outer_r, outer_r)

        track_pen = QPen(QColor(COLOR_ELEVATED), 10)
        track_pen.setWidthF(10)
        p.setPen(track_pen)
        p.drawArc(QRect(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2),
                  90 * 16, -360 * 16)

        if self._progress > 0:
            gradient = QConicalGradient(cx, cy, 90)
            gradient.setColorAt(0.0, QColor(COLOR_ACCENT))
            gradient.setColorAt(0.5, QColor(COLOR_ACCENT_HOVER))
            gradient.setColorAt(1.0, QColor(COLOR_ACCENT))
            progress_pen = QPen(QBrush(gradient), 10)
            progress_pen.setWidthF(10)
            progress_pen.setCapStyle(Qt.RoundCap)
            p.setPen(progress_pen)
            p.drawArc(QRect(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2),
                      90 * 16, -angle)

        glow = QColor(COLOR_ACCENT)
        glow.setAlpha(20)
        glow_pen = QPen(glow, 18)
        glow_pen.setWidthF(18)
        p.setPen(glow_pen)
        p.drawArc(QRect(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2),
                  90 * 16, -angle)

        p.setFont(QFont(FONT_DISPLAY.split(",")[0].strip(), 40, QFont.Bold))
        p.setPen(QColor(COLOR_TEXT))
        pct_text = f"{int(self._progress * 100)}%"
        p.drawText(QRect(0, cy - 30, w, 60), Qt.AlignCenter, pct_text)

        p.setFont(QFont(FONT_BODY.split(",")[0].strip(), 10))
        p.setPen(QColor(COLOR_MUTED))
        p.drawText(QRect(0, cy + 30, w, 20), Qt.AlignCenter, "PROCESSING")

class ProcessingScreen(QWidget):
    cancelled = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._progress_ring: Optional[CircularProgress] = None
        self._start_time: float = 0.0
        self._last_update: float = 0.0
        self._last_frame: int = 0
        self._total_frames: int = 0
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)

        center_widget = QWidget()
        center_widget.setMaximumWidth(500)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(20)

        self._progress_ring = CircularProgress()
        center_layout.addWidget(self._progress_ring, 0, Qt.AlignCenter)

        center_layout.addSpacing(8)

        stats_frame = QFrame()
        stats_frame.setStyleSheet(
            f"background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 12px; padding: 16px;"
        )
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(32)

        stats_data = [
            ("Frame", "0 / 0"),
            ("ETA", "--:--"),
            ("Speed", "0 fps"),
        ]
        self._stat_labels: list[QLabel] = []
        for label, value in stats_data:
            col = QVBoxLayout()
            col.setSpacing(4)
            header = QLabel(label)
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet(
                f"color: {COLOR_MUTED}; font-size: 10px; font-weight: 600; "
                f"font-family: {FONT_BODY}; background: transparent; "
                f"letter-spacing: 0.8px;"
            )
            col.addWidget(header)
            val = QLabel(value)
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet(
                f"color: {COLOR_TEXT}; font-size: 18px; font-weight: 600; "
                f"font-family: {FONT_MONO}; background: transparent;"
            )
            self._stat_labels.append(val)
            col.addWidget(val)
            stats_layout.addLayout(col)

        center_layout.addWidget(stats_frame)

        center_layout.addSpacing(16)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedSize(140, 38)
        cancel_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {COLOR_MUTED};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 19px;"
            f"  font-family: {FONT_BODY}; font-size: 13px; font-weight: 500;"
            f"}}"
            f"QPushButton:hover {{"
            f"  color: {COLOR_ERROR};"
            f"  border-color: {COLOR_ERROR};"
            f"}}"
        )
        cancel_btn.clicked.connect(self.cancelled.emit)
        center_layout.addWidget(cancel_btn, 0, Qt.AlignCenter)

        layout.addWidget(center_widget)

    def update_progress(self, current: int, total: int, message: str) -> None:
        if total > 0:
            pct = current / total
        else:
            pct = 0.0
        if self._progress_ring:
            self._progress_ring.set_progress(pct)

        now = __import__('time').time()
        elapsed = now - self._start_time
        self._total_frames = total

        if self._stat_labels and len(self._stat_labels) >= 3:
            self._stat_labels[0].setText(f"{current} / {total}")

            if elapsed > 0 and current > 0:
                fps = current / elapsed
                self._stat_labels[2].setText(f"{fps:.1f} fps")

                remaining_frames = total - current
                if fps > 0:
                    eta_s = remaining_frames / fps
                    if eta_s < 60:
                        eta_str = f"{eta_s:.0f}s"
                    elif eta_s < 3600:
                        eta_str = f"{eta_s // 60:.0f}m {eta_s % 60:.0f}s"
                    else:
                        eta_str = f"{eta_s // 3600:.0f}h {(eta_s % 3600) // 60:.0f}m"
                    self._stat_labels[1].setText(eta_str)
                else:
                    self._stat_labels[1].setText("--:--")
            else:
                self._stat_labels[1].setText("--:--")
                self._stat_labels[2].setText("0 fps")

    def start_processing(self) -> None:
        self._start_time = __import__('time').time()
        self._last_update = self._start_time
        self._last_frame = 0
        if self._progress_ring:
            self._progress_ring.set_progress(0.0)
        if self._stat_labels:
            self._stat_labels[0].setText("0 / 0")
            self._stat_labels[1].setText("--:--")
            self._stat_labels[2].setText("0 fps")

    def stop_processing(self) -> None:
        pass
