import bcrypt
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.account import Account

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/')
@login_required
def settings_page():
    """Beallitasok oldal."""
    categories = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()

    return render_template('settings/index.html',
        categories=categories,
        accounts=accounts,
    )


@settings_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    """Profil adatok frissitese."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if name:
        current_user.name = name
    if email:
        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing:
            flash('Ez az email cím már foglalt.', 'error')
            return redirect(url_for('settings.settings_page'))
        current_user.email = email
    if password and len(password) >= 6:
        current_user.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    db.session.commit()
    flash('Profil frissítve!', 'success')
    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/categories', methods=['POST'])
@login_required
def add_category():
    """Egyedi kategoria letrehozasa."""
    data = request.get_json()
    name = data.get('name', '').strip()
    icon = data.get('icon', '🏷️')
    color = data.get('color', '#6b7280')

    if not name:
        return jsonify({'error': 'Adj meg egy nevet'}), 400

    existing = Category.query.filter(
        Category.name == name,
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).first()
    if existing:
        return jsonify({'error': 'Már létezik ilyen kategória'}), 400

    cat = Category(user_id=current_user.id, name=name, icon=icon, color=color)
    db.session.add(cat)
    db.session.commit()
    return jsonify({'success': True, 'id': cat.id})


@settings_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@login_required
def delete_category(cat_id):
    """Egyedi kategoria torlese (csak sajat)."""
    cat = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'success': True})
