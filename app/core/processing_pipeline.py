import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

import cv2
import numpy as np

from app.core.video_loader import VideoMetadata
from app.core.frame_extractor import FrameExtractor
from app.core.enhancers.base_enhancer import BaseEnhancer
from app.core.enhancers.upscaler import Upscaler
from app.core.enhancers.denoiser import Denoiser
from app.core.enhancers.interpolator import FrameInterpolator

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str], None]


@dataclass
class ProcessingConfig:
    resolution: str = "1080p"
    mode: str = "Standard"
    face_enhance: bool = True
    noise_reduction: int = 40
    format: str = "MP4 (H.264)"
    interpolation: bool = False


@dataclass
class ProcessingResult:
    success: bool = False
    output_path: Optional[Path] = None
    total_frames: int = 0
    processed_frames: int = 0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class ProcessingPipeline:
    def __init__(self, config: Optional[ProcessingConfig] = None) -> None:
        self._config = config or ProcessingConfig()
        self._enhancers: list[BaseEnhancer] = []
        self._build_chain()

    def _build_chain(self) -> None:
        self._enhancers.clear()

        if self._config.noise_reduction > 0:
            self._enhancers.append(Denoiser(self._config.noise_reduction))

        self._enhancers.append(Upscaler(self._config.resolution))

        if self._config.interpolation:
            self._enhancers.append(FrameInterpolator(enabled=True))

    def update_config(self, config: ProcessingConfig) -> None:
        self._config = config
        self._build_chain()

    @property
    def enhancers(self) -> list[BaseEnhancer]:
        return list(self._enhancers)

    def process_video(
        self,
        metadata: VideoMetadata,
        output_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> ProcessingResult:
        logger.info(
            "Starting pipeline: %s -> %s (%d enhancers)",
            metadata.filename, output_path, len(self._enhancers),
        )

        result = ProcessingResult()

        try:
            extractor = FrameExtractor(metadata)
            if not extractor.open():
                return ProcessingResult(success=False, error="Failed to open video")

            total = extractor.total_frames()
            result.total_frames = total
            fps = extractor.fps() or 30

            fourcc_map = {
                "MP4 (H.264)": cv2.VideoWriter_fourcc(*"avc1"),
                "MP4 (H.265)": cv2.VideoWriter_fourcc(*"hevc"),
                "MOV": cv2.VideoWriter_fourcc(*"mp4v"),
                "WebM": cv2.VideoWriter_fourcc(*"vp80"),
            }
            fourcc = fourcc_map.get(self._config.format, cv2.VideoWriter_fourcc(*"avc1"))

            first = extractor.read_frame()
            if first is None:
                extractor.close()
                return ProcessingResult(success=False, error="Empty video")

            for enhancer in self._enhancers:
                first = enhancer.process(first).frame

            out_h, out_w = first.shape[:2]
            is_color = len(first.shape) == 3

            writer = cv2.VideoWriter(
                str(output_path), fourcc, fps, (out_w, out_h), is_color,
            )

            processed = 1
            writer.write(first)

            if progress_callback:
                progress_callback(processed, total, f"Frame {processed}/{total}")

            for idx, frame in extractor.extract_frames(start=1):
                current = frame
                for enhancer in self._enhancers:
                    current = enhancer.process(current).frame
                writer.write(current)

                processed += 1
                if progress_callback and processed % max(1, total // 100) == 0:
                    progress_callback(processed, total, f"Frame {processed}/{total}")

            writer.release()
            extractor.close()

            result.success = True
            result.output_path = output_path
            result.processed_frames = processed
            result.metadata = {
                "resolution": f"{out_w}x{out_h}",
                "fps": fps,
                "format": self._config.format,
            }

            logger.info(
                "Pipeline complete: %d frames -> %s",
                processed, output_path,
            )

        except Exception as e:
            logger.exception("Pipeline error")
            result.success = False
            result.error = str(e)

        return result
