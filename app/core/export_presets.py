import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from app.utils.constants import PROJECT_ROOT
from app.core.processing_pipeline import ProcessingConfig

logger = logging.getLogger(__name__)

PRESETS_PATH: Path = PROJECT_ROOT / "presets.json"

BUILTIN_PRESETS = {
    "Quick 1080p": ProcessingConfig(
        resolution="1080p", mode="Standard",
        face_enhance=False, noise_reduction=20,
        format="MP4 (H.264)", interpolation=False,
    ),
    "High Quality 4K": ProcessingConfig(
        resolution="4K", mode="Standard",
        face_enhance=True, noise_reduction=40,
        format="MP4 (H.265)", interpolation=False,
    ),
    "Anime Upscale": ProcessingConfig(
        resolution="4K", mode="Anime",
        face_enhance=False, noise_reduction=10,
        format="MP4 (H.264)", interpolation=False,
    ),
    "Film Restoration": ProcessingConfig(
        resolution="1080p", mode="Film Grain",
        face_enhance=False, noise_reduction=70,
        format="MOV", interpolation=False,
    ),
    "Full Enhancement": ProcessingConfig(
        resolution="4K", mode="Standard",
        face_enhance=True, noise_reduction=50,
        format="MP4 (H.265)", interpolation=True,
    ),
}


def config_to_dict(cfg: ProcessingConfig) -> dict:
    return asdict(cfg)


def dict_to_config(d: dict) -> ProcessingConfig:
    return ProcessingConfig(**d)


class ExportPresets:
    def __init__(self) -> None:
        self._presets: dict[str, ProcessingConfig] = {}
        self._load()

    def _load(self) -> None:
        for name, cfg in BUILTIN_PRESETS.items():
            self._presets[name] = cfg

        if PRESETS_PATH.exists():
            try:
                with open(PRESETS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for name, cfg_data in data.items():
                    self._presets[name] = dict_to_config(cfg_data)
                logger.info("Loaded %d presets from file", len(data))
            except Exception as e:
                logger.warning("Failed to load presets: %s", e)

    def _save(self) -> None:
        try:
            user_presets = {
                name: config_to_dict(cfg)
                for name, cfg in self._presets.items()
                if name not in BUILTIN_PRESETS
            }
            with open(PRESETS_PATH, "w", encoding="utf-8") as f:
                json.dump(user_presets, f, indent=2)
        except Exception as e:
            logger.error("Failed to save presets: %s", e)

    def list_names(self) -> list[str]:
        return list(self._presets.keys())

    def get(self, name: str) -> Optional[ProcessingConfig]:
        return self._presets.get(name)

    def save_preset(self, name: str, config: ProcessingConfig) -> None:
        self._presets[name] = config
        self._save()
        logger.info("Saved preset: %s", name)

    def delete_preset(self, name: str) -> bool:
        if name in BUILTIN_PRESETS:
            return False
        if name in self._presets:
            del self._presets[name]
            self._save()
            return True
        return False

    @property
    def builtin_names(self) -> list[str]:
        return list(BUILTIN_PRESETS.keys())
