from flask import Blueprint

employees_bp = Blueprint('employees', __name__, template_folder='templates', url_prefix='/employees')

from . import routes
