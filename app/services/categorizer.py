# Categorizer – kategoria nev -> id feloldas
import unicodedata

from app.extensions import db
from app.models.category import Category

DEFAULT_CATEGORIES = [
    {'name': 'Élelmiszer', 'icon': '🛒', 'color': '#22c55e'},
    {'name': 'Étterem', 'icon': '🍽️', 'color': '#f97316'},
    {'name': 'Közlekedés', 'icon': '🚗', 'color': '#3b82f6'},
    {'name': 'Szórakozás', 'icon': '🎬', 'color': '#a78bfa'},
    {'name': 'Vásárlás', 'icon': '🛍️', 'color': '#ec4899'},
    {'name': 'Közüzemi díjak', 'icon': '⚡', 'color': '#06b6d4'},
    {'name': 'Lakhatás', 'icon': '🏠', 'color': '#eab308'},
    {'name': 'Egészség', 'icon': '🏥', 'color': '#ef4444'},
    {'name': 'Pénzügyi', 'icon': '💱', 'color': '#8b5cf6'},
    {'name': 'Fizetés', 'icon': '💰', 'color': '#10b981'},
    {'name': 'Egyéb', 'icon': '🔮', 'color': '#6b7280'},
]


def _normalize(text):
    """Ekezetek, whitespace es specialis jelek eltavolitasa osszehasonlitashoz."""
    if not text:
        return ''
    nfkd = unicodedata.normalize('NFKD', str(text))
    stripped = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return ''.join(c for c in stripped.lower() if c.isalnum())


def ensure_default_categories():
    """Biztositja, hogy a rendszer alap kategoriak letezzenek."""
    existing_names = {
        category.name for category in Category.query.filter(Category.user_id.is_(None)).all()
    }
    created = False
    for category in DEFAULT_CATEGORIES:
        if category['name'] in existing_names:
            continue
        db.session.add(Category(user_id=None, is_default=True, **category))
        created = True

    if created:
        db.session.flush()


def get_category_aliases():
    """Normalizalt aliasok az LLM valaszok robusztusabb feloldasahoz."""
    aliases = {}
    for category in DEFAULT_CATEGORIES:
        aliases[_normalize(category['name'])] = category['name']
    aliases.update({
        'etel': 'Étterem',
        'etelek': 'Étterem',
        'ettermek': 'Étterem',
        'bevasarlas': 'Élelmiszer',
        'elelmiszerbolt': 'Élelmiszer',
        'uzemanyag': 'Közlekedés',
        'benzinkut': 'Közlekedés',
        'kozuzem': 'Közüzemi díjak',
        'rezsi': 'Közüzemi díjak',
        'egeszsegugy': 'Egészség',
        'orvosi': 'Egészség',
        'jovedelem': 'Fizetés',
        'ber': 'Fizetés',
        'fizetesek': 'Fizetés',
        'egyebek': 'Egyéb',
        'other': 'Egyéb',
    })
    return aliases


def build_category_map(user_id):
    """Kategoria nev -> id map (globalis, majd sajat kategoriak felulirnak)."""
    ensure_default_categories()
    categories = Category.query.filter(
        (Category.user_id == user_id) | (Category.user_id.is_(None))
    ).all()

    category_map = {}
    for category in sorted(categories, key=lambda item: item.user_id is not None):
        category_map[category.name] = category.id
    return category_map


def resolve_category_id(cat_name, cat_map):
    """Kategoria id feloldas: pontos, normalizalt, alias, vegul Egyeb."""
    direct = cat_map.get(cat_name)
    if direct:
        return direct

    normalized_name = _normalize(cat_name)
    for name, category_id in cat_map.items():
        if _normalize(name) == normalized_name:
            return category_id

    canonical_name = get_category_aliases().get(normalized_name)
    if canonical_name:
        direct = cat_map.get(canonical_name)
        if direct:
            return direct

    for name, category_id in cat_map.items():
        if _normalize(name) == _normalize('Egyéb'):
            return category_id

    return None
