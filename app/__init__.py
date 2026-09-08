"""
Flask Application Factory.
Creates and configures the Flask application.
"""
import os
from flask import Flask, request, session, render_template

from app.extensions import db, login_manager, babel, csrf, migrate
from app.config import config


def get_locale():
    """Determine the best locale for the current request."""
    # 1. User session preference
    lang = session.get('language')
    if lang:
        return lang

    # 2. Authenticated user preference
    from flask_login import current_user
    if current_user and hasattr(current_user, 'PreferredLanguage') and current_user.PreferredLanguage:
        return current_user.PreferredLanguage

    # 3. Browser Accept-Language header
    from flask import current_app
    return request.accept_languages.best_match(
        current_app.config.get('SUPPORTED_LANGUAGES', ['it', 'en'])
    )


def create_app(config_name: str = None) -> Flask:
    """Application factory for the Flask app."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # --- Initialize extensions ---
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Per favore accedi per accedere a questa pagina.'
    login_manager.login_message_category = 'info'

    babel.init_app(app, locale_selector=get_locale)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # --- User loader for Flask-Login ---
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.auth import User
        return db.session.get(User, int(user_id))

    # --- Register Blueprints ---
    from app.modules.auth import auth_bp
    from app.modules.dashboard import dashboard_bp
    from app.modules.employees import employees_bp
    from app.modules.needs import needs_bp
    from app.modules.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(needs_bp)
    app.register_blueprint(admin_bp)

    # --- Register CLI commands ---
    from installer.cli import register_commands
    register_commands(app)

    # --- Language switching route ---
    @app.route('/lang/<lang_code>')
    def switch_language(lang_code):
        from flask import redirect
        if lang_code in app.config.get('SUPPORTED_LANGUAGES', []):
            session['language'] = lang_code
        return redirect(request.referrer or '/')

    # --- Context processors ---
    @app.context_processor
    def inject_globals():
        return {
            'app_name': app.config.get('APP_NAME', 'Employees Management'),
            'app_version': app.config.get('APP_VERSION', '1.0.0'),
            'supported_languages': app.config.get('SUPPORTED_LANGUAGES', []),
        }

    # --- Error handlers ---
    _register_error_handlers(app)

    return app


def _register_error_handlers(app: Flask) -> None:
    """Register HTTP error handlers with custom templates."""

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
