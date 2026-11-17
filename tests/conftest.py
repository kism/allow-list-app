"""The conftest.py file serves as a means of providing fixtures for an entire directory.

Fixtures defined in a conftest.py can be used by any test in that package without needing to import them.

Tests should always use the tmp_path fixture as an instance_path so they don't pollute each other.
"""

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from allowlistapp import create_app
from allowlistapp.config import AppConf, AuthConf, Config, RemoteAuthConf, StaticAuthConf

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from fastapi import FastAPI

TEST_PASSWORD = "hunter2"
JELLYFIN_URL = "https://jf.example.com"
CLIENT = ("127.0.0.1", 50000)  # TestClient defaults to "testclient", which isn't an IP


@pytest.fixture
def config() -> Config:
    """Static auth config, no daily revert so no background thread."""
    return Config(
        app=AppConf(revert_daily=False),
        auth=AuthConf(static=StaticAuthConf(password_cleartext=TEST_PASSWORD)),
    )


@pytest.fixture
def config_jellyfin() -> Config:
    """Jellyfin auth config."""
    return Config(
        app=AppConf(auth_type="jellyfin", revert_daily=False),
        auth=AuthConf(remote=RemoteAuthConf(url=JELLYFIN_URL)),
    )


@pytest.fixture
def app(tmp_path: Path, config: Config) -> FastAPI:
    """App with the static auth config, in a tmp_path instance directory."""
    return create_app(config=config, instance_path=tmp_path)


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient]:
    """Test client for the app."""
    with TestClient(app, client=CLIENT) as test_client:
        yield test_client


@pytest.fixture
def client_jellyfin(tmp_path: Path, config_jellyfin: Config) -> Generator[TestClient]:
    """Test client for the app, with jellyfin auth."""
    with TestClient(create_app(config=config_jellyfin, instance_path=tmp_path), client=CLIENT) as test_client:
        yield test_client
