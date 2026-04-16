from datetime import date
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.budget import Budget
from app.services.analytics_service import (
    get_user_categories, get_category_spending, MONTH_NAMES,
)

budget_bp = Blueprint('budget', __name__, url_prefix='/budget')


@budget_bp.route('/')
@login_required
def budget_page():
    """Koltsegkeretek megjelenitese progress barokkal."""
    today = date.today()
    current_month = today.strftime('%Y-%m')

    categories = get_user_categories(current_user.id, exclude_income=True)

    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        year_month=current_month,
    ).all()
    budget_map = {b.category_id: b for b in budgets}

    spent_map = get_category_spending(current_user.id, current_month)

    budget_items = []
    for cat in categories:
        b = budget_map.get(cat.id)
        spent = spent_map.get(cat.id, 0)
        limit_val = b.monthly_limit if b else 0
        pct = (spent / limit_val * 100) if limit_val > 0 else 0
        budget_items.append({
            'category': cat,
            'budget': b,
            'spent': spent,
            'limit': limit_val,
            'pct': min(round(pct), 100),
            'pct_raw': round(pct),
            'over': pct >= 100,
            'warning': 80 <= pct < 100,
        })

    budget_items.sort(key=lambda x: (x['limit'] == 0, -x['pct_raw']))

    return render_template('budget/index.html',
        budget_items=budget_items,
        month_name=MONTH_NAMES.get(today.month, ''),
        year_month=current_month,
    )


@budget_bp.route('/', methods=['POST'])
@login_required
def save_budget():
    """Keret letrehozasa vagy frissitese."""
    data = request.get_json()
    cat_id = data.get('category_id')
    limit_val = data.get('monthly_limit', 0)
    today = date.today()
    ym = today.strftime('%Y-%m')

    if not cat_id:
        return jsonify({'error': 'Hiányzó kategória'}), 400

    existing = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=int(cat_id),
        year_month=ym
    ).first()

    if existing:
        if float(limit_val) <= 0:
            db.session.delete(existing)
        else:
            existing.monthly_limit = float(limit_val)
    else:
        if float(limit_val) > 0:
            db.session.add(Budget(
                user_id=current_user.id,
                category_id=int(cat_id),
                monthly_limit=float(limit_val),
                year_month=ym,
            ))

    db.session.commit()
    return jsonify({'success': True})
