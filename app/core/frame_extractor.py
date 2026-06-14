import logging
import subprocess
from pathlib import Path
from typing import Optional, Generator

import cv2
import numpy as np

from app.utils.constants import TEMP_DIR
from app.core.video_loader import VideoMetadata

logger = logging.getLogger(__name__)


class FrameExtractor:
    def __init__(self, metadata: VideoMetadata) -> None:
        self._metadata = metadata
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        if self._metadata.path is None:
            logger.error("No file path in metadata")
            return False
        self._cap = cv2.VideoCapture(str(self._metadata.path))
        if not self._cap.isOpened():
            logger.error("Failed to open video: %s", self._metadata.path)
            return False
        logger.info("Opened video: %s", self._metadata.filename)
        return True

    def close(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None

    def total_frames(self) -> int:
        if self._cap is None:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def fps(self) -> float:
        if self._cap is None:
            return 0.0
        return self._cap.get(cv2.CAP_PROP_FPS)

    def read_frame(self) -> Optional[np.ndarray]:
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame

    def seek_frame(self, frame_index: int) -> Optional[np.ndarray]:
        if self._cap is None:
            return None
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame

    def extract_frames(
        self,
        start: int = 0,
        end: Optional[int] = None,
        step: int = 1,
    ) -> Generator[tuple[int, np.ndarray], None, None]:
        if self._cap is None:
            if not self.open():
                return

        total = self.total_frames()
        if end is None or end > total:
            end = total

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        idx = start
        while idx < end:
            ret, frame = self._cap.read()
            if not ret:
                break
            if (idx - start) % step == 0:
                yield idx, frame
            idx += 1

    def extract_frame_at(self, timestamp_s: float) -> Optional[np.ndarray]:
        if self._metadata.path is None:
            return None
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp_s),
            "-i", str(self._metadata.path),
            "-vframes", "1",
            "-f", "image2pipe",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, timeout=30
            )
            if result.returncode != 0 or len(result.stdout) == 0:
                logger.warning("ffmpeg frame extraction failed")
                return None
            arr = np.frombuffer(result.stdout, dtype=np.uint8)
            w = self._metadata.width
            h = self._metadata.height
            expected = w * h * 3
            if len(arr) < expected:
                return None
            frame = arr[:expected].reshape((h, w, 3))
            return frame
        except Exception as e:
            logger.error("Frame extraction error: %s", e)
            return None

    def extract_thumbnail(self, output_path: Path) -> Optional[Path]:
        if self._metadata.path is None:
            return None
        cmd = [
            "ffmpeg",
            "-i", str(self._metadata.path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path),
            "-y",
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=15, check=True)
            if output_path.exists():
                logger.info("Thumbnail saved: %s", output_path)
                return output_path
        except Exception as e:
            logger.error("Thumbnail extraction error: %s", e)
        return None

    def __enter__(self) -> "FrameExtractor":
        self.open()
        return self

    def __exit__(self, *args) -> None:
        self.close()
