import logging
import subprocess
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FFmpegInfo:
    available: bool = False
    version: str = ""
    path: Optional[str] = None


class FFmpegDetector:
    def __init__(self) -> None:
        self._info: FFmpegInfo = FFmpegInfo()
        self._detect()

    def _detect(self) -> None:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                self._info.available = True
                self._info.path = self._find_ffmpeg_path()
                version_match = re.search(
                    r"ffmpeg version\s+(\S+)", result.stdout
                )
                if version_match:
                    self._info.version = version_match.group(1)
                logger.info(
                    "FFmpeg detected: version %s at %s",
                    self._info.version,
                    self._info.path,
                )
            else:
                self._info.available = False
                logger.warning("FFmpeg returned non-zero exit code")
        except FileNotFoundError:
            self._info.available = False
            logger.warning("FFmpeg not found on system PATH")
        except subprocess.TimeoutExpired:
            self._info.available = False
            logger.warning("FFmpeg detection timed out")
        except OSError as e:
            self._info.available = False
            logger.error("Error detecting FFmpeg: %s", e)

    @staticmethod
    def _find_ffmpeg_path() -> Optional[str]:
        try:
            result = subprocess.run(
                ["where", "ffmpeg"] if __import__("sys").platform == "win32"
                else ["which", "ffmpeg"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0].strip()
        except Exception:
            pass
        return None

    @property
    def available(self) -> bool:
        return self._info.available

    @property
    def version(self) -> str:
        return self._info.version

    @property
    def path(self) -> Optional[str]:
        return self._info.path

    @property
    def status_text(self) -> str:
        if self._info.available:
            return f"[OK] FFmpeg Found (v{self._info.version})"
        return "[MISSING] FFmpeg Missing"

    @property
    def info(self) -> FFmpegInfo:
        return self._info
