import logging
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QPixmap, QImage,
    QMouseEvent, QFontDatabase,
)

import numpy as np

from app.utils.constants import (
    COLOR_SURFACE, COLOR_ACCENT, COLOR_MUTED, COLOR_BORDER, COLOR_TEXT,
    FONT_MONO, FONT_BODY,
)

logger = logging.getLogger(__name__)


class ThumbnailStrip(QFrame):
    frame_selected = Signal(int)

    THUMB_W = 140
    THUMB_H = 79
    GAP = 6

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._thumbnails: list[QPixmap] = []
        self._frame_indices: list[int] = []
        self._selected: int = -1
        self._scroll_offset: int = 0
        self.setFixedHeight(self.THUMB_H + 28)
        self.setMouseTracking(True)
        self.setStyleSheet(
            f"background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 6px;"
        )

    def set_thumbnails(
        self, frames: list[np.ndarray], indices: list[int],
    ) -> None:
        self._thumbnails = []
        for frame in frames:
            h, w = frame.shape[:2]
            qimg = QImage(frame.data, w, h, 3 * w, QImage.Format_BGR888)
            pix = QPixmap.fromImage(qimg).scaled(
                self.THUMB_W, self.THUMB_H, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
            self._thumbnails.append(pix)
        self._frame_indices = list(indices)
        self._selected = -1
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(COLOR_SURFACE))

        if not self._thumbnails:
            p.setFont(QFont(FONT_BODY, 11))
            p.setPen(QColor(COLOR_MUTED))
            p.drawText(self.rect(), Qt.AlignCenter, "No thumbnails")
            return

        y = 6
        for i, (thumb, idx) in enumerate(zip(self._thumbnails, self._frame_indices)):
            x = 8 + i * (self.THUMB_W + self.GAP) - self._scroll_offset

            if x + self.THUMB_W < 0 or x > self.width():
                continue

            if i == self._selected:
                p.setPen(QPen(QColor(COLOR_ACCENT), 2))
                p.setBrush(QColor(COLOR_ACCENT + "20"))
                p.drawRoundedRect(x - 2, y - 2, self.THUMB_W + 4, self.THUMB_H + 4, 4, 4)

            p.drawPixmap(x, y, thumb)

            frame_num = QRect(x, y + self.THUMB_H - 18, self.THUMB_W, 18)
            p.fillRect(frame_num, QColor(0, 0, 0, 160))
            p.setFont(QFont(FONT_MONO, 9))
            p.setPen(QColor(COLOR_TEXT))
            p.drawText(frame_num, Qt.AlignCenter, f"#{idx}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._thumbnails:
            return
        mx = int(event.position().x())
        y = 6
        for i in range(len(self._thumbnails)):
            x = 8 + i * (self.THUMB_W + self.GAP) - self._scroll_offset
            if x <= mx <= x + self.THUMB_W:
                self._selected = i
                self.frame_selected.emit(self._frame_indices[i])
                self.update()
                break

    def clear(self) -> None:
        self._thumbnails.clear()
        self._frame_indices.clear()
        self._selected = -1
        self.update()
