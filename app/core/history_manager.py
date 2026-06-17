import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from app.utils.constants import PROJECT_ROOT

logger = logging.getLogger(__name__)

HISTORY_PATH: Path = PROJECT_ROOT / "history.json"


@dataclass
class HistoryEntry:
    filename: str = ""
    source_path: str = ""
    output_path: str = ""
    source_resolution: str = ""
    output_resolution: str = ""
    source_size: int = 0
    output_size: int = 0
    duration_s: float = 0.0
    config: dict = field(default_factory=dict)
    timestamp: str = ""


class HistoryManager:
    def __init__(self) -> None:
        self._entries: list[HistoryEntry] = []
        self._load()

    def _load(self) -> None:
        if not HISTORY_PATH.exists():
            return
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = [HistoryEntry(**item) for item in data]
            logger.info("Loaded %d history entries", len(self._entries))
        except Exception as e:
            logger.warning("Failed to load history: %s", e)
            self._entries = []

    def _save(self) -> None:
        try:
            data = [asdict(e) for e in self._entries]
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save history: %s", e)

    def add_entry(self, entry: HistoryEntry) -> None:
        self._entries.insert(0, entry)
        if len(self._entries) > 50:
            self._entries = self._entries[:50]
        self._save()

    def get_all(self) -> list[HistoryEntry]:
        return list(self._entries)

    def get_recent(self, count: int = 5) -> list[HistoryEntry]:
        return self._entries[:count]

    def clear(self) -> None:
        self._entries.clear()
        self._save()

    @property
    def count(self) -> int:
        return len(self._entries)
