"""PyTest, Tests the hello API endpoint."""

import logging
from collections.abc import Callable, Generator
from http import HTTPStatus
from typing import Any

import pytest
import requests
import responses
from flask.testing import FlaskClient
from responses import RequestsMock

AUTHENTICATE_ENDPOINT = "https://jf.example.com/Users/authenticatebyname"


@pytest.fixture
def mock_response_success() -> Generator[RequestsMock, None, None]:
    """Mock a Jellyfin auth success."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            json={},  # Mocked response JSON
            status=HTTPStatus.OK,
        )
        yield mocked_response


def test_auth_success(
    client_url_auth: FlaskClient, mock_response_success: RequestsMock, get_test_config: Callable[[str], dict[str, Any]]
) -> None:
    """TEST: Successful auth via URL."""
    result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert result.status_code == HTTPStatus.OK, "Login should have succeeded"


@pytest.fixture
def mock_response_failure() -> Generator[RequestsMock, None, None]:
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            json={},  # Mocked response JSON
            status=HTTPStatus.FORBIDDEN,
        )
        yield mocked_response


def test_auth_failure(
    client_url_auth: FlaskClient, mock_response_failure: RequestsMock, get_test_config: Callable[[str], dict[str, Any]]
) -> None:
    """TEST: Failed auth via URL."""
    result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert result.status_code == HTTPStatus.FORBIDDEN, "Login should have failed"


@pytest.fixture
def mock_response_connection_error() -> Generator[RequestsMock, None, None]:
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            body=requests.exceptions.ConnectionError(),
        )
        yield mocked_response


def test_auth_connection_error(
    client_url_auth: FlaskClient,
    mock_response_connection_error: RequestsMock,
    get_test_config: Callable[[str], dict[str, Any]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """TEST: Failed auth via URL."""
    with caplog.at_level(logging.ERROR):
        result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert "Connection error for url:" in caplog.text
    assert result.status_code == HTTPStatus.FORBIDDEN


@pytest.fixture
def mock_response_timeout() -> Generator[RequestsMock, None, None]:
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            body=requests.exceptions.Timeout(),
        )
        yield mocked_response


def test_auth_timeout(
    client_url_auth: FlaskClient,
    mock_response_timeout: RequestsMock,
    get_test_config: Callable[[str], dict[str, Any]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """TEST: Failed auth via URL."""
    with caplog.at_level(logging.ERROR):
        result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert "Timeout exception for url:" in caplog.text
    assert result.status_code == HTTPStatus.FORBIDDEN


@pytest.fixture
def mock_response_uncaught_exception() -> Generator[RequestsMock, None, None]:
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            body=Exception(),
        )
        yield mocked_response


def test_auth_uncaught_exception(
    client_url_auth: FlaskClient,
    mock_response_uncaught_exception: RequestsMock,
    get_test_config: Callable[[str], dict[str, Any]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """TEST: Failed auth via URL."""
    with caplog.at_level(logging.ERROR):
        result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert "Uncaught exception for url:" in caplog.text
    assert result.status_code == HTTPStatus.FORBIDDEN
