"""Flask webapp allowlistapp."""

from pprint import pformat

from flask import Flask, render_template

from . import config, logger


def create_app(test_config: dict | None = None, instance_path: str | None = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)  # Create Flask app object

    logger.setup_logger(app, config.DEFAULT_CONFIG["logging"])  # Setup logger with defaults defined in config module

    if test_config:  # For Python testing we will often pass in a config
        if not instance_path:
            app.logger.critical("When testing supply both test_config and instance_path!")
            raise AttributeError(instance_path)
        ala_conf = config.AllowListAppConfig(config=test_config, instance_path=app.instance_path)
    else:
        ala_conf = config.AllowListAppConfig(instance_path=app.instance_path)  # Loads app config from disk

    app.logger.debug("Instance path is: %s", app.instance_path)

    logger.setup_logger(app, ala_conf["logging"])  # Setup logger with config

    # Flask config, at the root of the config object.
    app.config.from_mapping(ala_conf["flask"])

    # Do some debug logging of config
    app_config_str = ">>>\nFlask config:"
    for key, value in app.config.items():
        app_config_str += f"\n  {key}: {pformat(value)}"

    app.logger.debug(app_config_str)

    from allowlistapp import ala_auth

    ala_auth.start_allowlist_auth(ala_conf)

    # Register the authentication endpoint
    app.register_blueprint(ala_auth.bp)

    if ala_conf["app"]["auth_type"] == "static":
        hide_username = True
    redirect_url = ala_conf["app"]["redirect_url"]

    @app.route("/")
    def home() -> str:
        """Flask Home."""
        return render_template("home.html.j2", hide_username=hide_username, redirect_url=redirect_url)

    app.logger.info("Starting Web Server")

    return app
