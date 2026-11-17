"""Tests the app home page and entrypoint."""

import argparse
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import uvicorn
from fastapi import FastAPI

from allowlistapp import __main__
from allowlistapp.config import CONFIG_FILE_NAME
from allowlistapp.constants import PROGRAM_NAME_WITH_FULL_VERSION

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from fastapi.testclient import TestClient


def test_home(client: TestClient) -> None:
    """TEST: The home page renders the form, with the username hidden for static auth."""
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK
    assert 'id="AUTH_FORM"' in response.text
    assert response.text.count('style="display: none;"') == 2  # ruff: ignore[magic-value-comparison] # Username and redirect link
    assert PROGRAM_NAME_WITH_FULL_VERSION in response.text


def test_home_jellyfin(client_jellyfin: TestClient) -> None:
    """TEST: The username field shows for jellyfin auth."""
    assert client_jellyfin.get("/").text.count('style="display: none;"') == 1  # Only the redirect link


def test_static_files(client: TestClient) -> None:
    """TEST: The page's script and css load."""
    for path in ("/static/allowlist.js", "/static/zysystem.css"):
        assert client.get(path).status_code == HTTPStatus.OK


def test_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST: The entrypoint builds an app from the instance config and hands it to uvicorn."""
    (tmp_path / CONFIG_FILE_NAME).write_text(
        '{"app": {"revert_daily": false}, "auth": {"static": {"password_cleartext": "hunter2"}}}'
    )
    mock_args = argparse.Namespace(host="127.0.0.1", port=5000, instance_path=tmp_path, forwarded_allow_ips="127.0.0.1")
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: mock_args)

    served: dict[str, Any] = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: served.update(app=app, **kwargs))

    __main__.main()

    assert isinstance(served["app"], FastAPI)
    assert served["port"] == 5000  # ruff: ignore[magic-value-comparison] # The port we passed in
