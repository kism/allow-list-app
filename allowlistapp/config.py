"""Config Processing."""

import contextlib
import logging
import os
import pwd

import tomlkit
from argon2 import PasswordHasher
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

ph = PasswordHasher()

VALID_AUTH_TYPES = ["static", "jellyfin"]


class ConfigPasswordError(Exception):
    """Custom exception for password issues."""

    def __init__(self, message: str) -> None:
        """Exception code."""
        super().__init__(message)
        self.message = message


class ConfigUrlAuthError(Exception):
    """Custom exception for URL auth issues."""

    def __init__(self, message: str) -> None:
        """Exception code."""
        super().__init__(message)
        self.message = message


class ConfigValidationError(Exception):
    """Error to raise if there is a config validation error."""

    def __init__(self, failure: list) -> None:
        """Raise exception with list of config issues."""
        super().__init__(failure)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    path: str = ""


class FlaskConfig(BaseModel):
    """Flask configuration."""

    DEBUG: bool = False
    TESTING: bool = False


class NginxConfig(BaseModel):
    """NGINX service configuration."""

    enabled: bool = False
    allowlist_path: str = ""


class ServicesConfig(BaseModel):
    """Services configuration."""

    nginx: NginxConfig = NginxConfig()


class StaticAuthConfig(BaseModel):
    """Static authentication configuration."""

    password_cleartext: str = ""
    password_hashed: str = ""


class RemoteAuthConfig(BaseModel):
    """Remote authentication configuration."""

    url: str = ""


class AuthConfig(BaseModel):
    """Authentication configuration."""

    remote: RemoteAuthConfig = RemoteAuthConfig()
    static: StaticAuthConfig = StaticAuthConfig()


class AppConfig(BaseModel):
    """Application configuration."""

    allowed_subnets: list[str] = []
    auth_type: str = "static"
    revert_daily: bool = True
    redirect_url: str = ""
    db_path: str = ""


class AllowListAppConfig(BaseSettings):
    """Config Object."""

    model_config = SettingsConfigDict(extra="ignore")

    app: AppConfig = AppConfig()
    services: ServicesConfig = ServicesConfig()
    auth: AuthConfig = AuthConfig()
    logging: LoggingConfig = LoggingConfig()
    flask: FlaskConfig = FlaskConfig()

    def write_config(self, config_path: str) -> None:
        """Write configuration to a TOML file."""
        try:
            with open(config_path, "w", encoding="utf8") as toml_file:
                tomlkit.dump(self.model_dump(), toml_file)
        except PermissionError as exc:
            user_account = pwd.getpwuid(os.getuid())[0]
            err = f"Fix permissions: chown {user_account} {config_path}"
            raise PermissionError(err) from exc

    @classmethod
    def load(cls, instance_path: str, config_data: dict | None = None) -> "AllowListAppConfig":
        """Load, validate, and return config.

        Args:
            instance_path: The flask instance path.
            config_data: If provided, config won't be loaded from a file.
        """
        config_path = cls._resolve_config_path(instance_path)

        if config_data is None:
            config_data = cls._load_file(config_path)

        config = cls(**config_data)

        config.write_config(config_path)

        config._post_validate(instance_path, config_path)

        config.write_config(config_path)

        logger.info("Configuration loaded successfully!")

        return config

    def _post_validate(self, instance_path: str, config_path: str) -> None:
        """Post-load validation and processing."""
        failed_items = []

        if self.flask.TESTING and not any(
            substring in str(instance_path) for substring in ["tmp", "temp", "TMP", "TEMP"]
        ):
            failed_items.append("['flask']['TESTING'] is True but instance_path is not a tmp_path")

        if failed_items:
            raise ConfigValidationError(failed_items)

        if self.app.db_path == "":
            self.app.db_path = os.path.join(str(instance_path), "database.csv")

        if self.app.auth_type == "static":
            self._process_static_password(config_path)
        else:
            self._check_url_auth()

    def _process_static_password(self, config_path: str) -> None:
        """Hash cleartext password if present, validate password is set."""
        if self.auth.static.password_cleartext == "" and self.auth.static.password_hashed == "":
            err_text = f"Please set password in: {config_path}"
            raise ConfigPasswordError(err_text)

        if self.auth.static.password_cleartext != "":
            logger.info("Plaintext password set, hashing and removing from config file")
            self.auth.static.password_hashed = ph.hash(self.auth.static.password_cleartext)
            self.auth.static.password_cleartext = ""
        else:
            logger.info("Found hashed password, probably")

    def _check_url_auth(self) -> None:
        """Validate remote URL auth settings."""
        if self.app.auth_type not in VALID_AUTH_TYPES:
            err_text = f"Invalid auth type: {self.app.auth_type}\nValid Auth types: {VALID_AUTH_TYPES}"
            raise ConfigUrlAuthError(err_text)

        if "http" not in self.auth.remote.url:
            err_text = "Please set the auth url, including http(s)://"
            raise ConfigUrlAuthError(err_text)

    @staticmethod
    def _resolve_config_path(instance_path: str) -> str:
        """Determine the config file path, creating defaults if none found."""
        paths = [
            os.path.join(str(instance_path), "config.toml"),
            os.path.expanduser("~/.config/allowlistapp/config.toml"),
            "/etc/allowlistapp/config.toml",
        ]

        config_path = None
        for path in paths:
            if os.path.isfile(path):
                logger.info("Found config at path: %s", path)
                if not config_path:
                    logger.info("Using this path as it's the first one that was found")
                    config_path = path
            else:
                logger.info("No config file found at: %s", path)

        if not config_path:
            config_path = paths[0]
            logger.warning("No configuration file found, creating at default location: %s", config_path)
            with contextlib.suppress(FileExistsError):
                os.makedirs(str(instance_path))
            try:
                with open(config_path, "w", encoding="utf8") as toml_file:
                    tomlkit.dump(AllowListAppConfig().model_dump(), toml_file)
            except PermissionError as exc:
                user_account = pwd.getpwuid(os.getuid())[0]
                err = f"Fix permissions: chown {user_account} {config_path}"
                raise PermissionError(err) from exc

        return config_path

    @staticmethod
    def _load_file(config_path: str) -> dict:
        """Load configuration from a TOML file."""
        with open(config_path, encoding="utf8") as toml_file:
            return dict(tomlkit.load(toml_file))


logger.debug("Loaded module: %s", __name__)
