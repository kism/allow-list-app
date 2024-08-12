"""PyTest, Tests the hello API endpoint."""

import logging
from http import HTTPStatus

import pytest
import requests
import responses
from flask.testing import FlaskClient
from responses import RequestsMock

AUTHENTICATE_ENDPOINT = "https://jf.example.com/Users/authenticatebyname"


@pytest.fixture()
def client_url_auth(tmp_path, get_test_config) -> FlaskClient:
    """This fixture uses the default config within the flask app."""
    from allowlistapp import create_app

    app = create_app(get_test_config("valid_url_auth_url.toml"), instance_path=tmp_path)

    return app.test_client()


@pytest.fixture()
def mock_response_success():
    """Mock a Jellyfin auth success."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            json={},  # Mocked response JSON
            status=HTTPStatus.OK,
        )
        yield mocked_response


def test_auth_success(client_url_auth, mock_response_success: RequestsMock, get_test_config):
    """TEST: Successful auth via URL."""
    result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert result.status_code == HTTPStatus.OK, "Login should have succeeded"


@pytest.fixture()
def mock_response_failure():
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            json={},  # Mocked response JSON
            status=HTTPStatus.FORBIDDEN,
        )
        yield mocked_response


def test_auth_failure(client_url_auth, mock_response_failure: RequestsMock, get_test_config):
    """TEST: Failed auth via URL."""
    result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert result.status_code == HTTPStatus.FORBIDDEN, "Login should have failed"


@pytest.fixture()
def mock_response_connection_error():
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            body=requests.exceptions.ConnectionError(),
        )
        yield mocked_response


def test_auth_connection_error(
    client_url_auth, mock_response_connection_error: RequestsMock, get_test_config, caplog: pytest.LogCaptureFixture
):
    """TEST: Failed auth via URL."""
    with caplog.at_level(logging.ERROR):
        result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert "Connection error for url:" in caplog.text
    assert result.status_code == HTTPStatus.FORBIDDEN


@pytest.fixture()
def mock_response_timeout():
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            body=requests.exceptions.Timeout(),
        )
        yield mocked_response


def test_auth_timeout(
    client_url_auth, mock_response_timeout: RequestsMock, get_test_config, caplog: pytest.LogCaptureFixture
):
    """TEST: Failed auth via URL."""
    with caplog.at_level(logging.ERROR):
        result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert "Timeout exception for url:" in caplog.text
    assert result.status_code == HTTPStatus.FORBIDDEN


@pytest.fixture()
def mock_response_uncaught_exception():
    """Mock a Jellyfin auth failure."""
    with responses.RequestsMock() as mocked_response:
        mocked_response.add(
            responses.POST,
            AUTHENTICATE_ENDPOINT,
            body=Exception,
        )
        yield mocked_response


def test_auth_uncaught_exception(
    client_url_auth, mock_response_uncaught_exception: RequestsMock, get_test_config, caplog: pytest.LogCaptureFixture
):
    """TEST: Failed auth via URL."""
    with caplog.at_level(logging.ERROR):
        result = client_url_auth.post("/authenticate/", data={"username": "test", "password": "test"})

    assert "Uncaught exception for url:" in caplog.text
    assert result.status_code == HTTPStatus.FORBIDDEN
