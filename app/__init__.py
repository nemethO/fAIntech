import os
from flask import Flask
from config import config


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    from app.extensions import db, migrate, login_manager
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Import models (registers user_loader and creates table mappings)
    from app import models  # noqa: F401

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.transactions import transactions_bp
    from app.routes.imports import imports_bp
    from app.routes.budget import budget_bp
    from app.routes.analytics import analytics_bp
    from app.routes.chat import chat_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(imports_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(settings_bp)

    return app
