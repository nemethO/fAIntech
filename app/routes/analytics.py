from datetime import date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from app.services.analytics_service import (
    month_str, get_month_txs, calc_income_expense, calc_savings_rate,
    pct_change, get_user_categories, get_6month_trend, get_top_merchants,
    MONTH_NAMES_LOWER,
)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


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
    curr_ym = month_str(today)
    prev_date = today.replace(day=1) - timedelta(days=1)
    prev_ym = month_str(prev_date)

    curr_txs = get_month_txs(current_user.id, curr_ym)
    prev_txs = get_month_txs(current_user.id, prev_ym)

    inc_curr, exp_curr = calc_income_expense(curr_txs)
    inc_prev, exp_prev = calc_income_expense(prev_txs)

    save_curr = inc_curr - exp_curr
    save_prev = inc_prev - exp_prev
    save_rate_curr = calc_savings_rate(inc_curr, exp_curr)
    save_rate_prev = calc_savings_rate(inc_prev, exp_prev)

    days_in_month = today.day
    avg_daily = exp_curr / days_in_month if days_in_month > 0 else 0

    # kategoriank osszevetese elozo honappal
    cats = get_user_categories(current_user.id, exclude_income=True)

    comparison = []
    for cat in cats:
        c_spent = sum(abs(t.amount) for t in curr_txs if not t.is_income and t.category_id == cat.id)
        p_spent = sum(abs(t.amount) for t in prev_txs if not t.is_income and t.category_id == cat.id)
        comparison.append({
            'name': cat.name, 'icon': cat.icon, 'color': cat.color,
            'current': c_spent, 'previous': p_spent,
            'change_pct': pct_change(c_spent, p_spent),
        })

    top_cat = max(comparison, key=lambda x: x['current']) if comparison else None
    trend = get_6month_trend(current_user.id)

    return jsonify({
        'summary': {
            'prev_savings': round(save_prev),
            'curr_savings': round(save_curr),
            'prev_rate': save_rate_prev,
            'curr_rate': save_rate_curr,
            'avg_daily': round(avg_daily),
            'top_cat': top_cat['name'] if top_cat else '-',
            'top_cat_amount': round(top_cat['current']) if top_cat else 0,
        },
        'comparison': comparison,
        'trend': trend,
        'months': {
            'current': MONTH_NAMES_LOWER.get(today.month, ''),
            'previous': MONTH_NAMES_LOWER.get(prev_date.month, ''),
        }
    })


@analytics_bp.route('/api/categories')
@login_required
def api_categories():
    """Kategoriak tab: radar chart + reszletes bontas + valtozas."""
    today = date.today()
    curr_ym = month_str(today)
    prev_date = today.replace(day=1) - timedelta(days=1)
    prev_ym = month_str(prev_date)

    curr_txs = get_month_txs(current_user.id, curr_ym)
    prev_txs = get_month_txs(current_user.id, prev_ym)
    cats = get_user_categories(current_user.id, exclude_income=True)

    result = []
    for cat in cats:
        c_spent = sum(abs(t.amount) for t in curr_txs if not t.is_income and t.category_id == cat.id)
        p_spent = sum(abs(t.amount) for t in prev_txs if not t.is_income and t.category_id == cat.id)
        result.append({
            'name': cat.name, 'icon': cat.icon, 'color': cat.color,
            'current': c_spent, 'previous': p_spent,
            'change_pct': pct_change(c_spent, p_spent),
        })
    result.sort(key=lambda x: x['current'], reverse=True)

    return jsonify({
        'categories': result,
        'months': {
            'current': MONTH_NAMES_LOWER.get(today.month, ''),
            'previous': MONTH_NAMES_LOWER.get(prev_date.month, ''),
        }
    })


@analytics_bp.route('/api/trends')
@login_required
def api_trends():
    """Trendek tab: megtakaritasi rata, napi atlag, kategoria eltolodasok, koltes tempo."""
    today = date.today()
    trend_raw = get_6month_trend(current_user.id)

    # kiegeszites szamolt mezokel
    months_data = []
    for i, m in enumerate(trend_raw):
        inc, exp = m['income'], m['expense']
        days = today.day if i == len(trend_raw) - 1 else 30
        txs = get_month_txs(current_user.id, m['ym'])
        tx_count = len([t for t in txs if not t.is_income])
        months_data.append({
            **m,
            'savings_rate': calc_savings_rate(inc, exp),
            'avg_daily': round(exp / days) if days > 0 else 0,
            'tx_count': tx_count,
        })

    # top kategoria valtozas
    curr_ym = months_data[-1]['ym']
    prev_ym = months_data[-2]['ym'] if len(months_data) > 1 else curr_ym
    curr_txs = get_month_txs(current_user.id, curr_ym)
    prev_txs = get_month_txs(current_user.id, prev_ym)
    cats = get_user_categories(current_user.id, exclude_income=True)

    cat_shifts = []
    for cat in cats:
        c = sum(abs(t.amount) for t in curr_txs if not t.is_income and t.category_id == cat.id)
        p = sum(abs(t.amount) for t in prev_txs if not t.is_income and t.category_id == cat.id)
        if c > 0 or p > 0:
            cat_shifts.append({
                'name': cat.name, 'icon': cat.icon, 'color': cat.color,
                'current': round(c), 'previous': round(p),
                'change_pct': pct_change(c, p) if p > 0 else (100 if c > 0 else 0),
            })
    cat_shifts.sort(key=lambda x: abs(x['change_pct']), reverse=True)

    # koltes tempo
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
    return jsonify(get_top_merchants(current_user.id, month_str(today)))
