"""Seed script to populate default categories."""
from app import create_app
from app.extensions import db
from app.models.category import Category

DEFAULT_CATEGORIES = [
    {'name': 'Élelmiszer',     'icon': '🛒', 'color': '#22c55e'},
    {'name': 'Étterem',        'icon': '🍽️', 'color': '#f97316'},
    {'name': 'Közlekedés',     'icon': '🚗', 'color': '#3b82f6'},
    {'name': 'Szórakozás',     'icon': '🎬', 'color': '#a78bfa'},
    {'name': 'Vásárlás',       'icon': '🛍️', 'color': '#ec4899'},
    {'name': 'Közüzemi díjak', 'icon': '⚡', 'color': '#06b6d4'},
    {'name': 'Lakhatás',       'icon': '🏠', 'color': '#eab308'},
    {'name': 'Egészség',       'icon': '🏥', 'color': '#ef4444'},
    {'name': 'Pénzügyi',       'icon': '💱', 'color': '#8b5cf6'},
    {'name': 'Fizetés',        'icon': '💰', 'color': '#10b981'},
    {'name': 'Egyéb',          'icon': '🔮', 'color': '#6b7280'},
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
