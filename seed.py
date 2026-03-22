"""Seed script to populate default categories."""
from app import create_app
from app.extensions import db
from app.models.category import Category

DEFAULT_CATEGORIES = [
    {'name': 'Elelmiszer',     'icon': '🛒', 'color': '#22c55e'},
    {'name': 'Etterem',        'icon': '🍽️', 'color': '#f97316'},
    {'name': 'Kozlekedes',     'icon': '🚗', 'color': '#3b82f6'},
    {'name': 'Szorakozas',     'icon': '🎬', 'color': '#a78bfa'},
    {'name': 'Vasarlas',       'icon': '🛍️', 'color': '#ec4899'},
    {'name': 'Kozuzemi dijak', 'icon': '⚡', 'color': '#06b6d4'},
    {'name': 'Lakhatas',       'icon': '🏠', 'color': '#eab308'},
    {'name': 'Egeszseg',       'icon': '🏥', 'color': '#ef4444'},
    {'name': 'Egyeb',          'icon': '🔮', 'color': '#6b7280'},
]


def seed_categories():
    app = create_app()
    with app.app_context():
        db.create_all()
        for cat in DEFAULT_CATEGORIES:
            existing = Category.query.filter_by(
                name=cat['name'], user_id=None
            ).first()
            if not existing:
                db.session.add(Category(
                    user_id=None,
                    is_default=True,
                    **cat,
                ))
        db.session.commit()
        print(f'Seeded {len(DEFAULT_CATEGORIES)} default categories.')


if __name__ == '__main__':
    seed_categories()
