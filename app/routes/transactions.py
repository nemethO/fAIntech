from flask import Blueprint

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

# Routes to implement:
# GET  /transactions           - List all transactions (filterable, searchable, paginated)
# POST /transactions/<id>/category  - Update transaction category (human-in-the-loop)
# GET  /transactions/export    - Export transactions as CSV
