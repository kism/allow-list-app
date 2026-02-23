"""Remote auth type definitions."""

from pydantic import BaseModel


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
                'Device="Python Flask", '
                'DeviceId="lmao", '
                'Version="0.0", '
                'Token="lmao"'
            ),
            "Content-Type": "application/json",
        },
    ),
}
