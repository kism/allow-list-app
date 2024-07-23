"""Flask webapp to control a nginx allowlist."""

import json
import logging
from http import HTTPStatus

import requests
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, request

from . import al_handler

logger = logging.getLogger(__name__)
bp = Blueprint("auth", __name__)
ph = PasswordHasher()

ala_conf = None

al = None


dynamic_auth_types = {
    "jellyfin": {
        "endpoint": "Users/authenticatebyname",
        "username_field": "Username",
        "password_field": "Pw",
        "headers": {
            "Authorization": (
                'MediaBrowser Client="Allowlist App", '
                'Device="Python Flask", '
                'DeviceId="lmao", '
                'Version="0.0", '
                'Token="lmao"'
            ),
            "Content-Type": "application/json",
        },
    },
}


@bp.route("/check_auth/", methods=["GET"])
def check_auth() -> int:
    """Test Authenticate."""
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
def authenticate() -> str:
    """Post da password."""
    username = request.form["username"]
    password = request.form["password"]

    # Check the auth depending on if we are using static auth, or checking via an external url
    result = (
        check_password_static(password)
        if ala_conf["app"]["auth_type"] == "static"
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


def start_allowlist_auth(ala_conf_in: dict) -> None:
    """Start the allowlist."""
    global al  # noqa: PLW0603 Needed due to how flask loads modules
    global ala_conf  # noqa: PLW0603 Needed due to how flask loads modules

    ala_conf = ala_conf_in

    al_handler.start_allowlist_handler(ala_conf)

    al = al_handler.AllowList(ala_conf)


def check_password_static(password: str) -> bool:
    """Check password (secure) (I hope)."""
    password_correct = False
    hashed = ala_conf["app"]["static_password_hashed"]
    try:
        ph.verify(hashed, password)
        password_correct = True
    except VerifyMismatchError:
        pass

    return password_correct


def check_password_url(username: str, password: str) -> bool:
    """Check password via Jellyfin (secure) (I hope)."""
    password_correct = False

    url = ala_conf["app"]["remote_auth_url"] + "/" + dynamic_auth_types[ala_conf["app"]["auth_type"]]["endpoint"]
    headers = dynamic_auth_types[ala_conf["app"]["auth_type"]]["headers"]

    data = {
        dynamic_auth_types[ala_conf["app"]["auth_type"]]["username_field"]: username,
        dynamic_auth_types[ala_conf["app"]["auth_type"]]["password_field"]: password,
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
