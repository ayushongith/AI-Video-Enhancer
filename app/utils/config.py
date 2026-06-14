import json
import logging
from typing import Any
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "theme": "dark",
    "gpu_enabled": True,
    "output_directory": "outputs",
    "temp_directory": "temp",
    "auto_check_updates": False,
}


class ConfigManager:
    def __init__(self, config_path: Path) -> None:
        self._config_path: Path = config_path
        self._config: dict[str, Any] = dict(DEFAULT_CONFIG)
        self._load()

    def _load(self) -> None:
        try:
            if self._config_path.exists():
                with open(self._config_path, "r", encoding="utf-8") as f:
                    loaded: dict[str, Any] = json.load(f)
                self._config.update(loaded)
                logger.info("Configuration loaded from %s", self._config_path)
            else:
                self._save()
                logger.info(
                    "Default configuration created at %s", self._config_path
                )
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(
                "Failed to load config, using defaults: %s", e
            )

    def _save(self) -> None:
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            logger.debug("Configuration saved to %s", self._config_path)
        except OSError as e:
            logger.error("Failed to save configuration: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value
        self._save()

    def update(self, updates: dict[str, Any]) -> None:
        self._config.update(updates)
        self._save()

    @property
    def theme(self) -> str:
        return str(self._config.get("theme", "dark"))

    @theme.setter
    def theme(self, value: str) -> None:
        self._config["theme"] = value
        self._save()

    @property
    def gpu_enabled(self) -> bool:
        return bool(self._config.get("gpu_enabled", True))

    @gpu_enabled.setter
    def gpu_enabled(self, value: bool) -> None:
        self._config["gpu_enabled"] = value
        self._save()

    @property
    def output_directory(self) -> str:
        return str(self._config.get("output_directory", "outputs"))

    @output_directory.setter
    def output_directory(self, value: str) -> None:
        self._config["output_directory"] = value
        self._save()

    @property
    def temp_directory(self) -> str:
        return str(self._config.get("temp_directory", "temp"))

    @temp_directory.setter
    def temp_directory(self, value: str) -> None:
        self._config["temp_directory"] = value
        self._save()

    def to_dict(self) -> dict[str, Any]:
        return dict(self._config)
