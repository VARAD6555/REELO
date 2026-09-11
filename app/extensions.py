"""Central place for Flask extension instances.

Instantiating extensions here (instead of inside the app factory) avoids
circular imports: models and blueprints can `from app.extensions import db`
without needing the app instance itself.
"""

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."
login_manager.login_message_category = "info"
