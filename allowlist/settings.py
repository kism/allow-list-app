"""Settings Processing."""

import logging
import os
import pwd
import sys

import yaml
from argon2 import PasswordHasher

VALID_URL_AUTH_TYPES = ["static", "jellyfin"]
ph = PasswordHasher()
logger = logging.getLogger("allowlist")
DEFAULT_SETTINGS = {
    "allowlist_path": "ipallowlist.conf",
    "allowed_subnets": [],
    "auth_type": "static",
    "log_level": "INFO",
    "log_path": "",
    "remote_auth_url": "",
    "services": ["nginx"],
    "static_password_cleartext": "",
    "static_password_hashed": "",
    "revert_daily": True,
}


class SettingsPasswordError(Exception):
    """Custom exception for password issues."""

    def __init__(self, message: str) -> None:
        """Exception code."""
        super().__init__(message)
        self.message = message


class SettingsUrlAuthError(Exception):
    """Custom exception for password issues."""

    def __init__(self, message: str) -> None:
        """Exception code."""
        super().__init__(message)
        self.message = message


class AllowListAppSettings:
    """Object Definition for the settings of the app."""

    def __init__(self) -> None:
        """Initiate settings object, get settings from file."""
        # Load the settings from one of the paths
        self.settings_path = None

        paths = []
        paths.append(os.getcwd() + os.sep + "settings.yml")
        paths.append(os.path.expanduser("~/.config/allowlistapp/settings.yml"))
        paths.append("/etc/allowlistapp/settings.yml")

        for path in paths:
            if os.path.exists(path):
                logger.info("Found settings at path: %s", path)
                if not self.settings_path:
                    logger.info("Using this path as it's the first one that was found")
                    self.settings_path = path
            else:
                logger.info("No settings file found at: %s", path)

        if not self.settings_path:
            self.settings_path = paths[0]
            logger.critical("No configuration file found, creating at default location: %s", self.settings_path)
            self.__write_settings()
            logger.critical("Exiting")
            sys.exit(1)

        # Load settings file from path
        with open(self.settings_path, encoding="utf8") as yaml_file:
            settings_temp = yaml.safe_load(yaml_file)

        # Set the variables of this object
        for key, default_value in DEFAULT_SETTINGS.items():
            try:
                setattr(self, key, settings_temp[key])
            except (KeyError, TypeError):
                logging.info("%s not defined, using default", key)
                setattr(self, key, default_value)

        self.__cleanup_config()

        logger.info("Using authentication type: %s", self.auth_type)
        logger.info("Checking config...")

        self.__write_settings()

        if self.auth_type_static():
            self.static_password_cleartext, self.static_password_hashed = self.__check_settings_static_password()
        else:
            self.__check_settings_url_auth()

        self.__write_settings()

        logger.info("Config looks all good!")

    def auth_type_static(self) -> bool:
        """Returns whether the auth type is 'static'."""
        result = True
        if self.auth_type != "static":
            result = False

        return result

    def __cleanup_config(self) -> True:
        """Cleanup the config entries."""
        self.auth_type = self.auth_type.lower()
        self.services = [string.lower() for string in self.services]
        if self.remote_auth_url.endswith("/"):
            self.remote_auth_url = self.remote_auth_url[:-1]

    def __check_settings_url_auth(self) -> True:
        """Check the remote parameters in the settings."""
        if "http" not in self.remote_auth_url:
            err_text = "Please set the auth url, including http(s)://"
            raise SettingsUrlAuthError(err_text)

        if self.auth_type not in VALID_URL_AUTH_TYPES:
            err_text = f"Invalid auth type: {self.auth_type}\nValid Auth types: {VALID_URL_AUTH_TYPES}"
            raise SettingsUrlAuthError(err_text)

        return

    def __check_settings_static_password(self) -> str:
        """Check the password parameters in the settings."""
        if self.static_password_cleartext == "" and self.static_password_hashed == "":
            err_text = f"Please set password in: {self.settings_path}"
            raise SettingsPasswordError(err_text)

        # Hash password if there is a plaintext password set
        if self.static_password_cleartext != "":
            logger.info("Plaintext password set, hashing and removing from config file")
            plaintext = self.static_password_cleartext
            hashed = ph.hash(plaintext)
            self.static_password_hashed = hashed
            self.static_password_cleartext = ""
        else:
            logger.info("Found hashed password, probably")

        return self.static_password_cleartext, self.static_password_hashed

    def __write_settings(self) -> None:
        """Write settings file."""
        try:
            with open(self.settings_path, "w", encoding="utf8") as yaml_file:
                settings_write_temp = vars(self).copy()
                del settings_write_temp["settings_path"]
                yaml.safe_dump(settings_write_temp, yaml_file)
        except PermissionError as exc:
            user_account = pwd.getpwuid(os.getuid())[0]
            err = f"Fix permissions: chown {user_account} {self.settings_path}"
            raise PermissionError(err) from exc
