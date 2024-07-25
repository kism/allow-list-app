"""This is specifically for this one variable since its a bit major."""

DYNAMIC_AUTH_TYPES = {
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
