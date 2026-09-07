from flask import Blueprint

auth_bp = Blueprint('auth', __name__, template_folder='../../templates/auth', url_prefix='/auth')

from . import routes
