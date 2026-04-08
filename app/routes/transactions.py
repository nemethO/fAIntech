from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.account import Account

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@transactions_bp.route('/')
@login_required
def list_transactions():
    """Tranzakciok listazasa szuressel es keresessel."""
    # szuro parameterek
    search = request.args.get('q', '').strip()
    cat_filter = request.args.get('category', '')
    acc_filter = request.args.get('account', '')
    type_filter = request.args.get('type', '')  # income / expense
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    page = request.args.get('page', 1, type=int)

    query = Transaction.query.filter_by(user_id=current_user.id)

    # szuresek
    if search:
        query = query.filter(
            (Transaction.partner.ilike(f'%{search}%')) |
            (Transaction.description.ilike(f'%{search}%'))
        )
    if cat_filter:
        query = query.filter_by(category_id=int(cat_filter))
    if acc_filter:
        query = query.filter_by(account_id=int(acc_filter))
    if type_filter == 'income':
        query = query.filter_by(is_income=True)
    elif type_filter == 'expense':
        query = query.filter_by(is_income=False)
    if date_from:
        query = query.filter(Transaction.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Transaction.date <= datetime.strptime(date_to, '%Y-%m-%d').date())

    # rendezés es lapozas
    pagination = query.order_by(Transaction.date.desc())\
        .paginate(page=page, per_page=20, error_out=False)

    categories = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()

    return render_template('transactions/list.html',
        transactions=pagination.items,
        pagination=pagination,
        categories=categories,
        accounts=accounts,
        filters={
            'q': search, 'category': cat_filter, 'account': acc_filter,
            'type': type_filter, 'from': date_from, 'to': date_to,
        }
    )


@transactions_bp.route('/<int:tx_id>/category', methods=['POST'])
@login_required
def update_category(tx_id):
    """Tranzakcio kategoriajanakfrissitese (human-in-the-loop)."""
    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    cat_id = data.get('category_id')

    if cat_id:
        tx.category_id = int(cat_id)
        tx.manually_categorized = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Hiányzó kategória'}), 400


@transactions_bp.route('/<int:tx_id>', methods=['DELETE'])
@login_required
def delete_transaction(tx_id):
    """Tranzakcio torlese."""
    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    db.session.delete(tx)
    db.session.commit()
    return jsonify({'success': True})
