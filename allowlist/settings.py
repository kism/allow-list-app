import logging
import os
import json
import sys

from . import auth
from __init__ import get_args


def get_settings():
    # Settings File
    args = get_args()
    settings = None

    errors_loading = False
    if not os.path.exists(args.settingspath):
        errors_loading = True
        with open(args.settingspath, "w", encoding="utf8") as json_file:
            settings = {
                "path_to_allowlist": "ipallowist.conf",
                "plaintext_password": "",
                "hashed_password": "",
                "allowed_subnets": ["127.0.0.1/32"],
            }
            json.dump(settings, json_file, indent=2)  # indent parameter is optional for pretty formatting
        logging.info("No config file found, creating default")
    else:
        with open(args.settingspath, "r", encoding="utf8") as json_file:
            settings = json.load(json_file)

        settings = auth.process_password(settings)

        with open(args.settingspath, "w", encoding="utf8") as json_file:
            json.dump(settings, json_file, indent=2)  # indent parameter is optional for pretty formatting

    if not errors_loading:
        if settings["plaintext_password"] == "" and settings["hashed_password"] == "":
            errors_loading = True
            logging.info("Please set password in: %s", args.settingspath)

    if errors_loading:
        sys.exit(1)

    return settings
