from flask import Flask

from app import models  # noqa: F401
from app.extensions import db, login_manager
from app.models.category import Category
from app.models.user import User
from app.routes.imports import imports_bp
from app.services.categorizer import build_category_map, ensure_default_categories, resolve_category_id


def create_test_app(tmp_path):
	app = Flask(__name__)
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
	app.register_blueprint(imports_bp)

	with app.app_context():
		db.create_all()

	return app


def test_default_categories_seed_once_and_user_override_wins(tmp_path):
	app = create_test_app(tmp_path)

	with app.app_context():
		user = User(name='Teszt Elek', email='teszt@example.com', password_hash='x')
		db.session.add(user)
		db.session.commit()

		ensure_default_categories()
		ensure_default_categories()
		db.session.commit()

		defaults = Category.query.filter_by(user_id=None).all()
		assert len(defaults) == 11

		custom = Category(
			user_id=user.id,
			name='Vásárlás',
			icon='🧾',
			color='#111111',
		)
		db.session.add(custom)
		db.session.commit()

		category_map = build_category_map(user.id)

		assert category_map['Vásárlás'] == custom.id
		assert resolve_category_id('Vasarlas', category_map) == custom.id
		assert resolve_category_id('other', category_map) == category_map['Egyéb']
