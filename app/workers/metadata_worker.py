import logging
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QThread, Signal

from app.core.video_loader import VideoLoader, VideoMetadata

logger = logging.getLogger(__name__)


class MetadataWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, file_path: Path, parent=None) -> None:
        super().__init__(parent)
        self._file_path: Path = file_path

    def run(self) -> None:
        try:
            metadata: Optional[VideoMetadata] = VideoLoader.load_metadata(
                self._file_path
            )
            if metadata:
                self.finished.emit(metadata)
            else:
                self.error.emit(
                    f"Failed to extract metadata from {self._file_path.name}"
                )
        except Exception as e:
            logger.exception("Metadata worker error")
            self.error.emit(str(e))
