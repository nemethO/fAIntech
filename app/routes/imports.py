from flask import Blueprint

imports_bp = Blueprint('imports', __name__, url_prefix='/import')

# Routes to implement (4-step wizard):
# GET  /import              - Step 1: Bank selection (OTP, Revolut, Erste)
# POST /import/upload       - Step 2: File upload (drag-and-drop CSV/PDF)
# GET  /import/preview      - Step 3: Preview parsed transactions
# POST /import/confirm      - Step 4: Confirm and save to database
