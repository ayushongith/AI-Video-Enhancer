import logging

import cv2
import numpy as np

from app.core.enhancers.base_enhancer import BaseEnhancer, EnhancementResult

logger = logging.getLogger(__name__)


class Denoiser(BaseEnhancer):
    def __init__(self, strength: int = 10) -> None:
        super().__init__()
        self._strength: int = max(0, min(100, strength))

    def process(self, frame: np.ndarray) -> EnhancementResult:
        h = max(1, 3 + self._strength // 20)
        if h % 2 == 0:
            h += 1
        h_color = max(1, h // 2)
        template_window = max(5, 7 + self._strength // 30)
        if template_window % 2 == 0:
            template_window += 1
        search_window = max(11, 21 + self._strength // 15)
        if search_window % 2 == 0:
            search_window += 1

        denoised = cv2.fastNlMeansDenoisingColored(
            frame, None, h, h_color, template_window, search_window
        )

        return EnhancementResult(denoised, metadata={"strength": self._strength})
