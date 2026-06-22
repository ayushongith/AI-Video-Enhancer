import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from app.utils.constants import TEMP_DIR

logger = logging.getLogger(__name__)


@dataclass
class Checkpoint:
    source: str = ""
    output: str = ""
    last_frame: int = 0
    total_frames: int = 0
    config: dict = field(default_factory=dict)
    processed_frames: list[int] = field(default_factory=list)


class Checkpointer:
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._path = TEMP_DIR / f"checkpoint_{session_id}.json"
        self._data = Checkpoint()

    def save(self) -> None:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(asdict(self._data), f, indent=2)
        except Exception as e:
            logger.error("Checkpoint save failed: %s", e)

    def load(self) -> Optional[Checkpoint]:
        if not self._path.exists():
            return None
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._data = Checkpoint(**data)
            logger.info(
                "Checkpoint loaded: frame %d/%d",
                self._data.last_frame, self._data.total_frames,
            )
            return self._data
        except Exception as e:
            logger.warning("Checkpoint load failed: %s", e)
            return None

    def update(self, frame_index: int, total: int, **kwargs) -> None:
        self._data.last_frame = frame_index
        self._data.total_frames = total
        self._data.processed_frames.append(frame_index)
        for k, v in kwargs.items():
            setattr(self._data, k, v)

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()
        self._data = Checkpoint()

    @property
    def has_checkpoint(self) -> bool:
        return self._path.exists() and self._data.last_frame > 0

    @property
    def resume_from(self) -> int:
        return self._data.last_frame + 1
