"""Password checking, against the static hash or a remote service, and the failed login limiter."""

import ipaddress
import json
import threading
import time
from http import HTTPStatus

import requests
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from pydantic import BaseModel

from allowlistapp.utils.logger import get_logger

logger = get_logger(__name__)

ph = PasswordHasher()


class RemoteAuthType(BaseModel):
    """Remote auth endpoint and payload mapping configuration."""

    endpoint: str
    username_field: str
    password_field: str
    headers: dict[str, str]


REMOTE_AUTH_TYPES: dict[str, RemoteAuthType] = {
    "jellyfin": RemoteAuthType(
        endpoint="Users/authenticatebyname",
        username_field="Username",
        password_field="Pw",
        headers={
            "Authorization": (
                'MediaBrowser Client="Allowlist App", '
                'Device="Python FastAPI", '
                'DeviceId="lmao", '
                'Version="0.0", '
                'Token="lmao"'
            ),
            "Content-Type": "application/json",
        },
    ),
}


def check_password_static(password: str, password_hashed: str) -> bool:
    """Check password against the argon2 hash, anything that isn't a match fails closed."""
    try:
        return ph.verify(password_hashed, password)
    except VerificationError, InvalidHashError:
        return False


def check_password_url(username: str, password: str, base_url: str, auth_type: str) -> bool:
    """Check password via a remote service, e.g. Jellyfin."""
    remote = REMOTE_AUTH_TYPES[auth_type]
    url = base_url.rstrip("/") + "/" + remote.endpoint
    data = json.dumps({remote.username_field: username, remote.password_field: password})

    try:
        response = requests.post(url, headers=remote.headers, data=data, timeout=5)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error for url: %s", url)  # ruff: ignore[error-instead-of-exception] # We dont need to treat this as an exception
    except requests.exceptions.Timeout:
        logger.error("Timeout exception for url: %s", url)  # ruff: ignore[error-instead-of-exception] # We dont need to treat this as an exception
    except Exception:
        logger.exception("Uncaught exception for url: %s", url)
    else:
        return response.status_code == HTTPStatus.OK

    return False


class LoginLimiter:
    """Blocks a client after too many failed logins in a window, in memory."""

    def __init__(self, max_failures: int = 5, window_seconds: float = 60) -> None:
        """Set the limits."""
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(ip: str) -> str:
        """IPv6 clients get a whole /64, so they can't hop addresses to dodge the limit."""
        address = ipaddress.ip_address(ip)
        if address.version == 6:  # ruff: ignore[magic-value-comparison] # IPv6
            return str(ipaddress.ip_network(f"{ip}/64", strict=False))
        return ip

    def is_blocked(self, ip: str) -> bool:
        """Whether this client has too many recent failures."""
        key = self._key(ip)
        now = time.monotonic()
        with self._lock:
            recent = [t for t in self._failures.pop(key, []) if now - t < self.window_seconds]
            if recent:
                self._failures[key] = recent
            return len(recent) >= self.max_failures

    def record_failure(self, ip: str) -> None:
        """Count a failed login."""
        now = time.monotonic()
        with self._lock:
            self._failures.setdefault(self._key(ip), []).append(now)
            # ponytail: clients that fail once and leave are only pruned when the dict gets big
            if len(self._failures) > 10_000:  # ruff: ignore[magic-value-comparison] # Arbitrary memory bound
                self._failures = {
                    k: v for k, v in self._failures.items() if any(now - t < self.window_seconds for t in v)
                }
