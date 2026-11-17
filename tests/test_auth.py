"""Tests the auth endpoints, static and jellyfin."""

import csv
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
import requests
import responses
from fastapi.testclient import TestClient

from allowlistapp.services.auth import LoginLimiter, check_password_static

from .conftest import CLIENT, JELLYFIN_URL, TEST_PASSWORD

if TYPE_CHECKING:
    from pathlib import Path

    from fastapi import FastAPI

AUTHENTICATE_ENDPOINT = JELLYFIN_URL + "/Users/authenticatebyname"


def test_auth_static_fail(client: TestClient) -> None:
    """TEST: Wrong password is rejected, and the IP isn't in the allowlist."""
    response = client.post("/authenticate/", json={"password": "hunter3"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"authenticated": False}

    response = client.get("/check_auth/")
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_auth_missing_password(client: TestClient) -> None:
    """TEST: The request model rejects a missing password."""
    response = client.post("/authenticate/", json={"username": "bob"})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT


@pytest.mark.parametrize("headers", [{}, {"X-Forwarded-For": "192.168.0.1"}])
def test_auth_static_success(tmp_path: Path, client: TestClient, headers: dict[str, str]) -> None:
    """TEST: Correct password adds the client IP, a client supplied X-Forwarded-For is ignored."""
    response = client.post("/authenticate/", json={"username": "", "password": TEST_PASSWORD}, headers=headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"authenticated": True}

    response = client.get("/check_auth/", headers=headers)
    assert response.status_code == HTTPStatus.OK

    with (tmp_path / "database.csv").open() as f:
        allowlist = list(csv.DictReader(f))

    assert len(allowlist) == 1
    assert allowlist[0]["ip"] == CLIENT[0]
    assert not allowlist[0]["username"]


@pytest.mark.parametrize("username", ["bob\nallow all;", "bob\r", "bob\x00", "a" * 129])
def test_auth_bad_username(client: TestClient, username: str) -> None:
    """TEST: Usernames that could end a log line or the nginx comment are rejected before anything else."""
    response = client.post("/authenticate/", json={"username": username, "password": TEST_PASSWORD})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert client.get("/check_auth/").status_code == HTTPStatus.FORBIDDEN


def test_auth_bad_client_ip(app: FastAPI) -> None:
    """TEST: A client address that isn't an IP is refused, not written to nginx."""
    with TestClient(app) as client:  # Default client host is "testclient"
        response = client.post("/authenticate/", json={"password": TEST_PASSWORD})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_auth_rate_limit(client: TestClient) -> None:
    """TEST: Too many failed logins blocks the client, even with the right password."""
    for _ in range(5):
        assert client.post("/authenticate/", json={"password": "nope"}).status_code == HTTPStatus.FORBIDDEN

    response = client.post("/authenticate/", json={"password": TEST_PASSWORD})
    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_login_limiter_window(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST: Failures expire after the window, IPv6 clients are limited per /64."""
    now = [1000.0]
    monkeypatch.setattr("allowlistapp.services.auth.monotonic", lambda: now[0])
    limiter = LoginLimiter(max_failures=2, window_seconds=60)

    limiter.record_failure("2001:db8::1")
    limiter.record_failure("2001:db8::2")
    assert limiter.is_blocked("2001:db8::ffff")
    assert not limiter.is_blocked("2001:db8:1::1")

    now[0] += 61
    assert not limiter.is_blocked("2001:db8::1")


def test_auth_jellyfin_success(client_jellyfin: TestClient) -> None:
    """TEST: Jellyfin says yes."""
    with responses.RequestsMock() as mock:
        mock.add(responses.POST, AUTHENTICATE_ENDPOINT, json={}, status=HTTPStatus.OK)
        response = client_jellyfin.post("/authenticate/", json={"username": "test", "password": "test"})

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    ("mock_kwargs", "log_text"),
    [
        ({"status": HTTPStatus.FORBIDDEN}, ""),
        ({"body": requests.exceptions.ConnectionError()}, "Connection error for url:"),
        ({"body": requests.exceptions.Timeout()}, "Timeout exception for url:"),
        ({"body": Exception()}, "Uncaught exception for url:"),
    ],
)
def test_auth_jellyfin_failure(
    client_jellyfin: TestClient, caplog: pytest.LogCaptureFixture, mock_kwargs: dict, log_text: str
) -> None:
    """TEST: Jellyfin says no, or can't be reached."""
    with responses.RequestsMock() as mock, caplog.at_level(logging.ERROR):
        mock.add(responses.POST, AUTHENTICATE_ENDPOINT, **mock_kwargs)
        response = client_jellyfin.post("/authenticate/", json={"username": "test", "password": "test"})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert log_text in caplog.text


def test_check_password_static_bad_hash() -> None:
    """TEST: A broken hash fails closed instead of raising."""
    assert not check_password_static("hunter2", "not a hash")
