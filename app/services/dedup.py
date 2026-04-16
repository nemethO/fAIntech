# Dedup – tranzakcio duplikacio ellenorzes hash alapjan
from app.models.transaction import Transaction


def is_duplicate(tx_hash, user_id=None):
    """True ha a hash mar letezik az adatbazisban az adott felhasznalohoz."""
    if not tx_hash:
        return False
    query = Transaction.query.filter_by(transaction_hash=tx_hash)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    return query.first() is not None
