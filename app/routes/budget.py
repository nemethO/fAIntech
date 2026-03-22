from flask import Blueprint

budget_bp = Blueprint('budget', __name__, url_prefix='/budget')

# Routes to implement:
# GET  /budget          - View current month budgets with progress bars & alerts
# POST /budget          - Create/update budget for a category
# DELETE /budget/<id>   - Remove a budget
