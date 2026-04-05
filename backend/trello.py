"""
HUTKO — trello.py
Full Trello integration for order management.
Creates cards, moves them through columns, calculates cook time.
"""

import os
import math
import requests
from datetime import datetime, timedelta

TRELLO_API_KEY = os.environ.get('TRELLO_API_KEY', '')
TRELLO_TOKEN   = os.environ.get('TRELLO_TOKEN', '')

# Board & List IDs
BOARD_ID = '69c83bc12f4c3402415b14d3'
LISTS = {
    'new_orders':       '69d29b50f81815133e083e42',
    'confirmed':        '69d29b5c4d746c0f0a4a201f',
    'in_storage':       '69d29b6e70155674b2fe1157',
    'out_for_delivery': '69d29b792569d8d839a78dc3',
    'delivered':        '69d29b87e98a49718dddd4a5',
    'cancelled':        '69d29b94c21f6521a96e613a',
}

# Cook time per unit (minutes) based on Excel production data
# Batch sizes: Syrnyky=100pcs/1.5h, Chicken=100pcs/1.5h, Zrazy=30pcs/1.5h
# Borscht=15L/1h, Solyanka=15L/1h, Shakshuka=20pcs/1h
COOK_MINUTES_PER_UNIT = {
    'syrnyky':      (90 / 100),   # 1.5h / 100pcs = 0.9 min/pc
    'chicken':      (90 / 100),   # 1.5h / 100pcs
    'kyiv':         (90 / 100),   # same as chicken
    'zrazy':        (90 / 30),    # 1.5h / 30pcs  = 3 min/pc
    'borscht':      (60 / 15),    # 1h   / 15L    = 4 min/L (900ml ≈ 0.9L)
    'borsch':       (60 / 15),
    'solyanka':     (60 / 15),    # 1h   / 15L
    'shakshuka':    (60 / 20),    # 1h   / 20pcs  = 3 min/pc
}

BASE_PREP_MINUTES = 30  # packing & freezing time added to every order


def _auth():
    return {'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN}


def _calculate_cook_time(items: list) -> int:
    """
    Calculate total cook time in minutes for an order.
    Returns total minutes rounded up to nearest 15.
    """
    total = BASE_PREP_MINUTES
    for item in items:
        name_lower = item.get('name', '').lower()
        qty = item.get('qty', 1)

        minutes_per = 0
        for keyword, mpp in COOK_MINUTES_PER_UNIT.items():
            if keyword in name_lower:
                minutes_per = mpp
                break

        total += minutes_per * qty

    # Round up to nearest 15 minutes
    return int(math.ceil(total / 15) * 15)


def _format_cook_time(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    if h and m:
        return f"{h}h {m}min"
    elif h:
        return f"{h}h"
    else:
        return f"{m}min"


def _get_delivery_day(order_date: datetime = None) -> str:
    """
    Returns next Thursday or Saturday from order date.
    Delivery days: Thursday (3) and Saturday (5).
    """
    if not order_date:
        order_date = datetime.now()

    weekday = order_date.weekday()  # 0=Mon, 3=Thu, 5=Sat

    days_to_thu = (3 - weekday) % 7 or 7
    days_to_sat = (5 - weekday) % 7 or 7

    next_thu = order_date + timedelta(days=days_to_thu)
    next_sat = order_date + timedelta(days=days_to_sat)

    # Pick the sooner one — but must be at least 1 day away
    if days_to_thu <= days_to_sat:
        delivery = next_thu
    else:
        delivery = next_sat

    return delivery.strftime('%A, %d %B %Y')


def create_order_card(order_ref: str, name: str, email: str, phone: str,
                      items: list, subtotal: float, delivery_cost: float,
                      total: float, address: str, delivery_method: str,
                      notes: str = '') -> str | None:
    """
    Create a Trello card in 'New Orders' list.
    Returns card ID or None if failed.
    """
    if not TRELLO_API_KEY or not TRELLO_TOKEN:
        print('[TRELLO SKIPPED] No API key/token configured')
        return None

    cook_minutes = _calculate_cook_time(items)
    cook_time    = _format_cook_time(cook_minutes)
    delivery_day = _get_delivery_day()

    items_text = '\n'.join([
        f"- {i['name']} ×{i['qty']} — €{i['qty'] * i['price']}"
        for i in items
    ])

    description = f"""## 🛒 Order #{order_ref}

**Customer**
👤 {name}
📧 {email}
📞 {phone}

**Delivery address**
📍 {address}
🚚 Method: {delivery_method}
{'📝 Note: ' + notes if notes else ''}

---

**Items ordered**
{items_text}

---

**Financials**
Subtotal: €{subtotal}
Delivery: {'Free' if delivery_cost == 0 else f'€{delivery_cost}'}
**Total: €{total}**

---

**Production planning**
⏱ Estimated cook time: **{cook_time}**
📅 Expected delivery: **{delivery_day}**

---
*Card created automatically by HUTKO Kitchen system*
"""

    # Card due date = expected delivery day
    delivery_date_obj = datetime.now()
    weekday = delivery_date_obj.weekday()
    days_to_thu = (3 - weekday) % 7 or 7
    days_to_sat = (5 - weekday) % 7 or 7
    days_ahead = min(days_to_thu, days_to_sat)
    due = (delivery_date_obj + timedelta(days=days_ahead)).strftime('%Y-%m-%dT12:00:00.000Z')

    try:
        res = requests.post(
            'https://api.trello.com/1/cards',
            params=_auth(),
            json={
                'idList': LISTS['new_orders'],
                'name':   f'#{order_ref} — {name} — €{total}',
                'desc':   description,
                'due':    due,
            },
            timeout=10
        )
        res.raise_for_status()
        card_id = res.json()['id']
        print(f'[TRELLO] Card created: {card_id} for order {order_ref}')
        return card_id
    except Exception as e:
        print(f'[TRELLO ERROR] create_order_card: {e}')
        return None


def move_card(card_id: str, list_name: str) -> bool:
    """
    Move a card to a different list.
    list_name: 'new_orders' | 'confirmed' | 'in_storage' |
               'out_for_delivery' | 'delivered' | 'cancelled'
    """
    if not card_id or list_name not in LISTS:
        return False
    try:
        res = requests.put(
            f'https://api.trello.com/1/cards/{card_id}',
            params=_auth(),
            json={'idList': LISTS[list_name]},
            timeout=10
        )
        res.raise_for_status()
        print(f'[TRELLO] Card {card_id} moved to {list_name}')
        return True
    except Exception as e:
        print(f'[TRELLO ERROR] move_card: {e}')
        return False


def add_comment(card_id: str, comment: str) -> bool:
    """Add a comment to a Trello card."""
    if not card_id:
        return False
    try:
        res = requests.post(
            f'https://api.trello.com/1/cards/{card_id}/actions/comments',
            params=_auth(),
            json={'text': comment},
            timeout=10
        )
        res.raise_for_status()
        return True
    except Exception as e:
        print(f'[TRELLO ERROR] add_comment: {e}')
        return False


def get_card_by_order_ref(order_ref: str) -> str | None:
    """Find a card by searching for order ref in card name."""
    try:
        res = requests.get(
            f'https://api.trello.com/1/boards/{BOARD_ID}/cards',
            params={**_auth(), 'fields': 'id,name'},
            timeout=10
        )
        res.raise_for_status()
        for card in res.json():
            if order_ref in card.get('name', ''):
                return card['id']
        return None
    except Exception as e:
        print(f'[TRELLO ERROR] get_card_by_order_ref: {e}')
        return None
