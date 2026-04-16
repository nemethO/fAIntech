# Analytics Service – kozos penzugyi szamitasok
from datetime import date, timedelta
from sqlalchemy import func

from app.extensions import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.account import Account

# magyar honapnevek
MONTH_NAMES = {
    1: 'Január', 2: 'Február', 3: 'Március', 4: 'Április',
    5: 'Május', 6: 'Június', 7: 'Július', 8: 'Augusztus',
    9: 'Szeptember', 10: 'Október', 11: 'November', 12: 'December',
}
MONTH_NAMES_SHORT = {
    1: 'Jan.', 2: 'Febr.', 3: 'Márc.', 4: 'Ápr.',
    5: 'Máj.', 6: 'Jún.', 7: 'Júl.', 8: 'Aug.',
    9: 'Szept.', 10: 'Okt.', 11: 'Nov.', 12: 'Dec.',
}
MONTH_NAMES_LOWER = {
    1: 'január', 2: 'február', 3: 'március', 4: 'április',
    5: 'május', 6: 'június', 7: 'július', 8: 'augusztus',
    9: 'szeptember', 10: 'október', 11: 'november', 12: 'december',
}


def month_str(d):
    """Date -> 'YYYY-MM' string."""
    return d.strftime('%Y-%m')


def get_month_txs(user_id, ym):
    """Adott honap tranzakcioi."""
    return Transaction.query.filter(
        Transaction.user_id == user_id,
        func.strftime('%Y-%m', Transaction.date) == ym,
    ).all()


def calc_income_expense(txs):
    """Bevetel es kiadas osszeg egy tranzakcio listabol."""
    income = sum(t.amount for t in txs if t.is_income)
    expense = sum(abs(t.amount) for t in txs if not t.is_income)
    return income, expense


def calc_savings_rate(income, expense):
    """Megtakaritasi rata %."""
    return round((income - expense) / income * 100, 1) if income > 0 else 0


def pct_change(curr, prev):
    """Szazalekos valtozas elozo idoszakhoz kepest."""
    return round((curr - prev) / prev * 100, 1) if prev > 0 else 0


def get_user_categories(user_id, exclude_income=False):
    """Felhasznalo kategoriai (sajat + globalis)."""
    q = Category.query.filter(
        (Category.user_id == user_id) | (Category.user_id.is_(None))
    )
    if exclude_income:
        q = q.filter(Category.name != 'Fizetés')
    return q.all()


def build_cat_breakdown(txs, limit=5):
    """Kategoria bontas fankdiagramhoz (top N)."""
    breakdown = {}
    for t in txs:
        cat = Category.query.get(t.category_id) if t.category_id else None
        name = cat.name if cat else 'Egyéb'
        color = cat.color if cat else '#6b7280'
        icon = cat.icon if cat else '🔮'
        breakdown[name] = breakdown.get(name, {'amount': 0, 'color': color, 'icon': icon})
        breakdown[name]['amount'] += abs(t.amount)
    sorted_bd = sorted(breakdown.items(), key=lambda x: x[1]['amount'], reverse=True)
    return sorted_bd[:limit] if limit else sorted_bd


def get_budget_alerts(user_id, ym, txs_current):
    """Koltsegkeret figyelmeztetesek (>=80%)."""
    budgets = Budget.query.filter_by(user_id=user_id, year_month=ym).all()
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
    return alerts


def get_6month_trend(user_id):
    """6 honap bevetel/kiadas trend adat."""
    today = date.today()
    months = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        ym = month_str(d)
        txs = get_month_txs(user_id, ym)
        inc, exp = calc_income_expense(txs)
        months.append({
            'label': MONTH_NAMES_SHORT.get(d.month, ''),
            'ym': ym,
            'income': inc,
            'expense': exp,
        })
    return months


def get_recent_transactions(user_id, limit=7):
    """Utolso N tranzakcio enrichekelve."""
    recent = Transaction.query.filter_by(user_id=user_id)\
        .order_by(Transaction.date.desc())\
        .limit(limit).all()

    result = []
    for t in recent:
        cat = Category.query.get(t.category_id) if t.category_id else None
        acc = Account.query.get(t.account_id) if t.account_id else None
        result.append({
            'date': t.date.strftime('%b. %d.'),
            'partner': t.partner or 'Ismeretlen',
            'description': t.description or '',
            'amount': t.amount,
            'is_income': t.is_income,
            'category_icon': cat.icon if cat else '🔮',
            'category_name': cat.name if cat else 'Egyéb',
            'account_name': acc.bank_name if acc else '',
        })
    return result


def get_category_spending(user_id, ym, exclude_income_cat=True):
    """Kategoriankok koltes map (cat_id -> amount)."""
    txs = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.is_income == False,
        func.strftime('%Y-%m', Transaction.date) == ym,
    ).all()
    spent = {}
    for t in txs:
        if t.category_id:
            spent[t.category_id] = spent.get(t.category_id, 0) + abs(t.amount)
    return spent


def get_top_merchants(user_id, ym, limit=20):
    """Top kereskedok koltes alapjan."""
    txs = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.is_income == False,
        func.strftime('%Y-%m', Transaction.date) == ym,
    ).all()
    merchants = {}
    for t in txs:
        name = t.partner or 'Ismeretlen'
        if name not in merchants:
            merchants[name] = {'amount': 0, 'count': 0}
        merchants[name]['amount'] += abs(t.amount)
        merchants[name]['count'] += 1
    sorted_m = sorted(merchants.items(), key=lambda x: x[1]['amount'], reverse=True)[:limit]
    return [{'name': n, 'amount': round(d['amount']), 'count': d['count']} for n, d in sorted_m]
