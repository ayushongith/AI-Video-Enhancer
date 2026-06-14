import logging
import sys
from pathlib import Path


class ModuleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        module_name = record.name
        return (
            f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}]\n"
            f"[{record.levelname}]\n"
            f"[{module_name}]\n"
            f"{record.getMessage()}\n"
        )


def setup_logger(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(ModuleFormatter())

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info("Logger initialized. Log file: %s", log_file)
    return logger
