from datetime import datetime, timezone
from app.extensions import db


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bank_name = db.Column(db.String(50), nullable=False)  # OTP, Revolut, Erste
    account_name = db.Column(db.String(100))               # User-defined display name
    currency = db.Column(db.String(3), default='HUF')      # ISO 4217
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic')
    imports = db.relationship('ImportLog', backref='account', lazy='dynamic')

    def __repr__(self):
        return f'<Account {self.bank_name} - {self.account_name}>'
