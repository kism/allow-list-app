"""Flask webapp to control a nginx allowlist."""

import logging

LOGLEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"


def init_logger() -> None:
    """Set logger defaults, before the config is loaded."""
    loglevel = logging.INFO
    logging.basicConfig(format=LOG_FORMAT, level=loglevel)

    logging.getLogger("waitress").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info(" ----------")
    logging.info("🙋 Logger started")


def setup_logger(config_loglevel: str, logpath: str) -> None:
    """APP LOGGING, set config."""
    if config_loglevel:
        config_loglevel = config_loglevel.upper()
        if config_loglevel not in LOGLEVELS:
            logging.warning(
                "❗ Invalid logging level: %s, defaulting to INFO",
                {logging.getLogger().getEffectiveLevel()},
            )
        else:
            logging.basicConfig(format=LOG_FORMAT, level=config_loglevel)

    # logging.getLogger("waitress").setLevel(logging.INFO)
    # logging.getLogger("werkzeug").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)

    try:
        if logpath and logpath != "":  # If we are logging to a file
            logger = logging.getLogger()
            formatter = logging.Formatter(LOG_FORMAT)

            filehandler = logging.FileHandler(logpath)
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler)
            logging.info("Logging to file: %s", logpath)
    except IsADirectoryError as exc:
        err = "You are trying to log to a directory, try a file"
        raise IsADirectoryError(err) from exc

    except PermissionError as exc:
        err = "The user running this does not have access to the file: " + logpath
        raise IsADirectoryError(err) from exc

    logging.info("Logger settings configured")
