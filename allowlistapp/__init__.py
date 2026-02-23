"""Flask webapp allowlistapp."""

from pathlib import Path
from pprint import pformat
from typing import Any

from flask import Flask, render_template

from . import auth, config, logger
from .instances.allowlist import get_allowlist
from .instances.config import get_ala_config
from .version import __version__


def create_app(test_config: dict[str, Any] | None = None, instance_path: str | Path | None = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    instance_path_str = str(instance_path) if instance_path is not None else None
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path_str)  # Create Flask app object

    logger.setup_logger(app, config.LoggingConfig())  # Setup logger with defaults defined in config module

    if test_config and not instance_path:  # For Python testing we will often pass in a config
        app.logger.critical("When testing supply both test_config and instance_path!")
        raise AttributeError(instance_path)

    ala_conf = get_ala_config(
        instance_path=Path(app.instance_path),
        config_data=test_config,
    )

    app.logger.debug("Instance path is: %s", app.instance_path)

    logger.setup_logger(app, ala_conf.logging)  # Setup logger with loaded config

    # Flask config, at the root of the config object.
    app.config.from_mapping(ala_conf.flask.model_dump())

    # Do some debug logging of config
    app_config_str = ">>>\nFlask config:"
    for key, value in app.config.items():
        app_config_str += f"\n  {key}: {pformat(value)}"

    app.logger.debug(app_config_str)

    # Register the authentication endpoint
    app.register_blueprint(auth.bp)

    get_allowlist()

    # Setup vars for template
    hide_username = ala_conf.app.auth_type == "static"
    redirect_url = ala_conf.app.redirect_url

    @app.route("/")
    def home() -> str:
        """Flask Home."""
        return render_template("home.html.j2", hide_username=hide_username, redirect_url=redirect_url)

    app.logger.info("AllowListApp version %s", __version__)

    return app
