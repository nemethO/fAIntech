from app.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL = system default
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(10))    # Emoji icon
    color = db.Column(db.String(7))    # Hex color e.g. #FF6B6B
    is_default = db.Column(db.Boolean, default=False)

    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')
    budgets = db.relationship('Budget', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'
