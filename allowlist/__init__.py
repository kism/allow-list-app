"""Flask webapp to control a nginx allowlist."""

import logging
import os
import threading
import tomllib

from flask import Flask, render_template  # , request  # , Blueprint  # , jsonify

from . import allowlist, logger, settings

ala_settings = None


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    logger = logging.getLogger("allowlist")

    app = Flask(__name__, instance_relative_config=True)

    if test_config:
        app.config.from_object(test_config)
    else:
        flask_config_path = f"{app.instance_path}{os.sep}flask.toml"
        try:
            app.config.from_file("flask.toml", load=tomllib.load, text=False)
            logger.warning("Loaded flask config from: %s, I'M NOT CONVINCED THIS WORKS", flask_config_path)
        except FileNotFoundError:
            logger.info("No flask configuration file found at: %s", flask_config_path)
            logger.info("Using flask app.config defaults (this is not a problem).")

    # Blueprints
    from . import auth

    app.register_blueprint(auth.bp)

    hide_username = ala_settings.auth_type_static()

    @app.route("/")
    def home() -> str:
        """Flask Home."""
        return render_template("home.html.j2", hide_username=hide_username)

    if not os.path.exists(ala_settings.allowlist_path):  # Create if file doesn't exist
        with open(ala_settings.allowlist_path, "w", encoding="utf8") as conf_file:
            conf_file.write("deny all;")

    thread = threading.Thread(target=allowlist.revert_list_daily, args=(ala_settings,), daemon=True)
    thread.start()

    return app


def get_ala_settings() -> dict:
    """Return the settings."""
    return ala_settings


if __name__ == "allowlist":  # Is this normal?
    ala_settings = settings.AllowListAppSettings()
    logger.setup_logger(ala_settings.log_level, ala_settings.log_path)
