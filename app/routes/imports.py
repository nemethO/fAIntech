import os
import json
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.import_log import ImportLog
from app.services.statement_parser import extract_text, parse_with_llm, categorize_transactions
from app.services.categorizer import build_category_map, resolve_category_id
from app.services.dedup import is_duplicate
from app.services.analytics_service import get_user_categories

imports_bp = Blueprint('imports', __name__, url_prefix='/import')

ALLOWED_EXTENSIONS = {'csv', 'pdf', 'xlsx', 'xls'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@imports_bp.route('/')
@login_required
def upload_page():
    """Feltoltes oldal megjelenitese."""
    return render_template('import/upload.html')


@imports_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Fajl feltoltese, LLM-mel parse-olas es kategorizalas."""
    if 'file' not in request.files:
        return jsonify({'error': 'Nincs fájl kiválasztva'}), 400

    file = request.files['file']
    if file.filename == '' or not _allowed_file(file.filename):
        return jsonify({'error': 'Nem támogatott fájlformátum (CSV, PDF, XLSX)'}), 400

    # fajl mentese
    filename = secure_filename(file.filename)
    # egyedi nev hogy ne irja felul
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = f"{timestamp}_{filename}"
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_name)
    file.save(upload_path)

    try:
        # 1) nyers szoveg kinyerese
        print(f"[Import] Szöveg kinyerése: {upload_path}", flush=True)
        raw_text = extract_text(upload_path)
        print(f"[Import] Szöveg kinyerve: {len(raw_text)} karakter", flush=True)

        # 2) LLM-mel strukturalt adat + kategorizalas (egyetlen hivas)
        print(f"[Import] LLM hívás indítása (provider: {current_app.config.get('AI_PROVIDER')})...", flush=True)
        parsed = parse_with_llm(raw_text)
        transactions = parsed.get('transactions', [])
        print(f"[Import] LLM kész: {len(transactions)} tranzakció találva", flush=True)

        # sessionbe mentjuk az eredmenyt az elonazethez
        session['import_data'] = {
            'filename': filename,
            'safe_name': safe_name,
            'bank_name': parsed.get('bank_name', 'Ismeretlen'),
            'currency': parsed.get('currency', 'HUF'),
            'transactions': transactions,
        }

        return jsonify({'success': True, 'redirect': url_for('imports.preview')})

    except Exception as e:
        return jsonify({'error': f'Feldolgozási hiba: {str(e)}'}), 500


@imports_bp.route('/preview')
@login_required
def preview():
    """Elonezet: a felhasznalo attekintheti es modosithatja a tranzakciokat."""
    import_data = session.get('import_data')
    if not import_data:
        flash('Nincs feldolgozott fájl, tölts fel egyet.', 'warning')
        return redirect(url_for('imports.upload_page'))

    # kategoria lista a legordulo menuhoz
    categories = get_user_categories(current_user.id)

    # felhasznalo szamlai
    accounts = Account.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'import/preview.html',
        data=import_data,
        categories=categories,
        accounts=accounts,
    )


@imports_bp.route('/confirm', methods=['POST'])
@login_required
def confirm():
    """Vegso importalas az adatbazisba, a felhasznalo altal jovahagyott adatokkal."""
    import_data = session.get('import_data')
    if not import_data:
        return jsonify({'error': 'Nincs mit importálni'}), 400

    form = request.get_json()
    account_id = form.get('account_id')
    edited_transactions = form.get('transactions', [])

    # szamla ellenorzes / letrehozas
    if account_id == 'new':
        account = Account(
            user_id=current_user.id,
            bank_name=import_data['bank_name'],
            account_name=form.get('account_name', import_data['bank_name']),
            currency=import_data['currency'],
        )
        db.session.add(account)
        db.session.flush()
        account_id = account.id
    else:
        account_id = int(account_id)
        account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()
        if not account:
            return jsonify({'error': 'Érvénytelen számla'}), 400

    # import log letrehozasa
    ext = os.path.splitext(import_data['filename'])[1].lstrip('.').upper()
    import_log = ImportLog(
        user_id=current_user.id,
        account_id=account_id,
        filename=import_data['filename'],
        file_type=ext,
        bank_type=import_data['bank_name'],
        status='processing',
        records_total=len(edited_transactions),
    )
    db.session.add(import_log)
    db.session.flush()

    # kategoria map + dedup
    cat_map = build_category_map(current_user.id)

    imported = 0
    duplicates = 0

    for tx in edited_transactions:
        if tx.get('excluded'):
            continue

        # duplikacio ellenorzes hash alapjan
        tx_hash = tx.get('transaction_hash', '')
        if is_duplicate(tx_hash, user_id=current_user.id):
            duplicates += 1
            continue

        # kategoria id megkeresese
        cat_name = tx.get('category', 'Egyéb')
        category_id = resolve_category_id(cat_name, cat_map)

        try:
            transaction = Transaction(
                user_id=current_user.id,
                account_id=account_id,
                import_id=import_log.id,
                category_id=category_id,
                date=datetime.strptime(tx['date'], '%Y-%m-%d').date(),
                amount=float(tx['amount']),
                currency=tx.get('currency', import_data['currency']),
                partner=tx.get('partner', ''),
                description=tx.get('description', ''),
                transaction_hash=tx_hash or None,
                is_income=float(tx['amount']) > 0,
                ai_category_confidence=tx.get('category_confidence'),
                manually_categorized=tx.get('manually_changed', False),
            )
            db.session.add(transaction)
            imported += 1
        except (ValueError, KeyError):
            continue

    import_log.records_imported = imported
    import_log.records_duplicate = duplicates
    import_log.status = 'completed'
    db.session.commit()

    # session torlese
    session.pop('import_data', None)

    return jsonify({
        'success': True,
        'imported': imported,
        'duplicates': duplicates,
        'total': len(edited_transactions),
    })
