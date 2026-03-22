from datetime import datetime, timezone
from app.extensions import db


class ImportLog(db.Model):
    __tablename__ = 'imports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)   # CSV or PDF
    bank_type = db.Column(db.String(50), nullable=False)    # OTP, Revolut, Erste
    status = db.Column(db.String(20), default='pending')    # pending/processing/completed/failed
    records_total = db.Column(db.Integer, default=0)
    records_imported = db.Column(db.Integer, default=0)
    records_duplicate = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    transactions = db.relationship('Transaction', backref='import_log', lazy='dynamic')

    def __repr__(self):
        return f'<ImportLog {self.filename} - {self.status}>'
