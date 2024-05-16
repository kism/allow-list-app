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
    app = Flask(__name__, instance_relative_config=True)

    if test_config:
        app.config.from_object(test_config)
    else:
        try:
            app.config.from_file("flask.toml", load=tomllib.load, text=False)
        except FileNotFoundError:
            err = f"No flask configuration file found at: {app.instance_path}{os.sep}flask.toml. "

            logging.info(err)
            logging.info("Using flask app.config defaults (this is not a problem).")

    # Blueprints
    from . import auth

    app.register_blueprint(auth.bp)

    @app.route("/")
    def home() -> str:
        """Flask Home."""
        return render_template("home.html.j2")

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
