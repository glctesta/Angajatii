"""
Flask extensions — initialized here, configured in the app factory.
The Base class is defined here to avoid circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 declarative models."""
    metadata = MetaData(naming_convention=convention)


# SQLAlchemy with our custom Base
db = SQLAlchemy(model_class=Base)

# Login manager
login_manager = LoginManager()

# Internationalization
babel = Babel()

# CSRF protection
csrf = CSRFProtect()

# Database migrations
migrate = Migrate()
