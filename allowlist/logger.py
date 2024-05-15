#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist"""

import logging

LOGLEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logger(config_loglevel, logpath):
    """APP LOGGING"""
    invalid_log_level = False
    loglevel = logging.INFO
    if config_loglevel:
        config_loglevel = config_loglevel.upper()
        if config_loglevel not in LOGLEVELS:
            invalid_log_level = True
        else:
            loglevel = config_loglevel

    logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=loglevel)

    logging.getLogger("waitress").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")

    try:
        if logpath:
            filehandler = logging.FileHandler(logpath)
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler)
    except IsADirectoryError as exc:
        err = "You are trying to log to a directory, try a file"
        raise IsADirectoryError(err) from exc

    except PermissionError as exc:
        err = "The user running this does not have access to the file: " + logpath
        raise IsADirectoryError(err) from exc

    logging.info(" ----------")
    logging.info("🙋 Logger started")
    if invalid_log_level:
        logging.warning("❗ Invalid logging level: %s, defaulting to INFO", {loglevel})
