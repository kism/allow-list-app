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


class SettingsLoadError(Exception):
    """Custom exception for loading the config."""

    def __init__(self, message: str) -> None:
        """Exception code."""
        super().__init__(message)
        self.message = message


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
        # Set default values
        self.allowed_subnets = []
        self.allowlist_path = "ipallowlist.conf"
        self.auth_type = "static"
        self.remote_auth_url = ""
        self.static_password_hashed = ""
        self.static_password_cleartext = ""
        self.log_path = ""
        self.log_level = "INFO"
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

        # Load from path
        with open(self.settings_path, encoding="utf8") as yaml_file:
            settings_temp = yaml.safe_load(yaml_file)

        # Get Real Values
        try:
            self.allowlist_path = settings_temp["allowlist_path"]
            self.allowed_subnets = settings_temp["allowed_subnets"]
            self.auth_type = settings_temp["auth_type"]
            self.log_level = settings_temp["log_level"]
            self.log_path = settings_temp["log_path"]
            self.remote_auth_url = settings_temp["remote_auth_url"]
            self.static_password_cleartext = settings_temp["static_password_cleartext"]
            self.static_password_hashed = settings_temp["static_password_hashed"]
        except (KeyError, TypeError) as exc:
            err_text = (
                f"Error loading settings from: {self.settings_path}, "
                f"remove: {self.settings_path} and run the app again to generate a new one\n"
                f"Problem: {exc}"
            )
            raise SettingsLoadError(err_text) from exc

        # Cleanup to avoid headaches
        self.auth_type = self.auth_type.lower()
        if self.remote_auth_url.endswith("/"):
            self.remote_auth_url = self.remote_auth_url[:-1]

        logger.info("Using authentication type: %s", self.auth_type)
        logger.info("Checking config...")

        if self.auth_type_static():
            self.static_password_cleartext, self.static_password_hashed = self.__check_settings_static_password()
        else:
            self.__check_settings_url_auth()

        self.__write_settings()

    def auth_type_static(self) -> bool:
        """Returns whether the auth type is 'static'."""
        result = True
        if self.auth_type != "static":
            result = False

        return result

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
                settings_write_temp = vars(self)
                del settings_write_temp["settings_path"]
                yaml.safe_dump(settings_write_temp, yaml_file)
        except PermissionError as exc:
            user_account = pwd.getpwuid(os.getuid())[0]
            err = f"Fix permissions: chown {user_account} {self.settings_path}"
            raise PermissionError(err) from exc
