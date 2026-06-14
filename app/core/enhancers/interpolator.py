import logging

import numpy as np

from app.core.enhancers.base_enhancer import BaseEnhancer, EnhancementResult

logger = logging.getLogger(__name__)


class FrameInterpolator(BaseEnhancer):
    def __init__(self, enabled: bool = False) -> None:
        super().__init__()
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def process(self, frame: np.ndarray) -> EnhancementResult:
        return EnhancementResult(frame, metadata={"interpolated": False})
