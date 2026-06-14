import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSlider, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer, QRect
from PySide6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QFont,
)

from app.utils.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
)
from app.core.video_loader import VideoMetadata
from app.core.frame_extractor import FrameExtractor

logger = logging.getLogger(__name__)


class VideoCanvas(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"background-color: #050508; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 8px;"
        )
        self.setMinimumSize(400, 300)
        self._pixmap: Optional[QPixmap] = None

    def set_frame(self, frame) -> None:
        if frame is None:
            self._pixmap = None
            self.update()
            return
        h, w = frame.shape[:2]
        bytes_per_line = 3 * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
        self._pixmap = QPixmap.fromImage(qimg)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor("#050508"))

        if self._pixmap:
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
        else:
            p.setFont(QFont(FONT_BODY, 13))
            p.setPen(QColor(COLOR_MUTED))
            p.drawText(self.rect(), Qt.AlignCenter, "No video loaded")


class PreviewScreen(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._canvas: Optional[VideoCanvas] = None
        self._extractor: Optional[FrameExtractor] = None
        self._play_timer: Optional[QTimer] = None
        self._playing: bool = False
        self._current_frame: int = 0
        self._total_frames: int = 0
        self._metadata: Optional[VideoMetadata] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Preview")
        title.setStyleSheet(
            f"font-family: {FONT_DISPLAY}; font-size: 20px; font-weight: 700; "
            f"color: {COLOR_TEXT}; background: transparent;"
        )
        header.addWidget(title)

        self._frame_label = QLabel("-- / --")
        self._frame_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 12px; font-family: {FONT_MONO}; "
            f"background: transparent;"
        )
        header.addWidget(self._frame_label)
        header.addStretch()
        layout.addLayout(header)

        self._canvas = VideoCanvas()
        layout.addWidget(self._canvas, stretch=1)

        controls = QFrame()
        controls.setStyleSheet(
            f"background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; "
            f"border-radius: 10px; padding: 12px;"
        )
        controls_layout = QVBoxLayout(controls)
        controls_layout.setSpacing(10)

        self._timeline = QSlider(Qt.Horizontal)
        self._timeline.setRange(0, 0)
        self._timeline.setStyleSheet(
            f"QSlider::groove:horizontal {{"
            f"  height: 4px; background: {COLOR_ELEVATED}; border-radius: 2px;"
            f"}}"
            f"QSlider::handle:horizontal {{"
            f"  background: {COLOR_ACCENT}; width: 14px; height: 14px;"
            f"  margin: -5px 0; border-radius: 7px;"
            f"}}"
            f"QSlider::sub-page:horizontal {{"
            f"  background: {COLOR_ACCENT}; border-radius: 2px;"
            f"}}"
        )
        self._timeline.sliderMoved.connect(self._on_seek)
        controls_layout.addWidget(self._timeline)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        self._play_btn = QPushButton("\u25B6")
        self._play_btn.setFixedSize(40, 36)
        self._play_btn.setCursor(Qt.PointingHandCursor)
        self._play_btn.clicked.connect(self._toggle_play)
        self._play_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {COLOR_ACCENT}; color: #ffffff;"
            f"  border: none; border-radius: 18px; font-size: 16px;"
            f"}}"
            f"QPushButton:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}"
        )
        btn_row.addWidget(self._play_btn)

        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 11px; font-family: {FONT_MONO}; "
            f"background: transparent; padding: 0 8px;"
        )
        btn_row.addWidget(self._time_label)
        btn_row.addStretch()
        controls_layout.addLayout(btn_row)

        layout.addWidget(controls)

        self._play_timer = QTimer(self)
        self._play_timer.timeout.connect(self._play_next)

    def load_video(self, metadata: VideoMetadata) -> None:
        self._metadata = metadata
        self._extractor = FrameExtractor(metadata)
        if not self._extractor.open():
            logger.error("Failed to open video for preview")
            return

        self._total_frames = self._extractor.total_frames()
        self._current_frame = 0
        self._timeline.setRange(0, max(0, self._total_frames - 1))
        self._timeline.setValue(0)

        frame = self._extractor.seek_frame(0)
        if frame is not None:
            self._canvas.set_frame(frame)
        self._update_labels()
        self._playing = False
        self._play_btn.setText("\u25B6")

    def _toggle_play(self) -> None:
        if not self._extractor:
            return
        self._playing = not self._playing
        self._play_btn.setText("\u23F8" if self._playing else "\u25B6")
        if self._playing:
            self._play_timer.start(int(1000 / max(1, self._extractor.fps())))
        else:
            self._play_timer.stop()

    def _play_next(self) -> None:
        if not self._extractor or self._current_frame >= self._total_frames - 1:
            self._playing = False
            self._play_btn.setText("\u25B6")
            self._play_timer.stop()
            return
        self._current_frame += 1
        frame = self._extractor.seek_frame(self._current_frame)
        if frame is not None:
            self._canvas.set_frame(frame)
        self._timeline.setValue(self._current_frame)
        self._update_labels()

    def _on_seek(self, position: int) -> None:
        if not self._extractor:
            return
        self._current_frame = position
        frame = self._extractor.seek_frame(position)
        if frame is not None:
            self._canvas.set_frame(frame)
        self._update_labels()

    def _update_labels(self) -> None:
        self._frame_label.setText(f"{self._current_frame} / {self._total_frames}")
        if self._metadata and self._metadata.fps > 0:
            current_s = self._current_frame / self._metadata.fps
            total_s = self._total_frames / self._metadata.fps
            self._time_label.setText(
                f"{int(current_s)//60:02d}:{int(current_s)%60:02d} / "
                f"{int(total_s)//60:02d}:{int(total_s)%60:02d}"
            )

    def unload(self) -> None:
        self._playing = False
        if self._play_timer:
            self._play_timer.stop()
        if self._extractor:
            self._extractor.close()
        self._extractor = None
        self._canvas.set_frame(None)
        self._frame_label.setText("-- / --")
        self._timeline.setRange(0, 0)
        self._timeline.setValue(0)
        self._time_label.setText("00:00 / 00:00")
        self._play_btn.setText("\u25B6")
