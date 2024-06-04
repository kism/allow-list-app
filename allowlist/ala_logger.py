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
        __set_log_level(logger, ala_sett.log_level)

    if ala_sett.log_path != "":  # If we are logging to a file
        __set_file_handler(logger, ala_sett.log_path)

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


def __set_log_level(logger: Logger, log_level: str) -> True:
    """Sets the log level."""
    log_level = log_level.upper()
    if log_level not in LOGLEVELS:
        logger.warning(
            "❗ Invalid logging level: %s, defaulting to INFO",
            logger.getEffectiveLevel(),
        )
    else:
        logger.setLevel(log_level)
        logger.debug("Set log level: %s", log_level)


def __set_file_handler(logger: Logger, log_path: str) -> True:
    """Sets up the file handler."""
    try:
        filehandler = RotatingFileHandler(log_path, maxBytes=1000000, backupCount=5)
        formatter = logging.Formatter(LOG_FORMAT)
        filehandler.setFormatter(formatter)
        logger.addHandler(filehandler)
        logger.info("Logging to file: %s", log_path)
    except IsADirectoryError as exc:
        err = "You are trying to log to a directory, try a file"
        raise IsADirectoryError(err) from exc

    except PermissionError as exc:
        err = "The user running this does not have access to the file: " + log_path
        raise IsADirectoryError(err) from exc
