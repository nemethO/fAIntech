from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract

from app.extensions import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.account import Account

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Fo dashboard: osszesito kartyak, alertek, chartok, utolso tranzakciok."""
    today = date.today()
    current_month = today.strftime('%Y-%m')
    prev_month_date = today.replace(day=1) - timedelta(days=1)
    prev_month = prev_month_date.strftime('%Y-%m')

    # aktualis havi tranzakciok
    txs_current = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        func.strftime('%Y-%m', Transaction.date) == current_month
    ).all()

    # elozo havi tranzakciok
    txs_prev = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        func.strftime('%Y-%m', Transaction.date) == prev_month
    ).all()

    # osszesites
    income_curr = sum(t.amount for t in txs_current if t.is_income)
    expense_curr = sum(abs(t.amount) for t in txs_current if not t.is_income)
    income_prev = sum(t.amount for t in txs_prev if t.is_income)
    expense_prev = sum(abs(t.amount) for t in txs_prev if not t.is_income)

    # egyenleg (osszes tranzakcio)
    all_txs = Transaction.query.filter_by(user_id=current_user.id).all()
    balance = sum(t.amount for t in all_txs)

    # megtakaritasi rata
    savings_rate = ((income_curr - expense_curr) / income_curr * 100) if income_curr > 0 else 0

    # elteresek az elozo honaphoz kepest
    income_change = ((income_curr - income_prev) / income_prev * 100) if income_prev > 0 else 0
    expense_change = ((expense_curr - expense_prev) / expense_prev * 100) if expense_prev > 0 else 0

    # elozo havi egyenleg es megtakaritas rata az osszehasonlitashoz
    balance_prev = sum(t.amount for t in all_txs if t.date <= prev_month_date)
    balance_change = ((balance - balance_prev) / abs(balance_prev) * 100) if balance_prev != 0 else 0
    savings_rate_prev = ((income_prev - expense_prev) / income_prev * 100) if income_prev > 0 else 0
    savings_change = savings_rate - savings_rate_prev

    # koltsegkeret alertek
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        year_month=current_month
    ).all()

    alerts = []
    for b in budgets:
        cat = Category.query.get(b.category_id)
        if not cat:
            continue
        spent = sum(abs(t.amount) for t in txs_current
                    if not t.is_income and t.category_id == b.category_id)
        pct = (spent / b.monthly_limit * 100) if b.monthly_limit > 0 else 0
        if pct >= 80:
            alerts.append({
                'category': cat.name,
                'icon': cat.icon,
                'spent': spent,
                'limit': b.monthly_limit,
                'pct': round(pct),
                'over': pct >= 100,
            })
    alerts.sort(key=lambda a: a['pct'], reverse=True)

    # kategoriank szerinti bontas (fankdiagram) - havi + osszes
    def _build_cat_breakdown(txs):
        breakdown = {}
        for t in txs:
            cat = Category.query.get(t.category_id) if t.category_id else None
            name = cat.name if cat else 'Egyéb'
            color = cat.color if cat else '#6b7280'
            icon = cat.icon if cat else '🔮'
            breakdown[name] = breakdown.get(name, {'amount': 0, 'color': color, 'icon': icon})
            breakdown[name]['amount'] += abs(t.amount)
        return sorted(breakdown.items(), key=lambda x: x[1]['amount'], reverse=True)[:5]

    monthly_expenses = [t for t in txs_current if not t.is_income]
    all_expenses = [t for t in all_txs if not t.is_income]
    top_categories_monthly = _build_cat_breakdown(monthly_expenses)
    top_categories_all = _build_cat_breakdown(all_expenses)
    has_monthly_data = len(monthly_expenses) > 0

    # utolso 7 tranzakcio
    recent = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc())\
        .limit(7).all()

    recent_list = []
    for t in recent:
        cat = Category.query.get(t.category_id) if t.category_id else None
        acc = Account.query.get(t.account_id) if t.account_id else None
        recent_list.append({
            'date': t.date.strftime('%b. %d.'),
            'partner': t.partner or 'Ismeretlen',
            'description': t.description or '',
            'amount': t.amount,
            'is_income': t.is_income,
            'category_icon': cat.icon if cat else '🔮',
            'category_name': cat.name if cat else 'Egyéb',
            'account_name': acc.bank_name if acc else '',
        })

    # honap nev magyarul
    month_names = {1:'Január', 2:'Február', 3:'Március', 4:'Április',
                   5:'Május', 6:'Június', 7:'Július', 8:'Augusztus',
                   9:'Szeptember', 10:'Október', 11:'November', 12:'December'}
    current_month_name = month_names.get(today.month, '')

    return render_template('dashboard/index.html',
        balance=balance,
        income=income_curr,
        expense=expense_curr,
        savings_rate=round(savings_rate, 1),
        income_change=round(income_change, 1),
        expense_change=round(expense_change, 1),
        balance_change=round(balance_change, 1),
        savings_change=round(savings_change, 1),
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
    today = date.today()
    months = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        ym = d.strftime('%Y-%m')
        txs = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            func.strftime('%Y-%m', Transaction.date) == ym
        ).all()
        month_names = {1:'Jan.', 2:'Febr.', 3:'Márc.', 4:'Ápr.',
                       5:'Máj.', 6:'Jún.', 7:'Júl.', 8:'Aug.',
                       9:'Szept.', 10:'Okt.', 11:'Nov.', 12:'Dec.'}
        months.append({
            'label': month_names.get(d.month, d.strftime('%b')),
            'income': sum(t.amount for t in txs if t.is_income),
            'expense': sum(abs(t.amount) for t in txs if not t.is_income),
        })
    return jsonify(months)
