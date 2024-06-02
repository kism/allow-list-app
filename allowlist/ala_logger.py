"""Logger functionality for Flask webapp to control a nginx allowlist."""

import logging
from logging import Logger

LOGLEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"


def setup_logger(module_name: str) -> Logger:
    """APP LOGGING, set config."""
    from . import get_ala_settings

    internal_logger = logging.getLogger(__name__)

    ala_settings = get_ala_settings()

    new_logger = logging.getLogger(module_name)

    if ala_settings.log_level:
        ala_settings.log_level = ala_settings.log_level.upper()
        if ala_settings.log_level not in LOGLEVELS:
            internal_logger.warning(
                "❗ Invalid logging level: %s, defaulting to INFO",
                new_logger.getLogger(module_name).getEffectiveLevel(),
            )
        else:
            new_logger.setLevel(ala_settings.log_level)
            internal_logger.debug("Set log level: %s", ala_settings.log_level)

    try:
        if ala_settings.log_path and ala_settings.log_path != "":  # If we are logging to a file
            new_logger = logging.getLogger(module_name)
            formatter = logging.Formatter(LOG_FORMAT)

            filehandler = logging.FileHandler(ala_settings.log_path)
            filehandler.setFormatter(formatter)
            new_logger.addHandler(filehandler)
            internal_logger.info("Logging to file: %s", ala_settings.log_path)
    except IsADirectoryError as exc:
        err = "You are trying to log to a directory, try a file"
        raise IsADirectoryError(err) from exc

    except PermissionError as exc:
        err = "The user running this does not have access to the file: " + ala_settings.log_path
        raise IsADirectoryError(err) from exc

    internal_logger.info("Logger settings configured")

    return new_logger


def setup_logger_initial(module_name: str) -> Logger:
    """Setup logging while not yet loading settings."""
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
    logger = logging.getLogger(module_name)

    logging.getLogger("waitress").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger.info(" ----------")
    logger.info("🙋 Logger started")
