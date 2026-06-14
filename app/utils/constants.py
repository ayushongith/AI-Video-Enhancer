from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
APP_DIR: Path = PROJECT_ROOT / "app"
OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"
TEMP_DIR: Path = PROJECT_ROOT / "temp"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
CONFIG_PATH: Path = PROJECT_ROOT / "config.json"
LOG_FILE: Path = LOGS_DIR / "application.log"

SUPPORTED_VIDEO_EXTENSIONS: list[str] = [".mp4", ".mkv", ".avi", ".mov", ".webm"]
VIDEO_EXTENSIONS_FILTER: str = "Video Files (*.mp4 *.mkv *.avi *.mov *.webm);;All Files (*.*)"

WINDOW_TITLE: str = "AI Video Enhancer"
WINDOW_WIDTH: int = 1400
WINDOW_HEIGHT: int = 850
APP_VERSION: str = "1.0.0"

COLOR_BG = "#0A0A0F"
COLOR_SURFACE = "#13131A"
COLOR_ELEVATED = "#1E1E2E"
COLOR_ACCENT = "#6C63FF"
COLOR_ACCENT_HOVER = "#A78BFA"
COLOR_TEXT = "#E2E8F0"
COLOR_MUTED = "#64748B"
COLOR_BORDER = "#1E1E2E"
COLOR_SUCCESS = "#10B981"
COLOR_ERROR = "#EF4444"

FONT_DISPLAY = "Space Grotesk, Segoe UI, Arial, sans-serif"
FONT_BODY = "Inter, Segoe UI, Arial, sans-serif"
FONT_MONO = "JetBrains Mono, Consolas, Courier New, monospace"

STYLESHEET: str = f"""
QMainWindow, QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: {FONT_BODY};
    font-size: 13px;
}}
QMainWindow::separator {{
    width: 0px;
}}
QToolBar {{
    background-color: {COLOR_BG};
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 6px 14px;
    spacing: 8px;
}}
QToolBar QPushButton {{
    background-color: transparent;
    color: {COLOR_MUTED};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 16px;
    font-family: {FONT_BODY};
    font-size: 12px;
    font-weight: 500;
}}
QToolBar QPushButton:hover {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border-color: {COLOR_BORDER};
}}
QToolBar QPushButton:pressed {{
    background-color: {COLOR_ELEVATED};
}}
QSplitter::handle {{
    background-color: {COLOR_BORDER};
    width: 1px;
}}
QLabel {{
    background-color: transparent;
    color: {COLOR_TEXT};
}}
QLabel[muted="true"] {{
    color: {COLOR_MUTED};
}}
QStatusBar {{
    background-color: {COLOR_BG};
    border-top: 1px solid {COLOR_BORDER};
    color: {COLOR_MUTED};
    font-size: 12px;
    padding: 2px 0px;
    min-height: 26px;
}}
QStatusBar QLabel {{
    background-color: transparent;
    color: {COLOR_MUTED};
    padding: 0 12px;
    font-size: 11px;
}}
QDialog {{
    background-color: {COLOR_ELEVATED};
}}
QMessageBox {{
    background-color: {COLOR_ELEVATED};
}}
QMessageBox QLabel {{
    color: {COLOR_TEXT};
    font-size: 13px;
}}
QMessageBox QPushButton {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 6px 22px;
    min-width: 80px;
    font-family: {FONT_BODY};
}}
QMessageBox QPushButton:hover {{
    background-color: {COLOR_ELEVATED};
}}
QProgressBar {{
    background-color: {COLOR_SURFACE};
    border: none;
    border-radius: 4px;
    text-align: center;
    color: {COLOR_TEXT};
    height: 6px;
}}
QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
    border-radius: 4px;
}}
QScrollBar:vertical {{
    background-color: transparent;
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {COLOR_ELEVATED};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {COLOR_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background-color: transparent;
    height: 6px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {COLOR_ELEVATED};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {COLOR_MUTED};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""
