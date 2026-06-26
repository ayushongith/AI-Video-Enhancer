import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

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
    FONT_BODY, FONT_MONO, OUTPUTS_DIR,
)
from app.utils.config import ConfigManager
from app.core.ffmpeg_detector import FFmpegDetector
from app.core.video_loader import VideoLoader, VideoMetadata
from app.core.processing_pipeline import ProcessingConfig
from app.core.model_manager import ModelManager
from app.core.history_manager import HistoryManager, HistoryEntry
from app.core.gpu_detector import GPUDetector
from app.core.export_presets import ExportPresets, config_to_dict, dict_to_config
from app.gui.toolbar import MainToolbar
from app.gui.sidebar import Sidebar
from app.gui.screens import LandingScreen, ProcessingScreen, ResultScreen, PreviewScreen, BatchScreen, HistoryScreen
from app.gui.settings_panel import SettingsPanel
from app.gui.dialogs.shortcuts_dialog import ShortcutsDialog
from app.gui.dialogs.preset_dialog import PresetDialog
from app.gui.widgets.comparison_view import ComparisonView
from app.gui.widgets.thumbnail_strip import ThumbnailStrip
from app.workers.metadata_worker import MetadataWorker
from app.workers.processing_worker import ProcessingWorker
from app.workers.batch_worker import BatchWorker
from app.workers.thumbnail_worker import ThumbnailWorker

logger = logging.getLogger(__name__)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"

SCREEN_HOME = 0
SCREEN_PREVIEW = 1
SCREEN_PROCESSING = 2
SCREEN_RESULT = 3
SCREEN_BATCH = 4
SCREEN_HISTORY = 5


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: ConfigManager,
        ffmpeg_detector: FFmpegDetector,
    ) -> None:
        super().__init__()
        self._config: ConfigManager = config
        self._ffmpeg: FFmpegDetector = ffmpeg_detector
        self._gpu = GPUDetector()
        self._model_mgr = ModelManager()
        self._history = HistoryManager()
        self._presets = ExportPresets()
        self._current_metadata: Optional[VideoMetadata] = None
        self._current_file_path: Optional[Path] = None
        self._meta_worker: Optional[MetadataWorker] = None
        self._proc_worker: Optional[ProcessingWorker] = None
        self._batch_worker: Optional[BatchWorker] = None

        self._stack: Optional[QStackedWidget] = None
        self._landing: Optional[LandingScreen] = None
        self._preview: Optional[PreviewScreen] = None
        self._processing: Optional[ProcessingScreen] = None
        self._result: Optional[ResultScreen] = None
        self._batch_screen: Optional[BatchScreen] = None
        self._settings_panel: Optional[SettingsPanel] = None
        self._status_ffmpeg: Optional[QLabel] = None
        self._status_msg: Optional[QLabel] = None
        self._status_models: Optional[QLabel] = None
        self._sidebar: Optional[Sidebar] = None
        self._thumbnail_strip: Optional[ThumbnailStrip] = None
        self._comparison_view: Optional[ComparisonView] = None
        self._thumb_worker: Optional[ThumbnailWorker] = None
        self._history_screen: Optional[HistoryScreen] = None

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
        self._register_shortcuts()

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
        toolbar.presets_clicked.connect(self._on_presets)
        toolbar.shortcuts_clicked.connect(self._on_shortcuts)
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
        self._preview.enhance_requested.connect(self._start_enhance)
        self._stack.addWidget(self._preview)

        self._processing = ProcessingScreen()
        self._processing.cancelled.connect(self._on_cancel)
        self._stack.addWidget(self._processing)

        self._result = ResultScreen()
        self._result.upscale_another.connect(self._on_upscale_another)
        self._result.download_requested.connect(self._on_download_video)
        self._stack.addWidget(self._result)

        self._batch_screen = BatchScreen()
        self._batch_screen.files_selected.connect(self._on_batch_files_selected)
        self._batch_screen.start_batch.connect(self._on_batch_start)
        self._batch_screen.cancel_batch.connect(self._on_batch_cancel)
        self._stack.addWidget(self._batch_screen)

        self._history_screen = HistoryScreen()
        self._history_screen.open_result.connect(self._on_history_open)
        self._stack.addWidget(self._history_screen)

        content_layout.addWidget(self._stack)
        sidebar_splitter.addWidget(content_area)
        sidebar_splitter.setSizes([200, 1200])

        body_layout.addWidget(sidebar_splitter, stretch=1)

        self._settings_panel = SettingsPanel()
        self._settings_panel.closed.connect(self._on_settings_closed)
        self._settings_panel.settings_changed.connect(self._on_settings_changed)
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

        models = self._model_mgr.list_available()
        downloaded = sum(1 for m in models if m["downloaded"])
        self._status_models = QLabel(f"Models: {downloaded}/{len(models)}")
        self._status_models.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: 10px; font-family: {FONT_MONO}; "
            f"background: transparent; padding: 0 10px;"
        )
        status_bar.addPermanentWidget(self._status_models)

        gpu_label = QLabel(self._gpu.acceleration_label)
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
        if not urls:
            return
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        if len(paths) == 1:
            self._process_video(paths[0])
        elif len(paths) > 1:
            valid = [p for p in paths if VideoLoader.validate_file(p)[0]]
            if valid and self._batch_screen:
                self._batch_screen.add_files(valid)
                if self._stack:
                    self._stack.setCurrentIndex(SCREEN_BATCH)
                self._sidebar.select_item(1)

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

        self._thumb_worker = ThumbnailWorker(metadata, 12)
        self._thumb_worker.finished.connect(self._on_thumbnails_ready)
        self._thumb_worker.error.connect(lambda e: logger.debug("Thumbnail error: %s", e))
        self._thumb_worker.start()

        if self._stack:
            self._stack.setCurrentIndex(SCREEN_PREVIEW)
        self._sidebar.select_item(1)
        logger.info("Video loaded: %s", metadata.filename)

    def _on_thumbnails_ready(self, frames: list, indices: list) -> None:
        if self._preview:
            self._preview.set_thumbnails(frames, indices)

    def _on_metadata_error(self, error_msg: str) -> None:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(error_msg)
        msg.exec()
        if self._status_msg:
            self._status_msg.setText("Ready to enhance")

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
            Path(self._config.output_directory) if self._config else OUTPUTS_DIR
        )
        output_path = manager.generate_output_path(self._current_metadata, proc_config)

        self._proc_worker = ProcessingWorker(
            self._current_metadata, proc_config, output_path,
            gpu_info=self._gpu.info,
        )
        self._proc_worker.progress.connect(self._on_process_progress)
        self._proc_worker.finished.connect(self._on_process_complete)
        self._proc_worker.error.connect(self._on_process_error)
        self._proc_worker.start()

    def _on_process_progress(self, current: int, total: int, message: str) -> None:
        self._processing.update_progress(current, total, message)

    def _on_process_complete(self, result) -> None:
        self._processing.stop_processing()

        if result.success and self._current_metadata:
            if self._result:
                self._result.show_comparison(
                    getattr(result, "before_frame", None),
                    getattr(result, "after_frame", None),
                )
                if result.output_path:
                    self._result.set_output_path(str(result.output_path))
                meta_rows = [
                    ("Resolution",
                     self._current_metadata.resolution,
                     result.metadata.get("resolution", "")),
                ]
                out_path = Path(result.output_path) if result.output_path else None
                output_size_bytes = 0
                output_size_str = ""
                output_bitrate_str = ""
                if out_path and out_path.exists():
                    output_size_bytes = out_path.stat().st_size
                    output_size_str = _format_size(output_size_bytes)
                    if result.metadata.get("fps") and result.metadata.get("duration"):
                        fps_v = result.metadata["fps"]
                        dur_s = result.metadata["duration"]
                        if fps_v and dur_s:
                            total_bits = size_bytes * 8
                            output_bitrate_str = f"{total_bits / dur_s / 1_000_000:.1f} Mbps"
                meta_rows.append(("Bitrate", self._current_metadata.bitrate or "-", output_bitrate_str or "-"))
                meta_rows.append(("File size", self._current_metadata.size or "-", output_size_str or "-"))
                self._result.set_metadata(meta_rows)

            entry = HistoryEntry(
                filename=self._current_metadata.filename,
                source_path=str(self._current_file_path or ""),
                output_path=str(result.output_path or ""),
                source_resolution=self._current_metadata.resolution,
                output_resolution=result.metadata.get("resolution", ""),
                source_size=self._current_metadata.size,
                output_size=output_size_bytes,
                duration_s=self._current_metadata.duration,
                config={"format": self._config.to_dict() if hasattr(self._config, 'to_dict') else {}},
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            self._history.add_entry(entry)

        if self._stack:
            self._stack.setCurrentIndex(SCREEN_RESULT)
        if self._status_msg:
            self._status_msg.setText("Enhancement complete")
        self._sidebar.select_item(3)

    def _on_process_error(self, error_msg: str) -> None:
        self._processing.stop_processing()
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Processing Error")
        msg.setText(error_msg)
        msg.exec()

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

    def _on_history_open(self, output_path: str) -> None:
        from pathlib import Path as P
        p = P(output_path)
        if p.exists():
            import subprocess
            try:
                subprocess.Popen(["explorer", "/select,", str(p)])
            except Exception:
                QMessageBox.information(self, "File Location", str(p))

    def _on_download_video(self, source_path: str) -> None:
        from pathlib import Path as P
        src = P(source_path)
        if not src.exists():
            QMessageBox.warning(self, "File Not Found", f"Output file not found:\n{source_path}")
            return

        dest, _ = QFileDialog.getSaveFileName(
            self, "Save Upscaled Video", src.name,
            "Video Files (*.mp4 *.mov *.webm);;All Files (*.*)",
        )
        if dest:
            import shutil
            try:
                shutil.copy2(str(src), dest)
                if self._status_msg:
                    self._status_msg.setText(f"Saved to {P(dest).name}")
                logger.info("Video saved to %s", dest)
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save file:\n{e}")

    def _on_upscale_another(self) -> None:
        self._current_metadata = None
        self._current_file_path = None
        self._preview.unload()
        if self._stack:
            self._stack.setCurrentIndex(SCREEN_HOME)
        if self._status_msg:
            self._status_msg.setText("Ready to enhance")
        self._sidebar.select_item(0)

    def _on_batch_files_selected(self, files: list) -> None:
        if self._status_msg:
            self._status_msg.setText(f"Batch: {len(files)} files ready")

    def _on_batch_start(self) -> None:
        if not self._batch_screen:
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

        file_paths = self._batch_screen._files
        if not file_paths:
            return

        self._batch_worker = BatchWorker(file_paths, proc_config, gpu_info=self._gpu.info)
        self._batch_worker.progress.connect(self._on_batch_progress)
        self._batch_worker.finished.connect(self._on_batch_complete)
        self._batch_worker.start()

        if self._status_msg:
            self._status_msg.setText("Batch processing started...")

    def _on_batch_progress(self, current: int, total: int, filename: str, status: str) -> None:
        if self._batch_screen:
            self._batch_screen.set_progress(current, total, filename, status)
        if self._status_msg:
            self._status_msg.setText(f"Batch: {filename} - {status}")

    def _on_batch_complete(self, result) -> None:
        if self._batch_screen:
            self._batch_screen.reset()
        total = result.total if hasattr(result, 'total') else 0
        succeeded = result.succeeded if hasattr(result, 'succeeded') else 0
        failed = result.failed if hasattr(result, 'failed') else 0

        QMessageBox.information(
            self,
            "Batch Complete",
            f"Batch processing finished.\n\n"
            f"Total: {total}\n"
            f"Completed: {succeeded}\n"
            f"Failed: {failed}",
        )
        if self._status_msg:
            self._status_msg.setText(f"Batch complete: {succeeded}/{total} succeeded")

    def _on_batch_cancel(self) -> None:
        if self._batch_worker and self._batch_worker.isRunning():
            self._batch_worker.cancel()
            self._batch_worker.wait(3000)
        if self._batch_screen:
            self._batch_screen.reset()
        if self._status_msg:
            self._status_msg.setText("Batch cancelled")

    def _on_nav_changed(self, item: str) -> None:
        if item == "Home":
            if self._proc_worker and self._proc_worker.isRunning():
                self._proc_worker.cancel()
            self._processing.stop_processing()
            if self._stack:
                self._stack.setCurrentIndex(SCREEN_HOME)
        elif item == "Batch":
            self._batch_screen.reset() if self._batch_screen else None
            if self._stack:
                self._stack.setCurrentIndex(SCREEN_BATCH)
        elif item == "Enhance":
            if self._current_metadata:
                self._start_enhance()
        elif item == "History":
            if self._history_screen:
                self._history_screen.load_entries(self._history.get_all())
            if self._stack:
                self._stack.setCurrentIndex(SCREEN_HISTORY)
        elif item == "Export":
            if self._current_metadata:
                if self._stack:
                    self._stack.setCurrentIndex(SCREEN_RESULT)

    def _on_toggle_settings(self) -> None:
        if self._settings_panel:
            self._settings_panel.toggle()

    def _on_settings_changed(self, settings: dict) -> None:
        if self._config:
            for key in ("resolution", "mode", "format"):
                if key in settings:
                    self._config.set(f"last_{key}", settings[key])
            if "gpu_enabled" in settings:
                self._config.gpu_enabled = settings["gpu_enabled"]

    def _on_settings_closed(self) -> None:
        pass

    def _register_shortcuts(self) -> None:
        from PySide6.QtGui import QShortcut, QKeySequence, QKeyEvent

        mappings = {
            "Ctrl+O": self._on_open_video,
            "Ctrl+S": self._on_toggle_settings,
            "Ctrl+E": lambda: self._on_nav_changed("Enhance") if self._current_metadata else None,
            "Ctrl+B": lambda: self._on_nav_changed("Batch"),
            "Ctrl+P": self._on_presets,
            "Escape": lambda: self._on_nav_changed("Home"),
        }
        for seq, callback in mappings.items():
            s = QShortcut(QKeySequence(seq), self)
            s.activated.connect(callback)

        question = QShortcut(QKeySequence("?"), self)
        question.activated.connect(self._on_shortcuts)

    def _on_presets(self) -> None:
        settings = self._settings_panel.get_settings() if self._settings_panel else {}
        current = ProcessingConfig(
            resolution=settings.get("resolution", "1080p"),
            mode=settings.get("mode", "Standard"),
            face_enhance=settings.get("face_enhance", True),
            noise_reduction=settings.get("noise_reduction", 40),
            format=settings.get("format", "MP4 (H.264)"),
            interpolation=settings.get("interpolation", False),
        )
        dialog = PresetDialog(self._presets, current, self)
        dialog.preset_selected.connect(self._on_preset_selected)
        dialog.exec()

    def _on_preset_selected(self, name: str, config: ProcessingConfig) -> None:
        logger.info("Preset applied: %s", name)
        if self._settings_panel:
            self._settings_panel.apply_preset(config)

    def _on_shortcuts(self) -> None:
        dialog = ShortcutsDialog(self)
        dialog.exec()

    def _on_about(self) -> None:
        models = self._model_mgr.list_available()
        model_status = "\n".join(
            f"  {'[x]' if m['downloaded'] else '[ ]'} {m['description']}"
            for m in models
        )
        QMessageBox.about(
            self,
            "About AI Video Enhancer",
            f"AI Video Enhancer v1.0.0\n\n"
            f"FFmpeg: {'Available' if self._ffmpeg.available else 'Not Found'}\n"
            f"GPU: {self._gpu.acceleration_label}\n"
            f"History: {self._history.count} entries\n\n"
            f"Models:\n{model_status}\n\n"
            f"Press ? for keyboard shortcuts\n\n"
            f"Every pixel, elevated.",
        )
