from flask import Blueprint

needs_bp = Blueprint('needs', __name__, template_folder='templates', url_prefix='/needs')

from . import routes
