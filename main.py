import sys
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont

from app.utils.constants import CONFIG_PATH, LOG_FILE
from app.utils.logger import setup_logger
from app.utils.config import ConfigManager
from app.core.ffmpeg_detector import FFmpegDetector
from app.gui.main_window import MainWindow


def main() -> None:
    setup_logger(LOG_FILE)
    logger = logging.getLogger(__name__)
    logger.info("=== AI Video Enhancer Startup ===")

    try:
        config = ConfigManager(CONFIG_PATH)
        logger.info("Configuration loaded (theme: %s)", config.theme)

        ffmpeg = FFmpegDetector()
        logger.info("FFmpeg detection complete: %s", ffmpeg.status_text)

        app = QApplication(sys.argv)
        app.setApplicationName("AI Video Enhancer")
        app.setOrganizationName("AIVideoEnhancer")

        icon = QPixmap(64, 64)
        icon.fill(Qt.transparent)
        p = QPainter(icon)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor("#6C63FF"))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(4, 4, 56, 56, 12, 12)
        p.setFont(QFont("Segoe UI", 28, QFont.Bold))
        p.setPen(QColor("#ffffff"))
        p.drawText(icon.rect(), Qt.AlignCenter, "AI")
        p.end()
        app.setWindowIcon(QIcon(icon))

        window = MainWindow(config, ffmpeg)
        window.show()

        logger.info("Application started successfully")
        exit_code = app.exec()

        logger.info("=== AI Video Enhancer Shutdown ===")
        sys.exit(exit_code)

    except Exception as e:
        logger.critical("Fatal error during startup: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
