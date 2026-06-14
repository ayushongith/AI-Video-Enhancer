import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSlider, QComboBox, QButtonGroup, QCheckBox,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect

from app.utils.constants import (
    COLOR_BG, COLOR_SURFACE, COLOR_ELEVATED, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
)

logger = logging.getLogger(__name__)


class _SectionHeader(QLabel):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 1px; font-family: {FONT_BODY}; "
            f"background: transparent; padding: 12px 0 4px 0;"
        )


class _Toggle(QFrame):
    toggled = Signal(bool)

    def __init__(self, label: str, checked: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._checked = checked
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 12px; font-family: {FONT_BODY}; "
            f"background: transparent;"
        )
        layout.addWidget(lbl)

        layout.addStretch()

        self._toggle_btn = QPushButton()
        self._toggle_btn.setFixedSize(40, 22)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._on_click)
        self._update_style()
        layout.addWidget(self._toggle_btn)

    def _update_style(self) -> None:
        if self._checked:
            self._toggle_btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: {COLOR_ACCENT};"
                f"  border: none; border-radius: 11px;"
                f"}}"
            )
        else:
            self._toggle_btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: {COLOR_ELEVATED};"
                f"  border: 1px solid {COLOR_BORDER}; border-radius: 11px;"
                f"}}"
            )

    def _on_click(self) -> None:
        self._checked = not self._checked
        self._update_style()
        self.toggled.emit(self._checked)

    def is_checked(self) -> bool:
        return self._checked


class _ResolutionToggle(QFrame):
    changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        resolutions = ["720p", "1080p", "2K", "4K", "8K"]
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.idToggled.connect(self._on_toggled)

        for i, res in enumerate(resolutions):
            btn = QPushButton(res)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: {COLOR_SURFACE};"
                f"  color: {COLOR_MUTED};"
                f"  border: 1px solid {COLOR_BORDER};"
                f"  border-radius: 6px;"
                f"  font-family: {FONT_MONO}; font-size: 11px; font-weight: 500;"
                f"  padding: 0 12px;"
                f"}}"
                f"QPushButton:checked {{"
                f"  background-color: {COLOR_ACCENT};"
                f"  color: #ffffff;"
                f"  border-color: {COLOR_ACCENT};"
                f"}}"
                f"QPushButton:hover:!checked {{"
                f"  border-color: {COLOR_MUTED};"
                f"}}"
            )
            self._group.addButton(btn, i)
            layout.addWidget(btn)

        if self._group.buttons():
            self._group.buttons()[1].setChecked(True)

    def _on_toggled(self, id: int, checked: bool) -> None:
        if checked and 0 <= id < len(self._group.buttons()):
            self.changed.emit(self._group.buttons()[id].text())


class SettingsPanel(QFrame):
    closed = Signal()
    settings_changed = Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(0)
        self._is_open: bool = False
        self._animation: Optional[QPropertyAnimation] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            f"background-color: {COLOR_ELEVATED}; "
            f"border-left: 1px solid {COLOR_BORDER};"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(52)
        header.setStyleSheet(
            f"background-color: {COLOR_SURFACE}; "
            f"border-bottom: 1px solid {COLOR_BORDER};"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("Settings")
        title.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 600; "
            f"font-family: {FONT_BODY}; background: transparent;"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {COLOR_MUTED};"
            f"  border: none; border-radius: 14px;"
            f"  font-size: 14px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {COLOR_ELEVATED};"
            f"  color: {COLOR_TEXT};"
            f"}}"
        )
        close_btn.clicked.connect(self.close_panel)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(16, 8, 16, 16)
        scroll_layout.setSpacing(4)

        scroll_layout.addWidget(_SectionHeader("OUTPUT RESOLUTION"))
        self._res_toggle = _ResolutionToggle()
        scroll_layout.addWidget(self._res_toggle)

        scroll_layout.addWidget(_SectionHeader("ENHANCEMENT MODE"))
        modes = ["Standard", "Film Grain", "Anime", "Low Light"]
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(4)
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        for i, mode in enumerate(modes):
            btn = QPushButton(mode)
            btn.setCheckable(True)
            btn.setFixedHeight(60)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: {COLOR_SURFACE};"
                f"  color: {COLOR_MUTED};"
                f"  border: 1px solid {COLOR_BORDER};"
                f"  border-radius: 8px;"
                f"  font-family: {FONT_BODY}; font-size: 10px; font-weight: 500;"
                f"  padding: 4px;"
                f"}}"
                f"QPushButton:checked {{"
                f"  background-color: {COLOR_ACCENT};"
                f"  color: #ffffff;"
                f"  border-color: {COLOR_ACCENT};"
                f"}}"
                f"QPushButton:hover:!checked {{"
                f"  border-color: {COLOR_MUTED};"
                f"}}"
            )
            self._mode_group.addButton(btn, i)
            mode_layout.addWidget(btn)
        if self._mode_group.buttons():
            self._mode_group.buttons()[0].setChecked(True)
        scroll_layout.addLayout(mode_layout)

        scroll_layout.addWidget(_SectionHeader("FACE ENHANCEMENT"))
        self._face_toggle = _Toggle("Enhance faces", True)
        scroll_layout.addWidget(self._face_toggle)

        scroll_layout.addWidget(_SectionHeader("NOISE REDUCTION"))
        noise_layout = QVBoxLayout()
        self._noise_slider = QSlider(Qt.Horizontal)
        self._noise_slider.setRange(0, 100)
        self._noise_slider.setValue(40)
        self._noise_slider.setFixedHeight(24)
        self._noise_slider.setStyleSheet(
            f"QSlider::groove:horizontal {{"
            f"  height: 4px; background: {COLOR_ELEVATED}; border-radius: 2px;"
            f"}}"
            f"QSlider::handle:horizontal {{"
            f"  background: {COLOR_ACCENT}; width: 16px; height: 16px;"
            f"  margin: -6px 0; border-radius: 8px;"
            f"}}"
            f"QSlider::sub-page:horizontal {{"
            f"  background: {COLOR_ACCENT}; border-radius: 2px;"
            f"}}"
        )
        noise_layout.addWidget(self._noise_slider)

        self._noise_val = QLabel("40")
        self._noise_val.setAlignment(Qt.AlignRight)
        self._noise_val.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 14px; font-family: {FONT_MONO}; "
            f"background: transparent;"
        )
        self._noise_slider.valueChanged.connect(
            lambda v: self._noise_val.setText(str(v))
        )
        noise_layout.addWidget(self._noise_val)
        scroll_layout.addLayout(noise_layout)

        scroll_layout.addWidget(_SectionHeader("OUTPUT FORMAT"))
        self._format_combo = QComboBox()
        self._format_combo.addItems([
            "MP4 (H.264)", "MP4 (H.265)", "MOV", "WebM"
        ])
        self._format_combo.setFixedHeight(36)
        self._format_combo.setStyleSheet(
            f"QComboBox {{"
            f"  background-color: {COLOR_SURFACE};"
            f"  color: {COLOR_TEXT};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 8px;"
            f"  padding: 0 12px;"
            f"  font-family: {FONT_BODY}; font-size: 12px;"
            f"}}"
            f"QComboBox::drop-down {{"
            f"  border: none;"
            f"  width: 24px;"
            f"}}"
            f"QComboBox::down-arrow {{"
            f"  color: {COLOR_MUTED};"
            f"}}"
            f"QComboBox QAbstractItemView {{"
            f"  background-color: {COLOR_ELEVATED};"
            f"  color: {COLOR_TEXT};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 6px;"
            f"  selection-background-color: {COLOR_ACCENT};"
            f"}}"
        )
        scroll_layout.addWidget(self._format_combo)

        scroll_layout.addWidget(_SectionHeader("FRAME INTERPOLATION"))
        self._interp_toggle = _Toggle("Convert 24fps to 60fps", False)
        scroll_layout.addWidget(self._interp_toggle)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

    def toggle(self) -> None:
        if self._is_open:
            self.close_panel()
        else:
            self.open_panel()

    def open_panel(self) -> None:
        self._is_open = True
        self._animate_width(360)

    def close_panel(self) -> None:
        self._is_open = False
        self._animate_width(0)
        self.closed.emit()

    def _animate_width(self, target: int) -> None:
        if self._animation and self._animation.state():
            self._animation.stop()
        self._animation = QPropertyAnimation(self, b"fixedWidth")
        self._animation.setDuration(200)
        self._animation.setStartValue(self.width())
        self._animation.setEndValue(target)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()

    def get_settings(self) -> dict:
        res_btn = self._res_toggle._group.checkedButton()
        resolution = res_btn.text() if res_btn else "1080p"
        mode_btn = self._mode_group.checkedButton()
        mode = mode_btn.text() if mode_btn else "Standard"
        return {
            "resolution": resolution,
            "mode": mode,
            "face_enhance": self._face_toggle.is_checked(),
            "noise_reduction": self._noise_slider.value(),
            "format": self._format_combo.currentText(),
            "interpolation": self._interp_toggle.is_checked(),
        }
