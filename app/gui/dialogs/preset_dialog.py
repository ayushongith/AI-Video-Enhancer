import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QSize

from app.utils.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_DISPLAY, FONT_BODY,
)
from app.core.export_presets import ExportPresets, BUILTIN_PRESETS
from app.core.processing_pipeline import ProcessingConfig

logger = logging.getLogger(__name__)


class PresetDialog(QDialog):
    preset_selected = Signal(str, object)
    preset_saved = Signal(str, object)

    def __init__(
        self, presets: ExportPresets,
        current_config: Optional[ProcessingConfig] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._presets = presets
        self._current_config = current_config
        self.setWindowTitle("Export Presets")
        self.setFixedSize(440, 480)
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_BG}; }}")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Export Presets")
        title.setStyleSheet(
            f"font-family: {FONT_DISPLAY}; font-size: 18px; font-weight: 700; "
            f"color: {COLOR_TEXT}; background: transparent;"
        )
        layout.addWidget(title)

        self._list = QListWidget()
        self._list.setStyleSheet(
            f"QListWidget {{"
            f"  background-color: {COLOR_SURFACE};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 8px; padding: 4px;"
            f"}}"
            f"QListWidget::item {{"
            f"  color: {COLOR_TEXT}; padding: 8px 12px;"
            f"  border-bottom: 1px solid {COLOR_BORDER};"
            f"  font-family: {FONT_BODY}; font-size: 12px;"
            f"}}"
            f"QListWidget::item:selected {{"
            f"  background-color: {COLOR_ACCENT}; color: #ffffff;"
            f"}}"
        )
        for name in self._presets.list_names():
            item = QListWidgetItem(name)
            if name in BUILTIN_PRESETS:
                item.setToolTip("Built-in preset")
            self._list.addItem(item)
        layout.addWidget(self._list, stretch=1)

        save_layout = QHBoxLayout()
        save_layout.setSpacing(8)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Save current settings as...")
        self._name_input.setStyleSheet(
            f"QLineEdit {{"
            f"  background-color: {COLOR_SURFACE}; color: {COLOR_TEXT};"
            f"  border: 1px solid {COLOR_BORDER}; border-radius: 6px;"
            f"  padding: 6px 12px; font-family: {FONT_BODY}; font-size: 12px;"
            f"}}"
            f"QLineEdit:focus {{ border-color: {COLOR_ACCENT}; }}"
        )
        save_layout.addWidget(self._name_input, stretch=1)

        save_btn = QPushButton("Save")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        save_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {COLOR_ACCENT}; color: #ffffff;"
            f"  border: none; border-radius: 6px;"
            f"  font-family: {FONT_BODY}; font-size: 12px; font-weight: 600;"
            f"  padding: 6px 16px;"
            f"}}"
            f"QPushButton:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}"
        )
        save_layout.addWidget(save_btn)
        layout.addLayout(save_layout)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        apply_btn = QPushButton("Apply Preset")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.clicked.connect(self._on_apply)
        apply_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {COLOR_SURFACE}; color: {COLOR_TEXT};"
            f"  border: 1px solid {COLOR_BORDER}; border-radius: 8px;"
            f"  font-family: {FONT_BODY}; font-size: 12px; padding: 8px 20px;"
            f"}}"
            f"QPushButton:hover {{ border-color: {COLOR_ACCENT}; color: {COLOR_ACCENT}; }}"
        )
        btn_row.addWidget(apply_btn)

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent; color: {COLOR_MUTED};"
            f"  border: 1px solid {COLOR_BORDER}; border-radius: 8px;"
            f"  font-family: {FONT_BODY}; font-size: 12px; padding: 8px 20px;"
            f"}}"
            f"QPushButton:hover {{ color: {COLOR_TEXT}; }}"
        )
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _on_apply(self) -> None:
        current = self._list.currentItem()
        if current:
            name = current.text()
            config = self._presets.get(name)
            if config:
                self.preset_selected.emit(name, config)
                self.accept()

    def _on_save(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Name required", "Enter a preset name")
            return
        if self._current_config:
            self._presets.save_preset(name, self._current_config)
            item = QListWidgetItem(name)
            self._list.addItem(item)
            self._list.setCurrentItem(item)
            self._name_input.clear()
            self.preset_saved.emit(name, self._current_config)
