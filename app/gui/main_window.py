import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFrame, QLabel, QStatusBar, QStackedWidget,
    QFileDialog, QMessageBox, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from app.utils.constants import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    SUPPORTED_VIDEO_EXTENSIONS, VIDEO_EXTENSIONS_FILTER,
    STYLESHEET, COLOR_BG, COLOR_SURFACE, COLOR_ELEVATED,
    COLOR_ACCENT, COLOR_TEXT, COLOR_MUTED, COLOR_BORDER,
    FONT_BODY, FONT_MONO,
)
from app.utils.config import ConfigManager
from app.core.ffmpeg_detector import FFmpegDetector
from app.core.video_loader import VideoLoader, VideoMetadata
from app.core.processing_pipeline import ProcessingConfig
from app.gui.toolbar import MainToolbar
from app.gui.sidebar import Sidebar
from app.gui.screens import LandingScreen, ProcessingScreen, ResultScreen, PreviewScreen
from app.gui.settings_panel import SettingsPanel
from app.workers.metadata_worker import MetadataWorker
from app.workers.processing_worker import ProcessingWorker

logger = logging.getLogger(__name__)

SCREEN_HOME = 0
SCREEN_PREVIEW = 1
SCREEN_PROCESSING = 2
SCREEN_RESULT = 3


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: ConfigManager,
        ffmpeg_detector: FFmpegDetector,
    ) -> None:
        super().__init__()
        self._config: ConfigManager = config
        self._ffmpeg: FFmpegDetector = ffmpeg_detector
        self._current_metadata: Optional[VideoMetadata] = None
        self._current_file_path: Optional[Path] = None
        self._meta_worker: Optional[MetadataWorker] = None
        self._proc_worker: Optional[ProcessingWorker] = None

        self._stack: Optional[QStackedWidget] = None
        self._landing: Optional[LandingScreen] = None
        self._preview: Optional[PreviewScreen] = None
        self._processing: Optional[ProcessingScreen] = None
        self._result: Optional[ResultScreen] = None
        self._settings_panel: Optional[SettingsPanel] = None
        self._status_ffmpeg: Optional[QLabel] = None
        self._status_msg: Optional[QLabel] = None
        self._sidebar: Optional[Sidebar] = None

        self._setup_window()
        self._setup_ui()
        self._update_status_bar()
        logger.info("Main window initialized")

    def _setup_window(self) -> None:
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(1000, 600)
        self.setAcceptDrops(True)
        self.setStyleSheet(STYLESHEET)

        screen = self.screen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        toolbar = MainToolbar()
        toolbar.open_clicked.connect(self._on_open_video)
        toolbar.settings_clicked.connect(self._on_toggle_settings)
        toolbar.about_clicked.connect(self._on_about)
        main_layout.addWidget(toolbar)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar_splitter = QSplitter(Qt.Horizontal)
        sidebar_splitter.setHandleWidth(0)
        sidebar_splitter.setChildrenCollapsible(False)

        self._sidebar = Sidebar()
        self._sidebar.navigation_changed.connect(self._on_nav_changed)
        sidebar_splitter.addWidget(self._sidebar)

        content_area = QWidget()
        content_area.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget()

        self._landing = LandingScreen()
        self._landing.video_selected.connect(self._on_landing_cta)
        self._stack.addWidget(self._landing)

        self._preview = PreviewScreen()
        self._stack.addWidget(self._preview)

        self._processing = ProcessingScreen()
        self._processing.cancelled.connect(self._on_cancel)
        self._stack.addWidget(self._processing)

        self._result = ResultScreen()
        self._result.upscale_another.connect(self._on_upscale_another)
        self._stack.addWidget(self._result)

        content_layout.addWidget(self._stack)
        sidebar_splitter.addWidget(content_area)
        sidebar_splitter.setSizes([200, 1200])

        body_layout.addWidget(sidebar_splitter, stretch=1)

        self._settings_panel = SettingsPanel()
        self._settings_panel.closed.connect(self._on_settings_closed)
        body_layout.addWidget(self._settings_panel)

        main_layout.addWidget(body, stretch=1)
        self._setup_status_bar()

    def _setup_status_bar(self) -> None:
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.setStyleSheet("QStatusBar::item { border: none; }")

        self._status_msg = QLabel("Ready to enhance")
        self._status_msg.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 11px; font-weight: 400; "
            f"background: transparent; padding: 0 12px;"
        )
        status_bar.addWidget(self._status_msg, 1)

        self._status_ffmpeg = QLabel(self._ffmpeg.status_text)
        self._status_ffmpeg.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 10px; font-family: {FONT_MONO}; "
            f"background: transparent; padding: 0 10px;"
        )
        status_bar.addPermanentWidget(self._status_ffmpeg)

        gpu_text = "GPU: Enabled" if self._config.gpu_enabled else "GPU: Disabled"
        gpu_label = QLabel(gpu_text)
        gpu_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 10px; font-family: {FONT_MONO}; "
            f"background: transparent; padding: 0 10px;"
        )
        status_bar.addPermanentWidget(gpu_label)

    def _update_status_bar(self) -> None:
        if self._status_ffmpeg:
            self._status_ffmpeg.setText(self._ffmpeg.status_text)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            file_path = Path(urls[0].toLocalFile())
            self._process_video(file_path)

    def _on_landing_cta(self, path: str) -> None:
        if path == "__open_dialog__":
            self._on_open_video()

    def _on_open_video(self) -> None:
        file_path_str, _ = QFileDialog.getOpenFileName(
            self, "Import Video", "", VIDEO_EXTENSIONS_FILTER,
        )
        if file_path_str:
            self._process_video(Path(file_path_str))

    def _process_video(self, file_path: Path) -> None:
        valid, error_msg = VideoLoader.validate_file(file_path)
        if not valid:
            logger.warning("Invalid file: %s - %s", file_path, error_msg)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Invalid File")
            msg.setText(error_msg)
            msg.exec()
            return

        self._current_file_path = file_path
        if self._status_msg:
            self._status_msg.setText(f"Loading {file_path.name}...")

        self._meta_worker = MetadataWorker(file_path)
        self._meta_worker.finished.connect(self._on_metadata_loaded)
        self._meta_worker.error.connect(self._on_metadata_error)
        self._meta_worker.start()

    def _on_metadata_loaded(self, metadata: VideoMetadata) -> None:
        self._current_metadata = metadata
        self._preview.load_video(metadata)
        if self._status_msg:
            self._status_msg.setText(f"Loaded: {metadata.filename}")

        if self._stack:
            self._stack.setCurrentIndex(SCREEN_PREVIEW)
        self._sidebar.select_item(1)
        logger.info("Video loaded: %s", metadata.filename)

    def _on_metadata_error(self, error_msg: str) -> None:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(error_msg)
        msg.exec()
        if self._status_msg:
            self._status_msg.setText("Ready to enhance")
        logger.error("Metadata error: %s", error_msg)

    def _start_enhance(self) -> None:
        if not self._current_metadata or not self._current_file_path:
            return

        settings = self._settings_panel.get_settings() if self._settings_panel else {}
        proc_config = ProcessingConfig(
            resolution=settings.get("resolution", "1080p"),
            mode=settings.get("mode", "Standard"),
            face_enhance=settings.get("face_enhance", True),
            noise_reduction=settings.get("noise_reduction", 40),
            format=settings.get("format", "MP4 (H.264)"),
            interpolation=settings.get("interpolation", False),
        )

        if self._stack:
            self._stack.setCurrentIndex(SCREEN_PROCESSING)
        self._processing.start_processing()

        from app.core.export_manager import ExportManager
        manager = ExportManager(
            Path("outputs") if self._config is None else Path(self._config.output_directory)
        )
        output_path = manager.generate_output_path(self._current_metadata, proc_config)

        self._proc_worker = ProcessingWorker(
            self._current_metadata, proc_config, output_path,
        )
        self._proc_worker.progress.connect(self._on_process_progress)
        self._proc_worker.finished.connect(self._on_process_complete)
        self._proc_worker.error.connect(self._on_process_error)
        self._proc_worker.start()

    def _on_process_progress(self, current: int, total: int, message: str) -> None:
        self._processing.update_progress(current, total, message)

    def _on_process_complete(self, result) -> None:
        self._processing.stop_processing()
        if self._stack:
            self._stack.setCurrentIndex(SCREEN_RESULT)
        if self._status_msg:
            self._status_msg.setText("Enhancement complete")
        self._sidebar.select_item(2)

    def _on_process_error(self, error_msg: str) -> None:
        self._processing.stop_processing()
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Processing Error")
        msg.setText(error_msg)
        msg.exec()
        if self._status_msg:
            self._status_msg.setText("Processing failed")

    def _on_cancel(self) -> None:
        if self._proc_worker and self._proc_worker.isRunning():
            self._proc_worker.cancel()
            self._proc_worker.wait(3000)
        self._processing.stop_processing()
        self._current_metadata = None
        self._current_file_path = None
        self._preview.unload()
        if self._stack:
            self._stack.setCurrentIndex(SCREEN_HOME)
        if self._status_msg:
            self._status_msg.setText("Cancelled")
        self._sidebar.select_item(0)

    def _on_upscale_another(self) -> None:
        self._current_metadata = None
        self._current_file_path = None
        self._preview.unload()
        if self._stack:
            self._stack.setCurrentIndex(SCREEN_HOME)
        if self._status_msg:
            self._status_msg.setText("Ready to enhance")
        self._sidebar.select_item(0)

    def _on_nav_changed(self, item: str) -> None:
        if item == "Home":
            if self._proc_worker and self._proc_worker.isRunning():
                self._proc_worker.cancel()
            self._processing.stop_processing()
            if self._stack:
                self._stack.setCurrentIndex(SCREEN_HOME)
        elif item == "Enhance":
            if self._current_metadata:
                self._start_enhance()
        elif item == "Export":
            if self._current_metadata:
                if self._stack:
                    self._stack.setCurrentIndex(SCREEN_RESULT)

    def _on_toggle_settings(self) -> None:
        if self._settings_panel:
            self._settings_panel.toggle()

    def _on_settings_closed(self) -> None:
        pass

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "About AI Video Enhancer",
            f"AI Video Enhancer v1.0.0\n\n"
            f"FFmpeg: {'Available' if self._ffmpeg.available else 'Not Found'}\n"
            f"GPU: {'Enabled' if self._config.gpu_enabled else 'Disabled'}\n\n"
            f"Every pixel, elevated.",
        )
