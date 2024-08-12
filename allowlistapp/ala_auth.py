"""Flask webapp to control a nginx allowlist."""

import json
import logging
from http import HTTPStatus

import requests
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, current_app, request

from . import al_handler, ala_auth_types

REMOTE_AUTH_TYPES: dict = ala_auth_types.REMOTE_AUTH_TYPES

logger = logging.getLogger(__name__)
bp = Blueprint("auth", __name__)
ph = PasswordHasher()
al: al_handler.AllowList | None = None


@bp.route("/check_auth/", methods=["GET"])
def check_auth() -> tuple[str, int]:
    """Test Authenticate."""
    assert al is not None  # noqa: S101 Appease mypy
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        ip = request.environ["REMOTE_ADDR"]
    else:
        ip = request.environ["HTTP_X_FORWARDED_FOR"]

    status = HTTPStatus.FORBIDDEN
    message = "nope"
    if al.is_in_allowlist(ip):
        message = "yep"
        status = HTTPStatus.OK

    return message, status


@bp.route("/authenticate/", methods=["POST"])
def authenticate() -> tuple[str, int]:
    """Post da password."""
    assert al is not None  # noqa: S101 Appease mypy
    username = request.form["username"]
    password = request.form["password"]

    # Check the auth depending on if we are using static auth, or checking via an external url
    result = (
        check_password_static(password)
        if current_app.config["app"]["auth_type"] == "static"
        else check_password_url(username, password)
    )

    message = "nope"
    status = HTTPStatus.FORBIDDEN

    if result:
        status = HTTPStatus.OK
        message = "yep"

    # Get IP
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        ip = request.environ["REMOTE_ADDR"]
    else:
        ip = request.environ["HTTP_X_FORWARDED_FOR"]

    username_text = ""
    if username != "":
        username_text = f", Username: {username}"

    logger.info("Authentication returned: %s for %s%s", message, ip, username_text)

    if result:
        al.add_to_allowlist(username, ip)

    return message, status


def start_allowlist_auth() -> None:
    """Start the allowlist."""
    global al  # noqa: PLW0603 Needed due to how flask loads modules
    al = None  # Prevents tests from getting weird

    al_handler.start_allowlist_handler()

    al = al_handler.AllowList(current_app.config)


def check_password_static(password: str) -> bool:
    """Check password (secure) (I hope)."""
    password_correct = False
    hashed = current_app.config["auth"]["static"]["password_hashed"]
    try:
        ph.verify(hashed, password)
        password_correct = True
    except VerifyMismatchError:
        pass

    return password_correct


def check_password_url(username: str, password: str) -> bool:
    """Check password via Jellyfin (secure) (I hope)."""
    password_correct = False

    url = (
        current_app.config["auth"]["remote"]["url"]
        + "/"
        + REMOTE_AUTH_TYPES[current_app.config["app"]["auth_type"]]["endpoint"]
    )
    headers: dict[str, str] = REMOTE_AUTH_TYPES[current_app.config["app"]["auth_type"]]["headers"]

    data = {
        REMOTE_AUTH_TYPES[current_app.config["app"]["auth_type"]]["username_field"]: username,
        REMOTE_AUTH_TYPES[current_app.config["app"]["auth_type"]]["password_field"]: password,
    }
    json_data = json.dumps(data)

    response = None
    try:
        response = requests.post(url, headers=headers, data=json_data, timeout=5)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error for url: %s", url)  # noqa: TRY400 # We dont need to treat this as an exception
    except requests.exceptions.Timeout:
        logger.error("Timeout exception for url: %s", url)  # noqa: TRY400 # We dont need to treat this as an exception
    except Exception:
        logger.exception("Uncaught exception for url: %s", url)

    if response and response.status_code == HTTPStatus.OK:
        password_correct = True

    return password_correct


logger.debug("Loaded module: %s", __name__)
