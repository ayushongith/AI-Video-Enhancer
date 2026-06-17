import logging
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.utils.constants import MODELS_DIR

logger = logging.getLogger(__name__)


MODEL_REGISTRY = {
    "espcn": {
        "url": "https://github.com/fannymonori/TF-ESPCN/raw/master/export/ESPCN_x4.pb",
        "filename": "ESPCN_x4.pb",
        "type": "tensorflow",
        "scale": 4,
        "description": "ESPCN x4 super-resolution",
    },
    "face_detection": {
        "url": "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel",
        "filename": "res10_300x300_ssd_iter_140000.caffemodel",
        "type": "caffe",
        "proto": "deploy.prototxt",
        "description": "OpenCV face detector",
    },
    "face_detection_proto": {
        "url": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
        "filename": "deploy.prototxt",
        "type": "proto",
        "description": "Face detector prototxt",
    },
}


class ModelManager:
    def __init__(self) -> None:
        self._cache: dict[str, tuple] = {}

    def ensure_model(self, model_key: str) -> Optional[Path]:
        entry = MODEL_REGISTRY.get(model_key)
        if entry is None:
            logger.error("Unknown model: %s", model_key)
            return None

        model_path = MODELS_DIR / entry["filename"]
        if model_path.exists():
            logger.debug("Model cached: %s", model_path)
            return model_path

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        url = entry["url"]
        logger.info("Downloading %s from %s...", model_key, url)
        try:
            urllib.request.urlretrieve(url, model_path)
            logger.info("Downloaded: %s", model_path)
            return model_path
        except Exception as e:
            logger.error("Download failed for %s: %s", model_key, e)
            return None

    def ensure_prototxt(self) -> Optional[Path]:
        entry = MODEL_REGISTRY.get("face_detection_proto")
        if entry is None:
            return None
        proto_path = MODELS_DIR / entry["filename"]
        if proto_path.exists():
            return proto_path
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            urllib.request.urlretrieve(entry["url"], proto_path)
            logger.info("Downloaded prototxt: %s", proto_path)
            return proto_path
        except Exception as e:
            logger.error("Prototxt download failed: %s", e)
            return None

    def load_espcn(self) -> Optional[cv2.dnn.Net]:
        model_path = self.ensure_model("espcn")
        if model_path is None:
            return None
        try:
            net = cv2.dnn.readNetFromTensorflow(str(model_path))
            net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            logger.info("ESPCN model loaded")
            return net
        except Exception as e:
            logger.error("Failed to load ESPCN: %s", e)
            return None

    def load_face_detector(self) -> Optional[cv2.dnn.Net]:
        model_path = self.ensure_model("face_detection")
        proto_path = self.ensure_prototxt()
        if model_path is None or proto_path is None:
            return None
        try:
            net = cv2.dnn.readNetFromCaffe(str(proto_path), str(model_path))
            net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            logger.info("Face detection model loaded")
            return net
        except Exception as e:
            logger.error("Failed to load face detector: %s", e)
            return None

    def list_available(self) -> list[dict]:
        available = []
        for key, entry in MODEL_REGISTRY.items():
            model_path = MODELS_DIR / entry["filename"]
            available.append({
                "key": key,
                "description": entry["description"],
                "downloaded": model_path.exists(),
                "scale": entry.get("scale", 1),
            })
        return available
