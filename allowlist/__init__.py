"""Flask webapp to control a nginx allowlist."""

import os
import tomllib

from flask import Flask, render_template

from . import ala_logger

ala_logger.setup_logger()


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    if test_config:
        app.config.from_object(test_config)
    else:
        flask_config_path = f"{app.instance_path}{os.sep}flask.toml"
        try:
            app.config.from_file("flask.toml", load=tomllib.load, text=False)
            app.logger.warning("Loaded flask config from: %s, I'M NOT CONVINCED THIS WORKS", flask_config_path)
        except FileNotFoundError:
            app.logger.info("No flask configuration file found at: %s", flask_config_path)
            app.logger.info("Using flask app.config defaults (this is not a problem).")

    # Now that we have loaded out configuration, we can import our modules
    from . import ala_auth

    # Register the authentication endpoint
    app.register_blueprint(ala_auth.bp)

    hide_username = ala_sett.auth_type_static()
    redirect_url = ala_sett.redirect_url

    @app.route("/")
    def home() -> str:
        """Flask Home."""
        return render_template("home.html.j2", hide_username=hide_username, redirect_url=redirect_url)

    return app


def get_ala_settings() -> dict:
    """Return the settings."""
    return ala_sett


if __name__ == "allowlist":  # Is this normal? It might be, the linter doesnt complain about the imports being here.
    from . import ala_settings

    ala_sett = ala_settings.AllowListAppSettings()

    ala_logger.setup_logger(ala_sett)
