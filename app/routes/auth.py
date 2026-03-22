from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Routes to implement:
# GET  /auth/login     - Login page
# POST /auth/login     - Handle login
# GET  /auth/register  - Registration page
# POST /auth/register  - Handle registration
# GET  /auth/logout    - Logout
