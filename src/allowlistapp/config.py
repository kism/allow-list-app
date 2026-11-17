"""Config loading, validating, writing."""

from pathlib import (
    Path,  # ruff: ignore[typing-only-standard-library-import] # Cannot be put in type checking block due to pydantic
)
from typing import Annotated, Literal, Self

import argon2
from argon2 import PasswordHasher
from pydantic import AfterValidator, BaseModel, Field, HttpUrl, model_validator

from .services.allowlist import normalise_ip
from .utils.logger import get_logger

# Logging should be all done at INFO level or higher as the log level hasn't been set yet
logger = get_logger(__name__)

CONFIG_FILE_NAME = "config.json"

ph = PasswordHasher()


def _write_private(path: Path, text: str) -> None:
    """Write a file only the owner can read, it holds the password hash."""
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)  # touch doesn't change the mode of an existing file
    path.write_text(text, encoding="utf8")


class AppConf(BaseModel):
    """Application configuration definition."""

    allowed_subnets: list[Annotated[str, AfterValidator(normalise_ip)]] = []  # Host bits are dropped
    auth_type: Literal["static", "jellyfin"] = "static"
    revert_daily: bool = True
    redirect_url: str = ""
    db_path: Path | None = None  # instance_path / database.csv if None


class NginxConf(BaseModel):
    """NGINX service configuration definition."""

    enabled: bool = False
    allowlist_path: Path | None = None

    @model_validator(mode="after")
    def path_set_if_enabled(self) -> Self:
        """An enabled nginx service needs somewhere to write."""
        if self.enabled and self.allowlist_path is None:
            msg = "NginxConf: allowlist_path must be set when nginx is enabled"
            raise ValueError(msg)
        return self


class ServicesConf(BaseModel):
    """Services configuration definition."""

    nginx: NginxConf = Field(default_factory=NginxConf)


class StaticAuthConf(BaseModel):
    """Static authentication configuration definition."""

    password_cleartext: str = ""
    password_hashed: str = ""


class RemoteAuthConf(BaseModel):
    """Remote authentication configuration definition."""

    url: HttpUrl | None = None


class AuthConf(BaseModel):
    """Authentication configuration definition."""

    remote: RemoteAuthConf = Field(default_factory=RemoteAuthConf)
    static: StaticAuthConf = Field(default_factory=StaticAuthConf)


class LoggingConf(BaseModel):
    """Logging configuration definition."""

    level: str = "INFO"
    path: Path | None = None


class Config(BaseModel):
    """Settings loaded from a JSON file in the instance directory."""

    app: AppConf = Field(default_factory=AppConf)
    services: ServicesConf = Field(default_factory=ServicesConf)
    auth: AuthConf = Field(default_factory=AuthConf)
    logging: LoggingConf = Field(default_factory=LoggingConf)

    @model_validator(mode="after")
    def check_auth(self) -> Self:
        """Hash a cleartext static password, check the selected auth type has what it needs."""
        if self.app.auth_type == "static":
            static = self.auth.static
            if static.password_cleartext:
                logger.info("Plaintext password set, hashing and removing from config file")
                static.password_hashed = ph.hash(static.password_cleartext)
                static.password_cleartext = ""
            if not static.password_hashed:
                msg = "Config: set auth.static.password_cleartext"
                raise ValueError(msg)
            try:
                argon2.extract_parameters(static.password_hashed)
            except argon2.exceptions.InvalidHashError:
                msg = "Config: auth.static.password_hashed isn't an argon2 hash, clear it and set password_cleartext"
                raise ValueError(msg) from None
        elif self.auth.remote.url is None:
            msg = "Config: set auth.remote.url, including http(s)://"
            raise ValueError(msg)
        return self

    @classmethod
    def load(cls, instance_path: Path) -> Self:
        """Load the config from the instance directory, writing it back with any missing defaults filled in."""
        config_path = instance_path / CONFIG_FILE_NAME
        instance_path.mkdir(parents=True, exist_ok=True)

        if not config_path.is_file():
            # The defaults don't validate (no password), write them out so there is a file to fill in.
            _write_private(config_path, cls.model_construct().model_dump_json(indent=2) + "\n")
            logger.warning("No config found, wrote defaults to: %s", config_path)

        config = cls.model_validate_json(config_path.read_text())

        # ponytail: no backup of the old file, git/your backups can have that job
        _write_private(config_path, config.model_dump_json(indent=2) + "\n")
        logger.info("Config loaded from and written to: %s", config_path)

        return config
