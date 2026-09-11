"""Application factory.

Building the app with a factory (instead of a single flat script) is what
lets the project have a proper test suite, multiple config environments,
and Flask-Migrate database migrations — the standard structure for a
production Flask project.
"""

import os

from flask import Flask

from config import config_by_name
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.auth import auth_bp
    from app.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    from app import models  # noqa: F401  (ensure models are registered with SQLAlchemy)
    from app.cli import register_cli

    register_cli(app)

    @app.context_processor
    def inject_globals():
        return {"current_year": __import__("datetime").datetime.utcnow().year}

    return app
