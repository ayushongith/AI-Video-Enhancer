import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.core.video_loader import VideoMetadata
from app.utils.constants import TEMP_DIR

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    STRIP_SIZE = (160, 90)

    def __init__(self, metadata: VideoMetadata) -> None:
        self._metadata = metadata

    def generate_strip(
        self, num_frames: int = 12, output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        if self._metadata.path is None or not self._metadata.path.exists():
            return None

        cap = cv2.VideoCapture(str(self._metadata.path))
        if not cap.isOpened():
            return None

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            cap.release()
            return None

        intervals = np.linspace(0, max(total - 1, 1), num_frames, dtype=int)
        thumbnails: list[np.ndarray] = []

        for pos in intervals:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(pos))
            ret, frame = cap.read()
            if ret:
                thumb = cv2.resize(frame, self.STRIP_SIZE, interpolation=cv2.INTER_AREA)
                thumbnails.append(thumb)
            else:
                blank = np.zeros((self.STRIP_SIZE[1], self.STRIP_SIZE[0], 3), dtype=np.uint8)
                thumbnails.append(blank)

        cap.release()

        if not thumbnails:
            return None

        gap = 4
        strip_w = num_frames * (self.STRIP_SIZE[0] + gap) - gap
        strip_h = self.STRIP_SIZE[1]
        strip = np.zeros((strip_h, strip_w, 3), dtype=np.uint8)

        for i, thumb in enumerate(thumbnails):
            x = i * (self.STRIP_SIZE[0] + gap)
            strip[:, x:x + self.STRIP_SIZE[0]] = thumb
            cv2.rectangle(
                strip,
                (x, 0),
                (x + self.STRIP_SIZE[0] - 1, strip_h - 1),
                (30, 30, 50), 1,
            )

        if output_path is None:
            output_path = TEMP_DIR / f"{self._metadata.filename}_strip.jpg"
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), strip)
        logger.info("Thumbnail strip saved: %s", output_path)
        return output_path

    @staticmethod
    def extract_frame(path: Path, timestamp_s: float = 0.0) -> Optional[Path]:
        output = TEMP_DIR / f"frame_{path.stem}_{int(timestamp_s)}.jpg"
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return None

        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_s * 1000)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        cv2.imwrite(str(output), frame)
        return output if output.exists() else None
