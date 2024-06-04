"""Logger functionality for Flask webapp to control a nginx allowlist."""

import logging
from logging import Logger
from logging.handlers import RotatingFileHandler

LOGLEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"


def get_logger() -> Logger:
    """Method to get the logger."""
    return logging.getLogger()


def setup_logger(ala_sett: dict) -> Logger:
    """APP LOGGING, set config per ala_sett."""
    logger = __setup_logger()

    if ala_sett.log_level:
        ala_sett.log_level = ala_sett.log_level.upper()
        if ala_sett.log_level not in LOGLEVELS:
            logger.warning(
                "❗ Invalid logging level: %s, defaulting to INFO",
                logger.getEffectiveLevel(),
            )
        else:
            logger.setLevel(ala_sett.log_level)
            logger.debug("Set log level: %s", ala_sett.log_level)

    try:
        if ala_sett.log_path != "":  # If we are logging to a file
            filehandler = logging.RotatingFileHandler(ala_sett.log_path, maxBytes=1000000, backupCount=5)
            formatter = logging.Formatter(LOG_FORMAT)
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler)
            logger.info("Logging to file: %s", ala_sett.log_path)
    except IsADirectoryError as exc:
        err = "You are trying to log to a directory, try a file"
        raise IsADirectoryError(err) from exc

    except PermissionError as exc:
        err = "The user running this does not have access to the file: " + ala_sett.log_path
        raise IsADirectoryError(err) from exc

    logger.info("Logger settings configured!")


def setup_logger_initial() -> Logger:
    """Setup logging while not yet loading settings."""
    logger = __setup_logger(logging.INFO)

    logging.getLogger("waitress").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger.info(" ----------")
    logger.info("🙋 Logger started")

    return logger


def __setup_logger(log_level: str = logging.INFO) -> Logger:
    """Setup Default Console Handler."""
    logger = logging.getLogger()

    logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.setLevel(log_level)

    return logger
