from flask import Blueprint

bp = Blueprint('cms', __name__, template_folder='templates')

from app.cms import routes