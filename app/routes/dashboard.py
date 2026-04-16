from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from app.models.transaction import Transaction
from app.services.analytics_service import (
    month_str, get_month_txs, calc_income_expense, calc_savings_rate,
    pct_change, build_cat_breakdown, get_budget_alerts,
    get_6month_trend, get_recent_transactions,
    MONTH_NAMES,
)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Fo dashboard: osszesito kartyak, alertek, chartok, utolso tranzakciok."""
    today = date.today()
    current_month = month_str(today)
    prev_month_date = today.replace(day=1) - timedelta(days=1)
    prev_month = month_str(prev_month_date)

    txs_current = get_month_txs(current_user.id, current_month)
    txs_prev = get_month_txs(current_user.id, prev_month)

    income_curr, expense_curr = calc_income_expense(txs_current)
    income_prev, expense_prev = calc_income_expense(txs_prev)

    # egyenleg (osszes tranzakcio)
    all_txs = Transaction.query.filter_by(user_id=current_user.id).all()
    balance = sum(t.amount for t in all_txs)

    savings_rate = calc_savings_rate(income_curr, expense_curr)

    income_change = pct_change(income_curr, income_prev)
    expense_change = pct_change(expense_curr, expense_prev)

    balance_prev = sum(t.amount for t in all_txs if t.date <= prev_month_date)
    balance_change = round((balance - balance_prev) / abs(balance_prev) * 100, 1) if balance_prev != 0 else 0
    savings_rate_prev = calc_savings_rate(income_prev, expense_prev)
    savings_change = round(savings_rate - savings_rate_prev, 1)

    # budget alertek
    alerts = get_budget_alerts(current_user.id, current_month, txs_current)

    # kategoria bontas (havi + osszes)
    monthly_expenses = [t for t in txs_current if not t.is_income]
    all_expenses = [t for t in all_txs if not t.is_income]
    top_categories_monthly = build_cat_breakdown(monthly_expenses)
    top_categories_all = build_cat_breakdown(all_expenses)
    has_monthly_data = len(monthly_expenses) > 0

    recent_list = get_recent_transactions(current_user.id, limit=7)
    current_month_name = MONTH_NAMES.get(today.month, '')

    return render_template('dashboard/index.html',
        balance=balance,
        income=income_curr,
        expense=expense_curr,
        savings_rate=savings_rate,
        income_change=income_change,
        expense_change=expense_change,
        balance_change=balance_change,
        savings_change=savings_change,
        alerts=alerts,
        top_categories_monthly=top_categories_monthly,
        top_categories_all=top_categories_all,
        has_monthly_data=has_monthly_data,
        recent=recent_list,
        month_name=current_month_name,
        alert_count=len([a for a in alerts if a['over']]),
    )


@dashboard_bp.route('/api/dashboard/chart')
@login_required
def dashboard_chart():
    """6 havi bevetel vs kiadas adat a vonaldiagramhoz."""
    return jsonify(get_6month_trend(current_user.id))
