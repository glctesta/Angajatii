from functools import wraps
from flask import abort
from flask_login import current_user
from app.models.license import License

def license_required(level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_license_level(level):
                abort(403, description="License level required: " + level)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
