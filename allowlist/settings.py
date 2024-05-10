import logging
import sys


def check(app_settings):
    # Settings File
    if app_settings["plaintext_password"] == "" and app_settings["hashed_password"] == "":
        logging.info(
            "Please set password in config.toml",
        )
        sys.exit(1)

    return app_settings
