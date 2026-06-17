import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

from app.core.video_loader import VideoMetadata, VideoLoader
from app.core.processing_pipeline import ProcessingConfig, ProcessingPipeline, ProcessingResult

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str, str], None]


@dataclass
class BatchItem:
    file_path: Path
    metadata: Optional[VideoMetadata] = None
    output_path: Optional[Path] = None
    status: str = "pending"
    result: Optional[ProcessingResult] = None
    error: Optional[str] = None


@dataclass
class BatchResult:
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    items: list[BatchItem] = field(default_factory=list)


class BatchProcessor:
    def __init__(self, output_dir: Path, config: ProcessingConfig) -> None:
        self._output_dir = output_dir
        self._config = config
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def build_items(self, file_paths: list[Path]) -> list[BatchItem]:
        items: list[BatchItem] = []
        for fp in file_paths:
            valid, err = VideoLoader.validate_file(fp)
            if valid:
                items.append(BatchItem(file_path=fp))
            else:
                items.append(BatchItem(file_path=fp, status="invalid", error=err))
        return items

    def process_all(
        self,
        items: list[BatchItem],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> BatchResult:
        result = BatchResult(total=len(items))

        for idx, item in enumerate(items):
            if item.status == "invalid":
                result.failed += 1
                continue

            if progress_callback:
                progress_callback(idx, len(items), item.file_path.name, "Loading metadata...")

            valid, err_msg = VideoLoader.validate_file(item.file_path)
            if not valid:
                item.status = "failed"
                item.error = err_msg
                result.failed += 1
                continue

            metadata = VideoLoader.load_metadata(item.file_path)
            if metadata is None:
                item.status = "failed"
                item.error = "Could not read metadata"
                result.failed += 1
                continue

            item.metadata = metadata
            stem = metadata.filename.rsplit(".", 1)[0]
            item.output_path = self._output_dir / f"{stem}_enhanced.mp4"

            if progress_callback:
                progress_callback(idx, len(items), item.file_path.name, "Processing...")

            pipeline = ProcessingPipeline(self._config)
            proc_result = pipeline.process_video(
                metadata,
                item.output_path,
                progress_callback=lambda c, t, m: None,
            )

            item.result = proc_result
            if proc_result.success:
                item.status = "completed"
                result.succeeded += 1
            else:
                item.status = "failed"
                item.error = proc_result.error
                result.failed += 1

            if progress_callback:
                status_text = "Complete" if proc_result.success else f"Failed: {proc_result.error}"
                progress_callback(idx + 1, len(items), item.file_path.name, status_text)

        result.items = items
        return result
