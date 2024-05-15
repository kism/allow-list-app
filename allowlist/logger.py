"""Flask webapp to control a nginx allowlist."""

import logging

LOGLEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"


def setup_logger(config_loglevel: str, logpath: str) -> None:
    """APP LOGGING, set config."""
    logger = logging.getLogger("allowlist")

    if config_loglevel:
        config_loglevel = config_loglevel.upper()
        if config_loglevel not in LOGLEVELS:
            logger.warning(
                "❗ Invalid logging level: %s, defaulting to INFO",
                logger.getLogger("allowlist").getEffectiveLevel(),
            )
        else:
            logger.setLevel(config_loglevel)
            logger.debug("Set log level: %s", config_loglevel)

    try:
        if logpath and logpath != "":  # If we are logging to a file
            logger = logging.getLogger("allowlist")
            formatter = logging.Formatter(LOG_FORMAT)

            filehandler = logging.FileHandler(logpath)
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler)
            logger.info("Logging to file: %s", logpath)
    except IsADirectoryError as exc:
        err = "You are trying to log to a directory, try a file"
        raise IsADirectoryError(err) from exc

    except PermissionError as exc:
        err = "The user running this does not have access to the file: " + logpath
        raise IsADirectoryError(err) from exc

    logger.info("Logger settings configured")


logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger("allowlist")

logging.getLogger("waitress").setLevel(logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger.info(" ----------")
logger.info("🙋 Logger started")
