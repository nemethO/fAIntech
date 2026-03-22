from flask import Blueprint

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

# Routes to implement:
# GET  /settings        - Settings page
# POST /settings/profile - Update user profile
# POST /settings/categories - Manage custom categories
