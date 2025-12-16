"""Logger module with colored output for better CLI readability."""

import inspect
import logging
import sys


COLOR_MAP = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[41m",  # Red background
}
RESET_COLOR = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Custom logging formatter that adds color and source metadata."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color and metadata."""
        color = COLOR_MAP.get(record.levelname, "")
        reset = RESET_COLOR if color else ""
        timestamp = self.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S")
        package_name = record.name
        file_name = record.pathname.split("/")[-1]
        line_number = record.lineno
        cls_name = None
        func_name = record.funcName
        try:
            frame = inspect.currentframe()
            while frame:
                if frame.f_code.co_name == func_name:
                    if "self" in frame.f_locals:
                        cls_name = frame.f_locals["self"].__class__.__name__
                    break
                frame = frame.f_back
        except Exception:
            cls_name = None
        cls_part = cls_name if cls_name else None
        method_part = func_name
        if cls_part:
            header = (
                f"{color}[{timestamp}] [{package_name}] {record.levelname} "
                f"[{file_name}:{line_number}:{cls_part}:{method_part}]{reset} {record.getMessage()}"
            )
        else:
            header = (
                f"{color}[{timestamp}] [{package_name}] {record.levelname} "
                f"[{file_name}:{line_number}:{method_part}]{reset} {record.getMessage()}"
            )
        return header


# Create global logger instance
logger = logging.getLogger(name="arithmetic_client_server")
if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(ColoredFormatter())
    logger.addHandler(ch)
