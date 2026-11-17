"""Router for authenticating and checking if you are in the allowlist."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator

from allowlistapp.services.allowlist import normalise_ip
from allowlistapp.services.auth import check_password_static, check_password_url
from allowlistapp.utils.logger import get_logger

if TYPE_CHECKING:
    from allowlistapp.config import Config
    from allowlistapp.services.allowlist import AllowList
    from allowlistapp.services.auth import LoginLimiter

logger = get_logger(__name__)

router = APIRouter(tags=["auth"])


class AuthRequest(BaseModel):
    """Login form, username is blank for static auth."""

    username: str = Field(default="", max_length=128)
    password: str = Field(max_length=1024)

    @field_validator("username")
    @classmethod
    def username_printable(cls, v: str) -> str:
        """No newlines or control characters, they'd end up in the logs and the nginx config."""
        if not v.isprintable():
            msg = "username contains unprintable characters"
            raise ValueError(msg)
        return v


class AuthResponse(BaseModel):
    """Whether the client IP is (now) in the allowlist."""

    authenticated: bool


def _get_ip(request: Request) -> str:
    """Get the client IP, uvicorn only takes it from X-Forwarded-For when the proxy is in --forwarded-allow-ips."""
    try:
        return normalise_ip(request.client.host if request.client else "")
    except ValueError:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Could not determine the client IP") from None


def _respond(response: Response, *, authenticated: bool) -> AuthResponse:
    response.status_code = HTTPStatus.OK if authenticated else HTTPStatus.FORBIDDEN
    return AuthResponse(authenticated=authenticated)


@router.get("/check_auth/")
def check_auth(request: Request, response: Response) -> AuthResponse:
    """Check if the client IP is in the allowlist."""
    allowlist: AllowList = request.app.state.allowlist
    return _respond(response, authenticated=allowlist.is_in_allowlist(_get_ip(request)))


@router.post("/authenticate/")
def authenticate(body: AuthRequest, request: Request, response: Response) -> AuthResponse:
    """Check the password, add the client IP to the allowlist if correct."""
    config: Config = request.app.state.config
    allowlist: AllowList = request.app.state.allowlist
    limiter: LoginLimiter = request.app.state.login_limiter
    ip = _get_ip(request)

    if limiter.is_blocked(ip):
        logger.warning("Too many failed logins from %s", ip)
        raise HTTPException(HTTPStatus.TOO_MANY_REQUESTS, "Too many failed logins, try again later")

    if config.app.auth_type == "static":
        result = check_password_static(body.password, config.auth.static.password_hashed)
    else:
        result = check_password_url(body.username, body.password, str(config.auth.remote.url), config.app.auth_type)

    username_text = f", Username: {body.username}" if body.username else ""
    logger.info("Authentication returned: %s for %s%s", result, ip, username_text)

    if result:
        allowlist.add_to_allowlist(body.username, ip)
    else:
        limiter.record_failure(ip)

    return _respond(response, authenticated=result)
