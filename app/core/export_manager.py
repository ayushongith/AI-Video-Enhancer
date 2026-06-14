import logging
from pathlib import Path
from typing import Optional

from app.core.video_loader import VideoMetadata
from app.core.processing_pipeline import ProcessingPipeline, ProcessingConfig, ProcessingResult

logger = logging.getLogger(__name__)


class ExportManager:
    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def generate_output_path(
        self,
        metadata: VideoMetadata,
        config: ProcessingConfig,
    ) -> Path:
        stem = Path(metadata.filename).stem
        res = config.resolution.lower().replace("p", "p_")
        ext_map = {
            "MP4 (H.264)": ".mp4",
            "MP4 (H.265)": ".mp4",
            "MOV": ".mov",
            "WebM": ".webm",
        }
        ext = ext_map.get(config.format, ".mp4")
        filename = f"{stem}_enhanced_{res}{ext}"
        return self._output_dir / filename

    def export(
        self,
        metadata: VideoMetadata,
        config: ProcessingConfig,
        output_path: Optional[Path] = None,
        progress_callback=None,
    ) -> ProcessingResult:
        if output_path is None:
            output_path = self.generate_output_path(metadata, config)

        logger.info("Export starting: %s -> %s", metadata.filename, output_path)

        pipeline = ProcessingPipeline(config)
        result = pipeline.process_video(
            metadata, output_path, progress_callback,
        )

        if result.success:
            logger.info("Export complete: %s", output_path)
        else:
            logger.error("Export failed: %s", result.error)

        return result
