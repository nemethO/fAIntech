"""Seed script to populate default categories."""
from app import create_app
from app.extensions import db
from app.services.categorizer import DEFAULT_CATEGORIES, ensure_default_categories


def seed_categories():
    app = create_app()
    with app.app_context():
        db.create_all()
        ensure_default_categories()
        db.session.commit()
        print(f'Seeded {len(DEFAULT_CATEGORIES)} default categories.')


if __name__ == '__main__':
    seed_categories()
