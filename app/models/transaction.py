from datetime import datetime, timezone
from app.extensions import db


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    import_id = db.Column(db.Integer, db.ForeignKey('imports.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='HUF')
    partner = db.Column(db.String(200))         # Payee / merchant name
    description = db.Column(db.Text)            # Kozlemeny / memo
    transaction_hash = db.Column(db.String(64), unique=True)  # SHA-256 for dedup

    is_income = db.Column(db.Boolean, default=False)
    ai_category_confidence = db.Column(db.Float, nullable=True)
    manually_categorized = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Transaction {self.date} {self.partner} {self.amount}>'
