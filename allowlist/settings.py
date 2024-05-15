"""Settings Processing."""

import logging
import os
import pwd

import yaml
from argon2 import PasswordHasher

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


class AllowListAppSettings:
    """Object Definition for the settings of the app."""

    def __init__(self) -> None:
        """Initiate settings object, get settings from file."""
        # Set default values
        self.allowed_subnets = []
        self.allowlist_path = "ipallowlist.conf"
        self.password_hashed = ""
        self.password_cleartext = ""
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
            logger.info("No configuration file found, creating at default location: %s", self.settings_path)
            self.__write_settings()

        # Load from path
        with open(self.settings_path, encoding="utf8") as yaml_file:
            settings_temp = yaml.safe_load(yaml_file)

        # Get Real Values
        try:
            self.allowlist_path = settings_temp["allowlist_path"]
            self.allowed_subnets = settings_temp["allowed_subnets"]
            self.log_level = settings_temp["log_level"]
            self.log_path = settings_temp["log_path"]
            self.password_cleartext = settings_temp["password_cleartext"]
            self.password_hashed = settings_temp["password_hashed"]
        except (KeyError, TypeError) as exc:
            err_text = (
                f"Error loading settings from: {self.settings_path}, "
                "remove: {self.settings_path} and run the app again to generate a new one"
            )
            raise SettingsLoadError(err_text) from exc

        self.password_cleartext, self.password_hashed = self.__check_settings_password()
        self.__write_settings()

    def __check_settings_password(self) -> str:
        """Check the password parameters in the settings."""
        if self.password_cleartext == "" and self.password_hashed == "":
            err_text = "Please set password in: %s", self.settings_path
            raise SettingsPasswordError(err_text)

        # Hash password if there is a plaintext password set
        if self.password_cleartext != "":
            logger.info("Plaintext password set, hashing and removing from config file")
            plaintext = self.password_cleartext
            hashed = ph.hash(plaintext)
            self.password_hashed = hashed
            self.password_cleartext = ""
        else:
            logger.info("Found hashed password, probably")

        return self.password_cleartext, self.password_hashed

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
