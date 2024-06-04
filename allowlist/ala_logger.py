"""Logger functionality for Flask webapp to control a nginx allowlist."""

import logging
from logging import Logger
from logging.handlers import RotatingFileHandler

LOGLEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"


def setup_logger(ala_sett: dict | None = None) -> Logger:
    """APP LOGGING, set config per ala_sett."""
    # Configure modules that are external and have their own loggers
    logging.getLogger("waitress").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Figure out the settings we will use...
    ala_sett_dict = {"log_level": logging.INFO, "log_path": ""}
    if ala_sett:
        ala_sett_dict["log_level"] = ala_sett.log_level
        ala_sett_dict["log_path"] = ala_sett.log_path

    # Handle our app's logger
    logger = logging.getLogger()
    logger.handlers.clear()
    __set_console_handler(logger)
    __set_log_level(logger, ala_sett_dict["log_level"])

    # If we are logging to a file
    if ala_sett_dict["log_path"] != "":
        __set_file_handler(logger, ala_sett_dict["log_path"])

    if ala_sett:
        logger.info("Logger settings configured!")
    else:
        logger.info("Logger initial setup complete.")


def __set_console_handler(logger: Logger) -> True:
    """Setup the Console handler."""
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)


def __set_log_level(logger: Logger, log_level: int | str) -> True:
    """Sets the log level."""
    if isinstance(log_level, str):
        log_level = log_level.upper()
        if log_level not in LOGLEVELS:
            logger.warning(
                "❗ Invalid logging level: %s, defaulting to INFO",
                logger.getEffectiveLevel(),
            )
        else:
            logger.setLevel(log_level)
            logger.debug("Set log level: %s", log_level)
    else:
        logger.setLevel(log_level)


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
