"""
Flask application configuration.
Reads DB credentials from the existing config_manager.py (encrypted).
The NEW database is called 'Employees' (not the existing 'Employee').
"""
import os
import sys
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is in sys.path for importing config_manager
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)


def _build_db_uri(database: str = 'Employees') -> str:
    """Build SQLAlchemy database URI from encrypted credentials."""
    try:
        from config_manager import ConfigManager

        manager = ConfigManager(
            key_file=os.path.join(_root_dir, 'encryption_key.key'),
            config_file=os.path.join(_root_dir, 'db_config.enc')
        )
        config = manager.load_config()

        server = config.get('server', 'localhost')
        username = config.get('username', '')
        password = config.get('password', '')
        driver = config.get('driver', 'ODBC Driver 18 for SQL Server')

        # Build pyodbc connection string
        conn_params = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
            "Encrypt=yes;"
            "Connection Timeout=30;"
        )
        params = urllib.parse.quote_plus(conn_params)
        return f"mssql+pyodbc:///?odbc_connect={params}"

    except Exception as e:
        print(f"[Config] Error building database URI: {e}")
        # Fallback per sviluppo locale
        driver = urllib.parse.quote_plus("ODBC Driver 18 for SQL Server")
        return (
            f"mssql+pyodbc://@localhost/{database}"
            f"?driver={driver}&Trusted_Connection=yes&TrustServerCertificate=yes"
        )


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Session & CSRF
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 86400 * 30  # 30 days
    WTF_CSRF_ENABLED = True

    # Babel — Internationalization
    BABEL_DEFAULT_LOCALE = 'it'
    SUPPORTED_LANGUAGES = ['it', 'ro', 'en', 'es', 'fr', 'de']

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # App settings
    APP_NAME = 'Employees Management'
    APP_VERSION = '1.0.0'

    # Lockout settings
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    # Password reset
    PASSWORD_RESET_EXPIRY_HOURS = 1


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _build_db_uri('Employees')


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _build_db_uri('Employees')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
