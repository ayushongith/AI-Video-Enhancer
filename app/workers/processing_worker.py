import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from app.core.video_loader import VideoMetadata
from app.core.processing_pipeline import ProcessingConfig
from app.core.export_manager import ExportManager
from app.utils.constants import OUTPUTS_DIR

logger = logging.getLogger(__name__)


class ProcessingWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        metadata: VideoMetadata,
        config: ProcessingConfig,
        output_path: Optional[Path] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._metadata = metadata
        self._config = config
        self._output_path = output_path
        self._cancelled = False

    def run(self) -> None:
        try:
            manager = ExportManager(OUTPUTS_DIR)
            result = manager.export(
                self._metadata,
                self._config,
                self._output_path,
                progress_callback=self._on_progress,
            )

            if self._cancelled:
                return

            if result.success:
                self.finished.emit(result)
            else:
                self.error.emit(result.error or "Processing failed")

        except Exception as e:
            logger.exception("Worker error")
            self.error.emit(str(e))

    def _on_progress(self, current: int, total: int, message: str) -> None:
        if not self._cancelled:
            self.progress.emit(current, total, message)

    def cancel(self) -> None:
        self._cancelled = True
