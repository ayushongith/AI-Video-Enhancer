import logging
from typing import Optional

import cv2
import numpy as np

from app.core.enhancers.base_enhancer import BaseEnhancer, EnhancementResult
from app.core.model_manager import ModelManager

logger = logging.getLogger(__name__)


class DNNUpscaler(BaseEnhancer):
    TARGETS = {"720p": 720, "1080p": 1080, "2K": 1440, "4K": 2160, "8K": 4320}

    def __init__(self, target: str = "1080p") -> None:
        super().__init__()
        self._target: str = target
        self._model_mgr = ModelManager()
        self._net: Optional[cv2.dnn.Net] = None

    @property
    def target_height(self) -> int:
        return self.TARGETS.get(self._target, 1080)

    def _ensure_net(self) -> Optional[cv2.dnn.Net]:
        if self._net is not None:
            return self._net
        self._net = self._model_mgr.load_espcn()
        return self._net

    def process(self, frame: np.ndarray) -> EnhancementResult:
        h, w = frame.shape[:2]
        target_h = self.target_height
        target_w = int(w * (target_h / h))

        net = self._ensure_net()
        if net is not None and h * 4 <= target_h and w * 4 <= target_w:
            try:
                return self._dnn_upscale(frame, net, target_w, target_h)
            except Exception as e:
                logger.warning("DNN upscale failed, falling back: %s", e)

        scaled = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
        return EnhancementResult(
            scaled,
            metadata={"method": "bicubic", "from": f"{w}x{h}", "to": f"{target_w}x{target_h}"},
        )

    def _dnn_upscale(
        self, frame: np.ndarray, net: cv2.dnn.Net,
        target_w: int, target_h: int,
    ) -> EnhancementResult:
        h, w = frame.shape[:2]
        input_blob = cv2.dnn.blobFromImage(
            frame, 1.0 / 255.0, (w, h), (0, 0, 0), swapRB=True, crop=False,
        )
        net.setInput(input_blob)
        output = net.forward()

        output = output.reshape(output.shape[2], output.shape[3], 3)
        output = np.clip(output * 255.0, 0, 255).astype(np.uint8)
        output = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)

        out_h, out_w = output.shape[:2]
        if out_h != target_h or out_w != target_w:
            output = cv2.resize(output, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

        return EnhancementResult(
            output,
            metadata={"method": "espcn", "from": f"{w}x{h}", "to": f"{out_w}x{out_h}"},
        )
