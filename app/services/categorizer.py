# Categorizer – kategoria nev -> id feloldas
import unicodedata

from app.models.category import Category


def _normalize(text):
    """Ekezetek eltavolitasa osszehasonlitashoz."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


def build_category_map(user_id):
    """Kategoria nev -> id map (sajat + globalis)."""
    cats = Category.query.filter(
        (Category.user_id == user_id) | (Category.user_id.is_(None))
    ).all()
    return {c.name: c.id for c in cats}


def resolve_category_id(cat_name, cat_map):
    """Kategoria id feloldas: elobb pontos, aztan ekezet nelkuli egyezes."""
    direct = cat_map.get(cat_name)
    if direct:
        return direct
    norm = _normalize(cat_name)
    for name, cid in cat_map.items():
        if _normalize(name) == norm:
            return cid
    return None
# Vasarlas, Kozuzemi dijak, Lakhatas, Egeszseg, Egyeb
