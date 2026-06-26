import logging
from typing import Optional

from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QPixmap, QImage,
    QMouseEvent, QWheelEvent, QCursor,
)
import numpy as np

from app.utils.constants import (
    COLOR_SURFACE, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_BODY, FONT_MONO,
)

logger = logging.getLogger(__name__)


class ComparisonView(QFrame):
    MODE_SIDE_BY_SIDE = 0
    MODE_OVERLAY = 1
    MODE_SLIDER = 2

    mode_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._before: Optional[QPixmap] = None
        self._after: Optional[QPixmap] = None
        self._mode = self.MODE_SLIDER
        self._split_pos = 0.5
        self._dragging = False
        self._zoom = 1.0
        self._offset = QPoint(0, 0)
        self._panning = False
        self._pan_start = QPoint(0, 0)
        self.setMinimumSize(500, 300)
        self.setMouseTracking(True)
        self.setStyleSheet(
            f"background-color: #0a0a10; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 8px;"
        )

    def set_frames(self, before: Optional[np.ndarray], after: Optional[np.ndarray]) -> None:
        self._before = self._to_pixmap(before)
        self._after = self._to_pixmap(after)
        self._zoom = 1.0
        self._offset = QPoint(0, 0)
        self.update()

    @staticmethod
    def _to_pixmap(frame: Optional[np.ndarray]) -> Optional[QPixmap]:
        if frame is None:
            return None
        h, w = frame.shape[:2]
        qimg = QImage(frame.data, w, h, 3 * w, QImage.Format_BGR888)
        return QPixmap.fromImage(qimg)

    def set_mode(self, mode: int) -> None:
        self._mode = mode
        self.mode_changed.emit(mode)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor("#0a0a10"))

        if self._before is None and self._after is None:
            p.setFont(QFont(FONT_BODY, 13))
            p.setPen(QColor(COLOR_MUTED))
            p.drawText(self.rect(), Qt.AlignCenter, "No comparison data")
            return

        if self._mode == self.MODE_SIDE_BY_SIDE:
            self._paint_side_by_side(p)
        elif self._mode == self.MODE_OVERLAY:
            self._paint_overlay(p)
        else:
            self._paint_slider(p)

    def _paint_side_by_side(self, p: QPainter) -> None:
        w = self.width()
        h = self.height()
        half = w // 2

        if self._before:
            p.save()
            p.setClipRect(0, 0, half, h)
            scaled = self._before.scaled(half, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (half - scaled.width()) // 2
            y = (h - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
            p.restore()

        p.setPen(QPen(QColor(COLOR_BORDER), 1))
        p.drawLine(half, 0, half, h)

        if self._after:
            p.save()
            p.setClipRect(half, 0, half, h)
            scaled = self._after.scaled(half, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = half + (half - scaled.width()) // 2
            y = (h - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
            p.restore()

        font = QFont(FONT_BODY, 10, QFont.Bold)
        p.setFont(font)
        p.setPen(QColor(COLOR_MUTED))
        p.drawText(QRect(0, h - 24, half, 20), Qt.AlignCenter, "ORIGINAL")
        p.drawText(QRect(half, h - 24, half, 20), Qt.AlignCenter, "ENHANCED")

    def _paint_overlay(self, p: QPainter) -> None:
        base = self._before or self._after
        if base is None:
            return
        scaled = base.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        p.drawPixmap(x, y, scaled)

        if self._after:
            overlay = self._after.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.setOpacity(0.5)
            p.drawPixmap(x, y, overlay)
            p.setOpacity(1.0)

    def _paint_slider(self, p: QPainter) -> None:
        w = self.width()
        h = self.height()
        split_x = int(w * self._split_pos)

        if self._before:
            p.save()
            p.setClipRect(0, 0, split_x, h)
            scaled = self._before.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            px = (w - scaled.width()) // 2
            py = (h - scaled.height()) // 2
            p.drawPixmap(px, py, scaled)
            p.restore()

        if self._after:
            p.save()
            p.setClipRect(split_x, 0, w, h)
            scaled = self._after.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            px = (w - scaled.width()) // 2
            py = (h - scaled.height()) // 2
            p.drawPixmap(px, py, scaled)
            p.restore()

        p.setPen(QPen(QColor(COLOR_ACCENT), 2))
        p.drawLine(split_x, 0, split_x, h)
        glow = QColor(COLOR_ACCENT)
        glow.setAlpha(30)
        p.setPen(QPen(glow, 10))
        p.drawLine(split_x, 0, split_x, h)

        handle = QRect(split_x - 16, h // 2 - 16, 32, 32)
        grad = QColor(COLOR_ACCENT)
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(handle, 16, 16)
        p.setPen(QPen(QColor("#ffffff"), 1.5))
        p.drawLine(split_x - 5, h // 2, split_x + 5, h // 2)
        p.drawLine(split_x - 3, h // 2 - 3, split_x - 5, h // 2)
        p.drawLine(split_x - 3, h // 2 + 3, split_x - 5, h // 2)
        p.drawLine(split_x + 3, h // 2 - 3, split_x + 5, h // 2)
        p.drawLine(split_x + 3, h // 2 + 3, split_x + 5, h // 2)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._mode == self.MODE_SLIDER:
            self._dragging = True
            self._update_split(event.position().x())
        elif event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            self._update_split(event.position().x())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False
        self._panning = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom = min(4.0, self._zoom * 1.1)
        else:
            self._zoom = max(0.25, self._zoom / 1.1)
        self.update()

    def _update_split(self, x: float) -> None:
        self._split_pos = max(0.05, min(0.95, x / max(1, self.width())))
        self.update()
