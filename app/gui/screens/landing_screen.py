import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import (
    QPainter, QColor, QPen, QLinearGradient, QFont, QMouseEvent,
)

from app.utils.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
)

logger = logging.getLogger(__name__)


class BeforeAfterSlider(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(280)
        self.setMinimumWidth(400)
        self.setCursor(Qt.SplitHCursor)
        self._split_pos: float = 0.5
        self._dragging: bool = False
        self.setMouseTracking(True)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        split_x = int(w * self._split_pos)

        bg = QColor(COLOR_SURFACE)
        p.fillRect(self.rect(), bg)

        font_mono = QFont(FONT_MONO.split(",")[0].strip(), 11)
        font_body = QFont(FONT_BODY.split(",")[0].strip(), 12)

        left_rect = QRect(0, 0, split_x, h)
        p.save()
        p.setClipRect(left_rect)

        p.setFont(font_mono)
        p.setPen(QColor(COLOR_MUTED))
        p.drawText(left_rect.adjusted(20, 0, -20, -10), Qt.AlignLeft | Qt.AlignBottom, "BEFORE")

        p.setFont(QFont(FONT_DISPLAY.split(",")[0].strip(), 18, QFont.Bold))
        p.setPen(QColor("#2a2a3a"))
        p.drawText(left_rect.adjusted(0, 0, -20, 0), Qt.AlignRight | Qt.AlignVCenter, "480p")

        for y in range(0, h, 4):
            p.setPen(QColor(255, 255, 255, 6))
            p.drawLine(0, y, split_x, y)

        p.restore()

        right_rect = QRect(split_x, 0, w - split_x, h)
        p.save()
        p.setClipRect(right_rect)

        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0.0, QColor(COLOR_SURFACE).lighter(110))
        gradient.setColorAt(1.0, QColor(COLOR_SURFACE))
        p.fillRect(right_rect, gradient)

        p.setFont(font_mono)
        p.setPen(QColor(COLOR_ACCENT_HOVER))
        p.drawText(right_rect.adjusted(20, 0, -20, -10), Qt.AlignLeft | Qt.AlignBottom, "AFTER")

        p.setFont(QFont(FONT_DISPLAY.split(",")[0].strip(), 18, QFont.Bold))
        p.setPen(QColor(COLOR_ACCENT).lighter(130))
        p.drawText(right_rect.adjusted(20, 0, -20, 0), Qt.AlignLeft | Qt.AlignVCenter, "4K")

        p.restore()

        divider_pen = QPen(QColor(COLOR_ACCENT), 3)
        divider_pen.setWidthF(2.5)
        p.setPen(divider_pen)
        p.drawLine(split_x, 0, split_x, h)

        glow = QColor(COLOR_ACCENT)
        glow.setAlpha(40)
        glow_pen = QPen(glow, 12)
        glow_pen.setWidthF(12)
        p.setPen(glow_pen)
        p.drawLine(split_x, 0, split_x, h)

        handle_size = 40
        handle_rect = QRect(split_x - handle_size // 2, h // 2 - handle_size // 2,
                            handle_size, handle_size)
        handle_gradient = QLinearGradient(0, handle_rect.top(), 0, handle_rect.bottom())
        handle_gradient.setColorAt(0.0, QColor(COLOR_ACCENT))
        handle_gradient.setColorAt(1.0, QColor(COLOR_ACCENT_HOVER))
        p.setBrush(handle_gradient)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(handle_rect, 20, 20)

        p.setPen(QPen(QColor("#ffffff"), 2))
        arrow_size = 8
        cx = handle_rect.center().x()
        cy = handle_rect.center().y()
        p.drawLine(cx - arrow_size, cy, cx + arrow_size, cy)
        p.drawLine(cx - arrow_size - 2, cy - 4, cx - arrow_size, cy)
        p.drawLine(cx - arrow_size - 2, cy + 4, cx - arrow_size, cy)
        p.drawLine(cx + arrow_size + 2, cy - 4, cx + arrow_size, cy)
        p.drawLine(cx + arrow_size + 2, cy + 4, cx + arrow_size, cy)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._update_split(event.position().x())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            self._update_split(event.position().x())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False

    def _update_split(self, x: float) -> None:
        self._split_pos = max(0.1, min(0.9, x / self.width()))
        self.update()


class LandingScreen(QWidget):
    video_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 24, 48, 24)
        layout.setSpacing(0)

        layout.addStretch(2)

        slider = BeforeAfterSlider()
        slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(slider, 0, Qt.AlignCenter)

        layout.addSpacing(28)

        tagline = QLabel("Every pixel, elevated.")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(
            f"font-family: {FONT_DISPLAY}; font-size: 44px; font-weight: 700; "
            f"color: {COLOR_TEXT}; letter-spacing: -0.5px; background: transparent;"
        )
        layout.addWidget(tagline)

        layout.addSpacing(8)

        sub_copy = QLabel(
            "AI-powered upscaling from 480p to 4K in minutes."
        )
        sub_copy.setAlignment(Qt.AlignCenter)
        sub_copy.setStyleSheet(
            f"font-family: {FONT_BODY}; font-size: 16px; font-weight: 400; "
            f"color: {COLOR_MUTED}; background: transparent;"
        )
        layout.addWidget(sub_copy)

        layout.addSpacing(24)

        cta_btn = QPushButton("Upscale a Video")
        cta_btn.setCursor(Qt.PointingHandCursor)
        cta_btn.setFixedSize(220, 48)
        cta_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 {COLOR_ACCENT}, stop:1 {COLOR_ACCENT_HOVER});"
            f"  color: #ffffff; border: none; border-radius: 24px;"
            f"  font-family: {FONT_BODY}; font-size: 14px; font-weight: 600;"
            f"  letter-spacing: 0.3px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 {COLOR_ACCENT_HOVER}, stop:1 #c4b5fd);"
            f"}}"
            f"QPushButton:pressed {{"
            f"  margin-top: 1px;"
            f"}}"
        )
        cta_btn.clicked.connect(self._on_cta_clicked)
        layout.addWidget(cta_btn, 0, Qt.AlignCenter)

        layout.addSpacing(32)

        drop_area = QFrame()
        drop_area.setObjectName("dropZoneLanding")
        drop_area.setFixedHeight(160)
        drop_area.setCursor(Qt.PointingHandCursor)
        drop_area.setStyleSheet(
            f"QFrame#dropZoneLanding {{"
            f"  background-color: {COLOR_SURFACE};"
            f"  border: 2px dashed {COLOR_ACCENT};"
            f"  border-radius: 16px;"
            f"}}"
            f"QFrame#dropZoneLanding:hover {{"
            f"  background-color: #181828;"
            f"}}"
        )
        drop_layout = QVBoxLayout(drop_area)
        drop_layout.setAlignment(Qt.AlignCenter)
        drop_layout.setSpacing(8)

        upload_icon = QLabel("\u21E7")
        upload_icon.setAlignment(Qt.AlignCenter)
        upload_icon.setStyleSheet(
            f"color: {COLOR_ACCENT}; font-size: 32px; background: transparent;"
        )
        drop_layout.addWidget(upload_icon)

        drop_title = QLabel("Drop your video here")
        drop_title.setAlignment(Qt.AlignCenter)
        drop_title.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 16px; font-weight: 600; "
            f"font-family: {FONT_BODY}; background: transparent;"
        )
        drop_layout.addWidget(drop_title)

        drop_hint = QLabel("or browse files")
        drop_hint.setAlignment(Qt.AlignCenter)
        drop_hint.setStyleSheet(
            f"color: {COLOR_ACCENT}; font-size: 13px; font-weight: 500; "
            f"text-decoration: underline; background: transparent;"
        )
        drop_layout.addWidget(drop_hint)

        formats = QLabel("MP4 \u00B7 MOV \u00B7 AVI \u00B7 MKV \u00B7 WebM")
        formats.setAlignment(Qt.AlignCenter)
        formats.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 11px; "
            f"font-family: {FONT_MONO}; background: transparent;"
        )
        drop_layout.addWidget(formats)

        layout.addWidget(drop_area)

        layout.addStretch(3)

    def _on_cta_clicked(self) -> None:
        self.video_selected.emit("__open_dialog__")
