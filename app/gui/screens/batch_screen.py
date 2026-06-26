import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QListWidget, QListWidgetItem, QFileDialog,
    QProgressBar,
)
from PySide6.QtCore import Qt, Signal, QSize

from app.utils.constants import (
    COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_BODY, VIDEO_EXTENSIONS_FILTER,
)

logger = logging.getLogger(__name__)


class BatchScreen(QWidget):
    files_selected = Signal(list)
    start_batch = Signal()
    cancel_batch = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._files: list[Path] = []
        self._list_widget: Optional[QListWidget] = None
        self._start_btn: Optional[QPushButton] = None
        self._progress_bar: Optional[QProgressBar] = None
        self._status_label: Optional[QLabel] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Batch Processing")
        title.setStyleSheet(
            f"font-family: {FONT_DISPLAY}; font-size: 20px; font-weight: 700; "
            f"color: {COLOR_TEXT}; background: transparent; letter-spacing: -0.3px;"
        )
        header.addWidget(title)

        count_label = QLabel("0 files")
        count_label.setObjectName("batchCount")
        count_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 12px; font-family: {FONT_MONO}; "
            f"background: transparent;"
        )
        header.addWidget(count_label)
        header.addStretch()
        layout.addLayout(header)

        add_btn = QPushButton("+ Add Videos")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._on_add_files)
        add_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {COLOR_SURFACE};"
            f"  color: {COLOR_TEXT};"
            f"  border: 1px dashed {COLOR_BORDER};"
            f"  border-radius: 8px;"
            f"  font-family: {FONT_BODY}; font-size: 13px; font-weight: 500;"
            f"  padding: 10px 20px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  border-color: {COLOR_ACCENT};"
            f"  color: {COLOR_ACCENT};"
            f"}}"
        )
        layout.addWidget(add_btn)

        self._list_widget = QListWidget()
        self._list_widget.setStyleSheet(
            f"QListWidget {{"
            f"  background-color: {COLOR_SURFACE};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 8px;"
            f"  padding: 4px;"
            f"}}"
            f"QListWidget::item {{"
            f"  color: {COLOR_TEXT};"
            f"  padding: 8px 12px;"
            f"  border-bottom: 1px solid {COLOR_BORDER};"
            f"}}"
            f"QListWidget::item:last {{"
            f"  border-bottom: none;"
            f"}}"
        )
        layout.addWidget(self._list_widget, stretch=1)

        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedHeight(6)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 12px; font-family: {FONT_BODY}; "
            f"background: transparent;"
        )
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        clear_btn = QPushButton("Clear All")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._on_clear)
        clear_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {COLOR_MUTED};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 8px;"
            f"  font-family: {FONT_BODY}; font-size: 12px;"
            f"  padding: 8px 18px;"
            f"}}"
            f"QPushButton:hover {{ color: {COLOR_ERROR}; border-color: {COLOR_ERROR}; }}"
        )
        btn_row.addWidget(clear_btn)

        self._start_btn = QPushButton("Start Batch Processing")
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._on_start)
        self._start_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 {COLOR_ACCENT}, stop:1 {COLOR_ACCENT_HOVER});"
            f"  color: #ffffff; border: none; border-radius: 20px;"
            f"  font-family: {FONT_BODY}; font-size: 13px; font-weight: 600;"
            f"  padding: 10px 28px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"    stop:0 {COLOR_ACCENT_HOVER}, stop:1 #c4b5fd);"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background: {COLOR_ELEVATED}; color: {COLOR_MUTED};"
            f"}}"
        )
        btn_row.addWidget(self._start_btn)
        layout.addLayout(btn_row)

    def add_files(self, files: list[Path]) -> None:
        for p in files:
            if p not in self._files:
                self._files.append(p)
        self._refresh_list()

    def _on_add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Videos", "", VIDEO_EXTENSIONS_FILTER,
        )
        if files:
            for f in files:
                p = Path(f)
                if p not in self._files:
                    self._files.append(p)
            self._refresh_list()

    def _on_clear(self) -> None:
        self._files.clear()
        self._refresh_list()

    def _on_start(self) -> None:
        if self._files:
            self.files_selected.emit(self._files)
            self.start_batch.emit()

    def _refresh_list(self) -> None:
        if not self._list_widget:
            return
        self._list_widget.clear()
        for f in self._files:
            item = QListWidgetItem(f"  {f.name}")
            item.setSizeHint(QSize(0, 36))
            self._list_widget.addItem(item)

        count_label = self.findChild(QLabel, "batchCount")
        if count_label:
            count_label.setText(f"{len(self._files)} files")

        if self._start_btn:
            self._start_btn.setEnabled(len(self._files) > 0)

    def set_progress(self, current: int, total: int, filename: str, status: str) -> None:
        self._progress_bar.setVisible(True)
        self._status_label.setVisible(True)
        if total > 0:
            self._progress_bar.setMaximum(total)
            self._progress_bar.setValue(current)
        self._status_label.setText(f"[{current}/{total}] {filename}: {status}")

    def reset(self) -> None:
        self._progress_bar.setVisible(False)
        self._status_label.setVisible(False)
        self._progress_bar.setValue(0)
