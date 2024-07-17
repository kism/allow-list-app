"""PyTest, Tests the hello API endpoint."""

import logging
from http import HTTPStatus

import pytest
import requests
import responses

from allowlistapp.ala_auth import check_password_url


@pytest.fixture()
def mock_response_success():
    """Mock a Jellyfin auth success."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            "https://jf.example.com/Users/authenticatebyname",
            json={},  # Mocked response JSON
            status=HTTPStatus.OK,
        )
        yield mocked_response


def test_auth_success(allowlistapp: any, mock_response_success: any, get_test_config: dict):
    """TEST: Successful auth via URL."""
    allowlistapp.create_app(get_test_config("testing_url_valid"))

    result = check_password_url("test", "test")

    assert result, "Login should have succeeded"


@pytest.fixture()
def mock_response_failure():
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            "https://jf.example.com/Users/authenticatebyname",
            json={},  # Mocked response JSON
            status=HTTPStatus.FORBIDDEN,
        )
        yield mocked_response


def test_auth_failure(allowlistapp: any, mock_response_failure: any, get_test_config: dict):
    """TEST: Failed auth via URL."""
    allowlistapp.create_app(get_test_config("testing_url_valid"))

    result = check_password_url("test", "test")

    assert not result, "Login should have failed"


@pytest.fixture()
def mock_response_connection_error():
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            "https://fail.example.com/Users/authenticatebyname",
            body=requests.exceptions.ConnectionError(),
        )
        yield mocked_response


def test_auth_connection_error(
    allowlistapp: any, mock_response_connection_error: any, get_test_config: dict, caplog: pytest.LogCaptureFixture
):
    """TEST: Failed auth via URL."""
    allowlistapp.create_app(get_test_config("testing_url_invalid"))

    with caplog.at_level(logging.ERROR):
        check_password_url("test", "test")

    assert "Connection error for url:" in caplog.text


@pytest.fixture()
def mock_response_timeout():
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            "https://fail.example.com/Users/authenticatebyname",
            body=requests.exceptions.Timeout(),
        )
        yield mocked_response


def test_auth_timeout(
    allowlistapp: any, mock_response_timeout: any, get_test_config: dict, caplog: pytest.LogCaptureFixture
):
    """TEST: Failed auth via URL."""
    allowlistapp.create_app(get_test_config("testing_url_invalid"))

    with caplog.at_level(logging.ERROR):
        check_password_url("test", "test")

    assert "Timeout exception for url:" in caplog.text


@pytest.fixture()
def mock_response_uncaught_exception():
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            "https://fail.example.com/Users/authenticatebyname",
            body=Exception,
        )
        yield mocked_response


def test_auth_uncaught_exception(
    allowlistapp: any, mock_response_uncaught_exception: any, get_test_config: dict, caplog: pytest.LogCaptureFixture
):
    """TEST: Failed auth via URL."""
    allowlistapp.create_app(get_test_config("testing_url_invalid"))

    with caplog.at_level(logging.ERROR):
        check_password_url("test", "test")

    assert "Uncaught exception for url:" in caplog.text
