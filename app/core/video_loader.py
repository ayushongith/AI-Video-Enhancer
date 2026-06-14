import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.utils.constants import SUPPORTED_VIDEO_EXTENSIONS

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    filename: str = ""
    duration: float = 0.0
    fps: float = 0.0
    width: int = 0
    height: int = 0
    codec: str = ""
    bitrate: int = 0
    size: int = 0
    path: Optional[Path] = None

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def duration_str(self) -> str:
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def bitrate_str(self) -> str:
        if self.bitrate > 0:
            return f"{self.bitrate // 1000} kbps"
        return "N/A"

    @property
    def size_str(self) -> str:
        if self.size > 0:
            mb = self.size / (1024 * 1024)
            if mb > 1024:
                return f"{mb / 1024:.2f} GB"
            return f"{mb:.1f} MB"
        return "N/A"


class VideoLoader:
    @staticmethod
    def validate_file(file_path: Path) -> tuple[bool, str]:
        if not file_path.exists():
            return False, "File does not exist."
        if file_path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
            return False, (
                f"Unsupported format '{file_path.suffix}'. "
                f"Supported: {', '.join(SUPPORTED_VIDEO_EXTENSIONS)}"
            )
        if file_path.stat().st_size == 0:
            return False, "File is empty."
        return True, ""

    @staticmethod
    def load_metadata(file_path: Path) -> Optional[VideoMetadata]:
        logger.info("Loading metadata for: %s", file_path)
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(file_path),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                logger.error("ffprobe failed: %s", result.stderr)
                return None

            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            fmt = data.get("format", {})

            video_stream = next(
                (s for s in streams if s.get("codec_type") == "video"), None
            )
            if not video_stream:
                logger.error("No video stream found in %s", file_path)
                return None

            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))

            fps: float = 0.0
            r_frame_rate = video_stream.get("r_frame_rate", "0/1")
            if "/" in r_frame_rate:
                try:
                    num, den = r_frame_rate.split("/")
                    fps = float(num) / float(den)
                except (ValueError, ZeroDivisionError):
                    fps = 0.0

            duration = float(fmt.get("duration", 0))
            codec = video_stream.get("codec_name", "")
            bitrate_str = fmt.get("bit_rate", "0")
            bitrate = int(bitrate_str) if bitrate_str else 0
            size = int(fmt.get("size", 0))

            metadata = VideoMetadata(
                filename=file_path.name,
                duration=duration,
                fps=round(fps, 2),
                width=width,
                height=height,
                codec=codec.upper(),
                bitrate=bitrate,
                size=size,
                path=file_path,
            )

            logger.info(
                "Metadata extracted: %s | %s | %s fps | %s",
                metadata.filename,
                metadata.resolution,
                metadata.fps,
                metadata.duration_str,
            )
            return metadata

        except subprocess.TimeoutExpired:
            logger.error("ffprobe timed out for %s", file_path)
            return None
        except json.JSONDecodeError as e:
            logger.error("Failed to parse ffprobe output: %s", e)
            return None
        except FileNotFoundError:
            logger.error("ffprobe not found. Is FFmpeg installed?")
            return None
        except Exception as e:
            logger.error("Unexpected error loading metadata: %s", e)
            return None
