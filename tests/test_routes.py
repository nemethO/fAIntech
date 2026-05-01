from datetime import date
from pathlib import Path

from flask import Blueprint, Flask

from app import models  # noqa: F401
from app.extensions import db, login_manager
from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.routes.budget import budget_bp
from app.routes.imports import imports_bp


def create_test_app(tmp_path):
	template_dir = Path(__file__).resolve().parents[1] / 'app' / 'templates'
	app = Flask(__name__, template_folder=str(template_dir))
	app.config.update(
		TESTING=True,
		SECRET_KEY='test-secret',
		SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'test.db'}",
		SQLALCHEMY_TRACK_MODIFICATIONS=False,
		UPLOAD_FOLDER=str(tmp_path / 'uploads'),
	)

	db.init_app(app)
	login_manager.init_app(app)
	login_manager.login_view = 'auth.login'

	dashboard_bp = Blueprint('dashboard', __name__)
	transactions_bp = Blueprint('transactions', __name__)
	analytics_bp = Blueprint('analytics', __name__)
	chat_bp = Blueprint('chat', __name__)
	settings_bp = Blueprint('settings', __name__)

	@dashboard_bp.route('/dashboard')
	def index():
		return 'dashboard'

	@transactions_bp.route('/transactions')
	def list_transactions():
		return 'transactions'

	@analytics_bp.route('/analytics')
	def analytics_page():
		return 'analytics'

	@chat_bp.route('/chat')
	def chat_page():
		return 'chat'

	@settings_bp.route('/settings')
	def settings_page():
		return 'settings'

	app.register_blueprint(dashboard_bp)
	app.register_blueprint(transactions_bp)
	app.register_blueprint(analytics_bp)
	app.register_blueprint(chat_bp)
	app.register_blueprint(settings_bp)
	app.register_blueprint(imports_bp)
	app.register_blueprint(budget_bp)

	with app.app_context():
		db.create_all()

	return app


def test_confirm_import_resolves_categories_without_manual_seed(tmp_path):
	app = create_test_app(tmp_path)

	with app.app_context():
		user = User(name='Teszt Elek', email='teszt@example.com', password_hash='x')
		db.session.add(user)
		db.session.flush()

		account = Account(
			user_id=user.id,
			bank_name='OTP',
			account_name='Fo szamla',
			currency='HUF',
		)
		db.session.add(account)
		db.session.commit()

		user_id = user.id
		account_id = account.id

	client = app.test_client()
	with client.session_transaction() as session:
		session['_user_id'] = str(user_id)
		session['_fresh'] = True
		session['import_data'] = {
			'filename': 'teszt.csv',
			'bank_name': 'OTP',
			'currency': 'HUF',
			'transactions': [],
		}

	response = client.post('/import/confirm', json={
		'account_id': str(account_id),
		'transactions': [
			{
				'date': '2026-01-10',
				'amount': -1234.56,
				'currency': 'HUF',
				'partner': 'Media Markt',
				'description': 'Vasarlas teszt',
				'category': 'Vasarlas',
				'transaction_hash': 'hash-1',
			},
			{
				'date': '2026-01-11',
				'amount': -345.67,
				'currency': 'HUF',
				'partner': 'Ismeretlen',
				'description': 'Ismeretlen teszt',
				'category': 'Totally Unknown Category',
				'transaction_hash': 'hash-2',
			},
		],
	})

	assert response.status_code == 200
	assert response.get_json()['success'] is True

	with app.app_context():
		transactions = Transaction.query.order_by(Transaction.date.asc()).all()
		assert len(transactions) == 2
		assert transactions[0].category.name == 'Vásárlás'
		assert transactions[1].category.name == 'Egyéb'
		assert Category.query.filter_by(user_id=None).count() == 11


def test_budget_page_shows_overrun_and_unbudgeted_spending_states(tmp_path):
	app = create_test_app(tmp_path)
	current_month = date.today().strftime('%Y-%m')

	with app.app_context():
		user = User(name='Teszt Elek', email='budget@example.com', password_hash='x')
		db.session.add(user)
		db.session.flush()

		account = Account(
			user_id=user.id,
			bank_name='OTP',
			account_name='Fo szamla',
			currency='HUF',
		)
		db.session.add(account)
		db.session.flush()

		groceries = Category(user_id=None, name='Élelmiszer', icon='🛒', color='#22c55e', is_default=True)
		utilities = Category(user_id=None, name='Közüzemi díjak', icon='⚡', color='#06b6d4', is_default=True)
		db.session.add_all([groceries, utilities])
		db.session.flush()

		db.session.add(Budget(
			user_id=user.id,
			category_id=groceries.id,
			monthly_limit=5000,
			year_month=current_month,
		))

		db.session.add_all([
			Transaction(
				user_id=user.id,
				account_id=account.id,
				category_id=groceries.id,
				date=date.today(),
				amount=-94180,
				currency='HUF',
				partner='Tesco',
				description='Groceries',
				transaction_hash='budget-hash-1',
				is_income=False,
			),
			Transaction(
				user_id=user.id,
				account_id=account.id,
				category_id=utilities.id,
				date=date.today(),
				amount=-20950,
				currency='HUF',
				partner='MVM',
				description='Utilities',
				transaction_hash='budget-hash-2',
				is_income=False,
			),
		])
		db.session.commit()

		user_id = user.id

	client = app.test_client()
	with client.session_transaction() as session:
		session['_user_id'] = str(user_id)
		session['_fresh'] = True

	response = client.get('/budget/')

	assert response.status_code == 200
	body = response.get_data(as_text=True)
	assert 'Ft-tal túllépve' in body
	assert 'de nincs hozzá keret beállítva' in body
