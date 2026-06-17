import logging
from typing import Optional

import cv2
import numpy as np

from app.core.enhancers.base_enhancer import BaseEnhancer, EnhancementResult
from app.core.model_manager import ModelManager

logger = logging.getLogger(__name__)


class FaceEnhancer(BaseEnhancer):
    def __init__(self, enabled: bool = True, strength: float = 0.5) -> None:
        super().__init__()
        self._enabled = enabled
        self._strength = max(0.0, min(1.0, strength))
        self._model_mgr = ModelManager()
        self._net: Optional[cv2.dnn.Net] = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def _ensure_net(self) -> Optional[cv2.dnn.Net]:
        if self._net is not None:
            return self._net
        self._net = self._model_mgr.load_face_detector()
        return self._net

    def process(self, frame: np.ndarray) -> EnhancementResult:
        if not self._enabled:
            return EnhancementResult(frame, metadata={"faces": 0})

        net = self._ensure_net()
        if net is None:
            return EnhancementResult(frame, metadata={"faces": 0, "error": "no_model"})

        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(
            frame, 1.0, (300, 300), (104.0, 177.0, 123.0),
        )
        net.setInput(blob)
        detections = net.forward()

        result = frame.copy()
        face_count = 0
        margin = 20

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence < 0.5:
                continue

            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(w, x2 + margin)
            y2 = min(h, y2 + margin)
            if x2 <= x1 or y2 <= y1:
                continue

            face_roi = result[y1:y2, x1:x2]
            if face_roi.size == 0:
                continue

            enhanced = self._enhance_face(face_roi)
            result[y1:y2, x1:x2] = enhanced
            face_count += 1

        return EnhancementResult(result, metadata={"faces": face_count})

    @staticmethod
    def _enhance_face(face: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0],
        ], dtype=np.float32)
        enhanced = cv2.filter2D(enhanced, -1, kernel)

        return enhanced
