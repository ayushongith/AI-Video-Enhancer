import logging
from typing import Optional
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QGridLayout, QLabel, QHBoxLayout,
)
from PySide6.QtCore import Qt

from app.core.video_loader import VideoMetadata

logger = logging.getLogger(__name__)


class _InfoItem(QFrame):
    def __init__(self, label: str, value: str = "-", parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            "background-color: #181838; border: 1px solid #222248; "
            "border-radius: 8px; padding: 12px 16px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label_w = QLabel(label.upper())
        label_w.setStyleSheet(
            "color: #5c5c80; font-size: 10px; font-weight: 600; "
            "background: transparent; letter-spacing: 0.8px;"
        )
        layout.addWidget(label_w)

        self._value_w = QLabel(value)
        self._value_w.setStyleSheet(
            "color: #e6e6f0; font-size: 14px; font-weight: 600; "
            "background: transparent;"
        )
        self._value_w.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._value_w)

    def set_value(self, text: str) -> None:
        self._value_w.setText(text)


class VideoInfoPanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("infoCard")
        self.setVisible(False)
        self._metadata: Optional[VideoMetadata] = None
        self._items: dict[str, _InfoItem] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Video Information")
        title.setProperty("heading", True)
        header_row.addWidget(title)

        self._badge = QLabel()
        self._badge.setStyleSheet(
            "background-color: #10b981; color: #ffffff; font-size: 10px; "
            "font-weight: 700; padding: 2px 10px; border-radius: 10px; "
            "letter-spacing: 0.5px;"
        )
        self._badge.setVisible(False)
        header_row.addWidget(self._badge)
        header_row.addStretch()
        layout.addLayout(header_row)

        grid = QGridLayout()
        grid.setSpacing(10)

        fields = [
            ("Video Name", "filename", 2, 0, 0),
            ("Resolution", "resolution", 1, 0, 1),
            ("FPS", "fps", 1, 0, 2),
            ("Duration", "duration_str", 1, 1, 0),
            ("Codec", "codec", 1, 1, 1),
            ("Bitrate", "bitrate_str", 1, 1, 2),
            ("File Size", "size_str", 1, 2, 0),
        ]

        for field_name, attr, colspan, row, col in fields:
            item = _InfoItem(field_name)
            self._items[attr] = item
            grid.addWidget(item, row, col, 1, colspan)

        layout.addLayout(grid)

    def display_metadata(self, metadata: VideoMetadata) -> None:
        self._metadata = metadata
        attr_map = {
            "filename": "filename",
            "resolution": "resolution",
            "fps": "fps",
            "duration_str": "duration_str",
            "codec": "codec",
            "bitrate_str": "bitrate_str",
            "size_str": "size_str",
        }

        for attr, source_attr in attr_map.items():
            item = self._items.get(attr)
            if item:
                value = getattr(metadata, source_attr, "-")
                if attr == "fps" and isinstance(value, float):
                    item.set_value(f"{value:.2f}")
                else:
                    item.set_value(str(value))

        self._badge.setText(metadata.codec)
        self._badge.setVisible(True)
        self.setVisible(True)
        logger.info("Displayed metadata for %s", metadata.filename)

    def clear(self) -> None:
        self._metadata = None
        for item in self._items.values():
            item.set_value("-")
        self._badge.setVisible(False)
        self.setVisible(False)
