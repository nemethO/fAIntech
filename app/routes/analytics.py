from datetime import date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.transaction import Transaction
from app.models.category import Category

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


def _month_str(d):
    return d.strftime('%Y-%m')


def _get_month_txs(user_id, ym):
    return Transaction.query.filter(
        Transaction.user_id == user_id,
        func.strftime('%Y-%m', Transaction.date) == ym
    ).all()


@analytics_bp.route('/')
@login_required
def analytics_page():
    """Analitika oldal renderelese."""
    return render_template('analytics/index.html')


@analytics_bp.route('/api/overview')
@login_required
def api_overview():
    """Attekintes tab: havi osszehasonlitas + fo mutatoszamok."""
    today = date.today()
    curr_ym = _month_str(today)
    prev_date = today.replace(day=1) - timedelta(days=1)
    prev_ym = _month_str(prev_date)

    curr_txs = _get_month_txs(current_user.id, curr_ym)
    prev_txs = _get_month_txs(current_user.id, prev_ym)

    inc_curr = sum(t.amount for t in curr_txs if t.is_income)
    exp_curr = sum(abs(t.amount) for t in curr_txs if not t.is_income)
    inc_prev = sum(t.amount for t in prev_txs if t.is_income)
    exp_prev = sum(abs(t.amount) for t in prev_txs if not t.is_income)

    save_curr = inc_curr - exp_curr
    save_prev = inc_prev - exp_prev
    save_rate_curr = (save_curr / inc_curr * 100) if inc_curr > 0 else 0
    save_rate_prev = (save_prev / inc_prev * 100) if inc_prev > 0 else 0

    days_in_month = today.day
    avg_daily = exp_curr / days_in_month if days_in_month > 0 else 0

    # kategoriank osszevetese elozo honappal
    cats = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).all()

    comparison = []
    for cat in cats:
        if cat.name == 'Fizetés':
            continue
        c_spent = sum(abs(t.amount) for t in curr_txs if not t.is_income and t.category_id == cat.id)
        p_spent = sum(abs(t.amount) for t in prev_txs if not t.is_income and t.category_id == cat.id)
        comparison.append({
            'name': cat.name,
            'icon': cat.icon,
            'color': cat.color,
            'current': c_spent,
            'previous': p_spent,
            'change_pct': round((c_spent - p_spent) / p_spent * 100, 1) if p_spent > 0 else 0,
        })

    # legnagyobb kategoria
    top_cat = max(comparison, key=lambda x: x['current']) if comparison else None

    # trend: 6 honap
    trend = []
    month_names_short = {1:'Jan.', 2:'Febr.', 3:'Márc.', 4:'Ápr.', 5:'Máj.', 6:'Jún.',
                         7:'Júl.', 8:'Aug.', 9:'Szept.', 10:'Okt.', 11:'Nov.', 12:'Dec.'}
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        ym = _month_str(d)
        txs = _get_month_txs(current_user.id, ym)
        trend.append({
            'label': month_names_short.get(d.month, ''),
            'income': sum(t.amount for t in txs if t.is_income),
            'expense': sum(abs(t.amount) for t in txs if not t.is_income),
        })

    month_names = {1:'január', 2:'február', 3:'március', 4:'április', 5:'május', 6:'június',
                   7:'július', 8:'augusztus', 9:'szeptember', 10:'október', 11:'november', 12:'december'}

    return jsonify({
        'summary': {
            'prev_savings': round(save_prev),
            'curr_savings': round(save_curr),
            'prev_rate': round(save_rate_prev, 1),
            'curr_rate': round(save_rate_curr, 1),
            'avg_daily': round(avg_daily),
            'top_cat': top_cat['name'] if top_cat else '-',
            'top_cat_amount': round(top_cat['current']) if top_cat else 0,
        },
        'comparison': comparison,
        'trend': trend,
        'months': {
            'current': month_names.get(today.month, ''),
            'previous': month_names.get(prev_date.month, ''),
        }
    })


@analytics_bp.route('/api/categories')
@login_required
def api_categories():
    """Kategoriak tab: radar chart + reszletes bontas + valtozas."""
    today = date.today()
    curr_ym = _month_str(today)
    prev_date = today.replace(day=1) - timedelta(days=1)
    prev_ym = _month_str(prev_date)

    curr_txs = _get_month_txs(current_user.id, curr_ym)
    prev_txs = _get_month_txs(current_user.id, prev_ym)

    cats = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).filter(Category.name != 'Fizetés').all()

    result = []
    for cat in cats:
        c_spent = sum(abs(t.amount) for t in curr_txs if not t.is_income and t.category_id == cat.id)
        p_spent = sum(abs(t.amount) for t in prev_txs if not t.is_income and t.category_id == cat.id)
        change = round((c_spent - p_spent) / p_spent * 100, 1) if p_spent > 0 else 0
        result.append({
            'name': cat.name,
            'icon': cat.icon,
            'color': cat.color,
            'current': c_spent,
            'previous': p_spent,
            'change_pct': change,
        })

    result.sort(key=lambda x: x['current'], reverse=True)

    month_names = {1:'január', 2:'február', 3:'március', 4:'április', 5:'május', 6:'június',
                   7:'július', 8:'augusztus', 9:'szeptember', 10:'október', 11:'november', 12:'december'}

    return jsonify({
        'categories': result,
        'months': {
            'current': month_names.get(today.month, ''),
            'previous': month_names.get(prev_date.month, ''),
        }
    })


@analytics_bp.route('/api/trends')
@login_required
def api_trends():
    """Trendek tab: megtakaritasi rata, napi atlag, kategoria eltolodasok, koltes tempo."""
    today = date.today()
    labels_short = {1:'Jan.', 2:'Febr.', 3:'Márc.', 4:'Ápr.', 5:'Máj.', 6:'Jún.',
                    7:'Júl.', 8:'Aug.', 9:'Szept.', 10:'Okt.', 11:'Nov.', 12:'Dec.'}

    # 6 honap adatai
    months_data = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        ym = _month_str(d)
        txs = _get_month_txs(current_user.id, ym)
        inc = sum(t.amount for t in txs if t.is_income)
        exp = sum(abs(t.amount) for t in txs if not t.is_income)
        tx_count = len([t for t in txs if not t.is_income])
        days = today.day if i == 0 else 30
        months_data.append({
            'label': labels_short.get(d.month, ''),
            'ym': ym,
            'income': inc,
            'expense': exp,
            'savings_rate': round((inc - exp) / inc * 100, 1) if inc > 0 else 0,
            'avg_daily': round(exp / days) if days > 0 else 0,
            'tx_count': tx_count,
        })

    # top kategoria valtozas (utolso 2 honap kozott)
    curr_ym = months_data[-1]['ym']
    prev_ym = months_data[-2]['ym'] if len(months_data) > 1 else curr_ym
    curr_txs = _get_month_txs(current_user.id, curr_ym)
    prev_txs = _get_month_txs(current_user.id, prev_ym)

    cats = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).filter(Category.name != 'Fizetés').all()

    cat_shifts = []
    for cat in cats:
        c = sum(abs(t.amount) for t in curr_txs if not t.is_income and t.category_id == cat.id)
        p = sum(abs(t.amount) for t in prev_txs if not t.is_income and t.category_id == cat.id)
        if c > 0 or p > 0:
            cat_shifts.append({
                'name': cat.name, 'icon': cat.icon, 'color': cat.color,
                'current': round(c), 'previous': round(p),
                'change_pct': round((c - p) / p * 100, 1) if p > 0 else (100 if c > 0 else 0),
            })
    cat_shifts.sort(key=lambda x: abs(x['change_pct']), reverse=True)

    # koltes tempo: ha a honap elejen vagyunk vs elozo honap osszes
    curr_expense = months_data[-1]['expense']
    prev_expense = months_data[-2]['expense'] if len(months_data) > 1 else 0
    day_of_month = today.day
    projected = round(curr_expense / day_of_month * 30) if day_of_month > 0 else 0
    pace_pct = round(projected / prev_expense * 100) if prev_expense > 0 else 0

    return jsonify({
        'months': months_data,
        'cat_shifts': cat_shifts[:6],
        'pace': {
            'current': round(curr_expense),
            'projected': projected,
            'prev_total': round(prev_expense),
            'pace_pct': pace_pct,
            'day_of_month': day_of_month,
        }
    })


@analytics_bp.route('/api/merchants')
@login_required
def api_merchants():
    """Kereskedok tab: top 20 partner koltes alapjan."""
    today = date.today()
    curr_ym = _month_str(today)

    txs = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.is_income == False,
        func.strftime('%Y-%m', Transaction.date) == curr_ym
    ).all()

    merchants = {}
    for t in txs:
        name = t.partner or 'Ismeretlen'
        if name not in merchants:
            merchants[name] = {'amount': 0, 'count': 0}
        merchants[name]['amount'] += abs(t.amount)
        merchants[name]['count'] += 1

    sorted_m = sorted(merchants.items(), key=lambda x: x[1]['amount'], reverse=True)[:20]

    return jsonify([{
        'name': name,
        'amount': round(data['amount']),
        'count': data['count'],
    } for name, data in sorted_m])
