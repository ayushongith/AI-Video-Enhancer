import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from app.core.batch_processor import BatchProcessor, BatchItem, BatchResult
from app.core.processing_pipeline import ProcessingConfig
from app.utils.constants import OUTPUTS_DIR

logger = logging.getLogger(__name__)


class BatchWorker(QThread):
    progress = Signal(int, int, str, str)
    item_complete = Signal(int, object)
    finished = Signal(object)

    def __init__(
        self,
        file_paths: list[Path],
        config: ProcessingConfig,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._file_paths = file_paths
        self._config = config
        self._cancelled = False

    def run(self) -> None:
        try:
            processor = BatchProcessor(OUTPUTS_DIR, self._config)
            items = processor.build_items(self._file_paths)

            result = BatchResult(total=len(items))

            for idx, item in enumerate(items):
                if self._cancelled:
                    item.status = "cancelled"
                    result.items.append(item)
                    continue

                from app.core.video_loader import VideoLoader, VideoMetadata
                from app.core.processing_pipeline import ProcessingPipeline

                valid, err = VideoLoader.validate_file(item.file_path)
                if not valid:
                    item.status = "failed"
                    item.error = err
                    result.failed += 1
                    result.items.append(item)
                    self.item_complete.emit(idx, item)
                    continue

                self.progress.emit(idx, len(items), item.file_path.name, "Reading metadata...")
                metadata = VideoLoader.load_metadata(item.file_path)
                if metadata is None:
                    item.status = "failed"
                    item.error = "Could not read metadata"
                    result.failed += 1
                    result.items.append(item)
                    self.item_complete.emit(idx, item)
                    continue

                item.metadata = metadata
                stem = metadata.filename.rsplit(".", 1)[0]
                item.output_path = OUTPUTS_DIR / f"{stem}_enhanced.mp4"

                self.progress.emit(idx, len(items), item.file_path.name, "Processing...")

                pipeline = ProcessingPipeline(self._config)

                def make_cb(idx=idx, total=len(items), name=item.file_path.name):
                    def cb(current, total_frames, msg):
                        if not self._cancelled:
                            self.progress.emit(idx, total, name, f"Frame {current}/{total_frames}")
                    return cb

                proc_result = pipeline.process_video(
                    metadata, item.output_path,
                    progress_callback=make_cb(),
                )

                item.result = proc_result
                if proc_result.success:
                    item.status = "completed"
                    result.succeeded += 1
                else:
                    item.status = "failed"
                    item.error = proc_result.error
                    result.failed += 1

                result.items.append(item)
                self.item_complete.emit(idx, item)

            if not self._cancelled:
                self.finished.emit(result)
            else:
                self.finished.emit(result)

        except Exception as e:
            logger.exception("Batch worker error")
            self.finished.emit(BatchResult(total=0, failed=1))

    def cancel(self) -> None:
        self._cancelled = True
