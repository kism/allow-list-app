"""Setup the logger functionality."""

import logging
import typing
from logging.handlers import RotatingFileHandler
from typing import cast

if typing.TYPE_CHECKING:
    from pathlib import Path

LOG_FORMAT = "%(levelname)s:%(name)s:%(message)s"
TRACE_LEVEL_NUM = 5


class CustomLogger(logging.Logger):
    """Custom logger to appease ty."""

    def trace(self, message: typing.Any, *args: typing.Any, **kws: typing.Any) -> None:  # ruff: ignore[any-type] # Typing.any required for logging
        """Create logger level for trace."""
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            # Yes, logger takes its '*args' as 'args'.
            self._log(TRACE_LEVEL_NUM, message, args, **kws)


logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
logging.setLoggerClass(CustomLogger)

logger = cast("CustomLogger", logging.getLogger(__name__))


def get_logger(name: str) -> CustomLogger:
    """Get a logger with the name provided."""
    return cast("CustomLogger", logging.getLogger(name))


def setup_logger(
    log_level: str | int = logging.INFO,
    log_path: Path | None = None,
    in_logger: logging.Logger | None = None,
) -> None:
    """Setup the logger, one console handler and optionally one file handler.

    Args:
        log_level: Logging level to set, "TRACE" and friends or an int.
        log_path: File to log to, no file logging if None.
        in_logger: Logger to configure, the root logger if None. Useful for testing.
    """
    if in_logger is None:
        in_logger = logging.getLogger()  # The root logger, uvicorn's loggers propagate to it.

    if isinstance(log_level, str):
        log_level = logging.getLevelNamesMapping().get(log_level.upper(), logging.INFO)

    in_logger.setLevel(log_level)

    formatter = logging.Formatter(LOG_FORMAT)

    if not any(isinstance(handler, logging.StreamHandler) for handler in in_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        in_logger.addHandler(console_handler)

    if log_path and not any(isinstance(handler, logging.FileHandler) for handler in in_logger.handlers):
        try:
            file_handler = RotatingFileHandler(log_path, maxBytes=1000000, backupCount=3)
        except IsADirectoryError as exc:
            err = "You are trying to log to a directory, try a file"
            raise IsADirectoryError(err) from exc
        except PermissionError as exc:
            err = f"The user running this does not have access to the file: {log_path}"
            raise PermissionError(err) from exc
        file_handler.setFormatter(formatter)
        in_logger.addHandler(file_handler)
        logger.info("Logging to file: %s", log_path)
