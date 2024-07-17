"""Flask webapp allowlistapp."""

from importlib import reload

from flask import Flask, render_template

from . import config, logger

ala_conf = config.AllowListAppConfig()  # Create the default config object


def create_app(test_config: dict | None = None, instance_path: str | None = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)

    logger.setup_logger(app, ala_conf["logging"])  # Setup logger per defaults

    if test_config:  # For Python testing we will often pass in a config
        ala_conf.load_from_dictionary(
            config=test_config, instance_path=app.instance_path
        )  # Loads app config from dict provided
    else:
        ala_conf.load_from_disk(instance_path=app.instance_path)  # Loads app config from disk

    logger.setup_logger(app, ala_conf["logging"])  # Setup logger per config

    app.config.from_mapping(ala_conf["flask"])  # Flask config, separate

    # Do some debug logging of config
    ala_conf.log_config()
    app_config_str = f">>>\nFlask object loaded app.config:\n{app.config.items()}"
    app.logger.debug(app_config_str)

    # Now that we have loaded out configuration, we can import our modules

    from allowlistapp import ala_auth

    reload(ala_auth)

    # Register the authentication endpoint
    app.register_blueprint(ala_auth.bp)

    hide_username = ala_conf.auth_type_static()
    redirect_url = ala_conf["app"]["redirect_url"]

    @app.route("/")
    def home() -> str:
        """Flask Home."""
        return render_template("home.html.j2", hide_username=hide_username, redirect_url=redirect_url)

    return app


def get_allowlistapp_config() -> dict:
    """Return the config object to whatever needs it."""
    return ala_conf
