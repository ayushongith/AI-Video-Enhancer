import logging
from typing import Optional

import cv2
import numpy as np

from app.core.enhancers.base_enhancer import BaseEnhancer, EnhancementResult

logger = logging.getLogger(__name__)


class Upscaler(BaseEnhancer):
    TARGETS = {"720p": 720, "1080p": 1080, "2K": 1440, "4K": 2160, "8K": 4320}

    def __init__(self, target: str = "1080p") -> None:
        super().__init__()
        self._target: str = target

    @property
    def target_height(self) -> int:
        return self.TARGETS.get(self._target, 1080)

    def process(self, frame: np.ndarray) -> EnhancementResult:
        h, w = frame.shape[:2]
        target_h = self.target_height
        aspect = w / h
        target_w = int(target_h * aspect)

        scaled = cv2.resize(
            frame, (target_w, target_h), interpolation=cv2.INTER_CUBIC
        )

        return EnhancementResult(
            scaled,
            metadata={"method": "bicubic", "from": f"{w}x{h}", "to": f"{target_w}x{target_h}"},
        )


class ESRGANUpscaler(BaseEnhancer):
    def __init__(self, model_path: Optional[str] = None) -> None:
        super().__init__()
        self._model_path = model_path
        self._model = None

    def process(self, frame: np.ndarray) -> EnhancementResult:
        if self._model is None:
            logger.info("ESRGAN model not loaded; falling back to bicubic")
            bicubic = Upscaler("4K")
            return bicubic.process(frame)
        logger.warning("ESRGAN model loading not yet implemented")
        return EnhancementResult(frame)
