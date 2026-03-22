from flask import Blueprint

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

# Routes to implement:
# GET /analytics                - Main analytics page (4 tabs)
# GET /analytics/api/overview   - JSON: monthly comparison bar chart data
# GET /analytics/api/categories - JSON: category breakdown, radar chart data
# GET /analytics/api/trends     - JSON: 6-month income vs expense trend line
# GET /analytics/api/merchants  - JSON: top merchants data
