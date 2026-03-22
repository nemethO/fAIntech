from datetime import datetime, timezone
from app.extensions import db


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    monthly_limit = db.Column(db.Float, nullable=False)
    year_month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category_id', 'year_month',
                            name='uq_budget_user_cat_month'),
    )

    def __repr__(self):
        return f'<Budget {self.year_month} {self.monthly_limit}>'
