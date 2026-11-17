"""FastAPI app factory."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import Config
from .constants import PROGRAM_NAME, PROGRAM_NAME_WITH_FULL_VERSION, STATIC_DIR, TEMPLATES_DIR
from .routers import auth as auth_router
from .services.allowlist import AllowList
from .services.auth import LoginLimiter
from .services.nginx import NGINXAllowlist
from .utils.logger import get_logger, setup_logger

logger = get_logger(__name__)

DEFAULT_INSTANCE_PATH = Path.cwd() / "instance"

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def create_app(config: Config | None = None, instance_path: Path | None = None) -> FastAPI:
    """Create and configure an instance of the FastAPI application.

    Args:
        config: Config to use, loaded from the instance directory if None. Handy for testing.
        instance_path: Directory that holds config.json and the default database.csv, './instance' if None.
    """
    instance_path = instance_path or DEFAULT_INSTANCE_PATH
    config = config or Config.load(instance_path)

    setup_logger(log_level=config.logging.level, log_path=config.logging.path)

    app = FastAPI(title=PROGRAM_NAME, version=PROGRAM_NAME_WITH_FULL_VERSION)
    app.state.config = config
    app.state.instance_path = instance_path
    app.state.login_limiter = LoginLimiter()

    nginx_conf = config.services.nginx
    app.state.allowlist = AllowList(
        db_path=config.app.db_path or instance_path / "database.csv",
        allowed_subnets=config.app.allowed_subnets,
        revert_daily=config.app.revert_daily,
        nginx_allowlist=NGINXAllowlist(nginx_conf.allowlist_path)
        if nginx_conf.enabled and nginx_conf.allowlist_path
        else None,
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(auth_router.router)

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        """Render the home page."""
        return templates.TemplateResponse(
            request=request,
            name="home.html.j2",
            context={
                "hide_username": config.app.auth_type == "static",
                "redirect_url": config.app.redirect_url,
                "version": PROGRAM_NAME_WITH_FULL_VERSION,
            },
        )

    logger.info("Starting %s", PROGRAM_NAME_WITH_FULL_VERSION)
    logger.debug("Instance path is: %s", instance_path)

    return app
