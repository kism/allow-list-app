"""Flask webapp to control a nginx allowlist."""

import logging
import os
import threading
import tomllib

from flask import Flask, render_template  # , request  # , Blueprint  # , jsonify

from . import logger, settings

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

    # Allowlist object, Blueprints
    from . import allowlist, auth, database

    app.register_blueprint(auth.bp)

    # Ensure the databse is ready
    database.init_database(ala_settings)
    # Write the allowlist
    allowlist.write_allowlist_files(ala_settings)

    # See if we need to revert the allowlist daily
    if ala_settings.revert_daily:
        thread = threading.Thread(target=allowlist.revert_list_daily, args=(ala_settings,), daemon=True)
        thread.start()

    hide_username = ala_settings.auth_type_static()

    @app.route("/")
    def home() -> str:
        """Flask Home."""
        return render_template("home.html.j2", hide_username=hide_username)

    return app


def get_ala_settings() -> dict:
    """Return the settings."""
    return ala_settings


if __name__ == "allowlist":  # Is this normal?
    ala_settings = settings.AllowListAppSettings()
    logger.setup_logger(ala_settings.log_level, ala_settings.log_path)
