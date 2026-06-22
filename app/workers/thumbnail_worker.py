import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from app.core.video_loader import VideoMetadata

logger = logging.getLogger(__name__)


class ThumbnailWorker(QThread):
    finished = Signal(object, object)
    error = Signal(str)

    def __init__(
        self, metadata: VideoMetadata, num_frames: int = 12, parent=None,
    ) -> None:
        super().__init__(parent)
        self._metadata = metadata
        self._num_frames = num_frames

    def run(self) -> None:
        try:
            if self._metadata.path is None:
                self.error.emit("No file path")
                return

            cap = cv2.VideoCapture(str(self._metadata.path))
            if not cap.isOpened():
                self.error.emit("Cannot open video")
                return

            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total <= 0:
                cap.release()
                self.error.emit("No frames in video")
                return

            indices = list(
                set(int(i) for i in np.linspace(0, max(total - 1, 1), self._num_frames))
            )
            indices.sort()

            thumbnails: list[np.ndarray] = []
            for pos in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(pos))
                ret, frame = cap.read()
                if ret:
                    thumb = cv2.resize(frame, (140, 79), interpolation=cv2.INTER_AREA)
                    thumbnails.append(thumb)
                else:
                    blank = np.zeros((79, 140, 3), dtype=np.uint8)
                    thumbnails.append(blank)

            cap.release()

            if thumbnails:
                self.finished.emit(thumbnails, indices)
            else:
                self.error.emit("No thumbnails generated")

        except Exception as e:
            logger.exception("Thumbnail worker error")
            self.error.emit(str(e))
