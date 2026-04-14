"""
HUTKO — orders.py
Uses token-based auth via Authorization header.
"""

import json
import random
import string
from flask import Blueprint, request, jsonify, g
from database import get_db
from auth import optional_token, token_required
from emails import send_order_confirmation, send_order_notification, send_delivery_dispatch
from trello import create_order_card, move_card, add_comment, get_card_by_order_ref

orders_bp = Blueprint('orders', __name__)

DELIVERY_PRICES = {'standard': 5.0, 'express': 12.0, 'free': 0.0}


def make_ref():
    chars = string.ascii_uppercase + string.digits
    return 'HK-' + ''.join(random.choices(chars, k=6))


@orders_bp.route('/api/checkout', methods=['POST'])
@optional_token
def checkout():
    data = request.get_json()
    required = ['first_name', 'last_name', 'email', 'phone',
                'street', 'postcode', 'city', 'province', 'items']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    items = data['items']
    if not items:
        return jsonify({'error': 'Cart is empty.'}), 400

    delivery_method = data.get('delivery_method', 'standard')
    subtotal     = sum(i['price'] * i['qty'] for i in items)
    delivery_cost = 0.0 if subtotal >= 60 else DELIVERY_PRICES.get(delivery_method, 5.0)
    total        = subtotal + delivery_cost
    order_ref    = make_ref()
    user_id      = g.user['id'] if g.user else None

    from database import _use_postgres
    p = '%s' if _use_postgres() else '?'

    conn = get_db()
    while conn.execute(f"SELECT id FROM orders WHERE order_ref={p}", (order_ref,)).fetchone():
        order_ref = make_ref()

    delivery_date = data.get('delivery_date', '')

    if _use_postgres():
        cur = conn.cursor()
        cur.execute(f"""
            INSERT INTO orders
              (order_ref, user_id, customer_name, customer_email, customer_phone,
               addr_street, addr_postcode, addr_city, addr_province, delivery_notes,
               delivery_method, delivery_date, items_json, subtotal, delivery_cost, total, status)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},'confirmed')
        """, (
            order_ref, user_id,
            f"{data['first_name']} {data['last_name']}",
            data['email'], data['phone'],
            data['street'], data['postcode'], data['city'], data['province'],
            data.get('notes', ''), delivery_method, delivery_date,
            json.dumps(items), subtotal, delivery_cost, total
        ))
    else:
        conn.execute("""
            INSERT INTO orders
              (order_ref, user_id, customer_name, customer_email, customer_phone,
               addr_street, addr_postcode, addr_city, addr_province, delivery_notes,
               delivery_method, delivery_date, items_json, subtotal, delivery_cost, total, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'confirmed')
        """, (
            order_ref, user_id,
            f"{data['first_name']} {data['last_name']}",
            data['email'], data['phone'],
            data['street'], data['postcode'], data['city'], data['province'],
            data.get('notes', ''), delivery_method, delivery_date,
            json.dumps(items), subtotal, delivery_cost, total
        ))
    conn.commit()
    conn.close()

    # Send emails + create Trello card
    customer_name  = f"{data['first_name']} {data['last_name']}"
    customer_addr  = f"{data['street']}, {data['postcode']} {data['city']}, {data['province']}"
    try:
        send_order_confirmation(
            order_ref, customer_name, data['email'],
            items, subtotal, delivery_cost, total,
            customer_addr, delivery_method, delivery_date
        )
        send_order_notification(
            order_ref, customer_name, data['email'],
            data['phone'], items, total,
            customer_addr, delivery_method, data.get('notes', ''),
            delivery_date
        )
    except Exception as e:
        print(f"[ORDER EMAIL ERROR] {e}")

    # Create Trello card
    try:
        card_id = create_order_card(
            order_ref, customer_name, data['email'], data['phone'],
            items, subtotal, delivery_cost, total,
            customer_addr, delivery_method, data.get('notes', '')
        )
        # Save card_id to order in DB
        if card_id:
            conn2 = get_db()
            conn2.execute(
                "UPDATE orders SET trello_card_id=? WHERE order_ref=?",
                (card_id, order_ref)
            )
            conn2.commit()
            conn2.close()
    except Exception as e:
        print(f"[TRELLO ERROR] {e}")

    return jsonify({
        'order_ref': order_ref, 'total': total,
        'subtotal': subtotal, 'delivery_cost': delivery_cost, 'status': 'confirmed',
    }), 201


@orders_bp.route('/api/orders', methods=['GET'])
@token_required
def get_my_orders():
    from database import _use_postgres
    conn = get_db()
    p    = '%s' if _use_postgres() else '?'
    rows = conn.execute(
        f"SELECT * FROM orders WHERE user_id={p} ORDER BY created_at DESC",
        (g.user['id'],)
    ).fetchall()
    conn.close()
    orders = []
    for r in rows:
        o = dict(r)
        o['items'] = json.loads(o['items_json'])
        del o['items_json']
        orders.append(o)
    return jsonify({'orders': orders}), 200


@orders_bp.route('/api/orders/<ref>', methods=['GET'])
def get_order(ref):
    conn = get_db()
    row  = conn.execute("SELECT * FROM orders WHERE order_ref=?", (ref,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Order not found.'}), 404
    o = dict(row)
    o['items'] = json.loads(o['items_json'])
    del o['items_json']
    return jsonify({'order': o}), 200


# ── UPDATE ORDER STATUS (called manually or by webhook) ──
@orders_bp.route('/api/orders/<ref>/status', methods=['PUT'])
def update_order_status(ref):
    # Allow either an admin token OR a webhook secret header
    from admin import _admin_tokens
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    webhook_secret = request.headers.get('X-Webhook-Secret', '')
    import os
    expected_secret = os.environ.get('WEBHOOK_SECRET', '')
    if token not in _admin_tokens and not (expected_secret and webhook_secret == expected_secret):
        return jsonify({'error': 'Admin access required.'}), 403

    data       = request.get_json()
    new_status = data.get('status', '')
    comment    = data.get('comment', '')

    valid = ['confirmed', 'cooking', 'storage', 'delivery', 'delivered', 'ok_confirmed', 'cancelled']
    if new_status not in valid:
        return jsonify({'error': f'Invalid status. Use: {valid}'}), 400

    # Status → Trello list mapping
    trello_map = {
        'confirmed':    'confirmed',
        'cooking':      'confirmed',
        'storage':      'in_storage',
        'delivery':     'out_for_delivery',
        'delivered':    'delivered',
        'ok_confirmed': 'ok_confirmed',
        'cancelled':    'cancelled',
    }

    conn = get_db()
    row  = conn.execute("SELECT * FROM orders WHERE order_ref=?", (ref,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404

    conn.execute("UPDATE orders SET status=? WHERE order_ref=?", (new_status, ref))
    conn.commit()

    # Send dispatch email when order goes out for delivery
    if new_status == 'delivery':
        try:
            send_delivery_dispatch(
                ref,
                row['customer_name'],
                row['customer_email'],
                row.get('delivery_date', '') or ''
            )
        except Exception as e:
            print(f"[DISPATCH EMAIL ERROR] {e}")

    # Move Trello card
    try:
        card_id = row['trello_card_id'] if 'trello_card_id' in row.keys() else None
        if not card_id:
            card_id = get_card_by_order_ref(ref)
        if card_id:
            move_card(card_id, trello_map[new_status])
            if comment:
                add_comment(card_id, f"Status → **{new_status}**\n{comment}")
    except Exception as e:
        print(f"[TRELLO STATUS ERROR] {e}")

    conn.close()
    return jsonify({'order_ref': ref, 'status': new_status}), 200


# ── DELIVERY CONFIRMATION (customer confirms receipt) ────
@orders_bp.route('/api/orders/<ref>/confirm-delivery', methods=['POST'])
def confirm_delivery(ref):
    data    = request.get_json()
    message = (data.get('message') or '').strip()
    rating  = data.get('rating', 5)

    conn = get_db()
    row  = conn.execute("SELECT * FROM orders WHERE order_ref=?", (ref,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404

    conn.execute("UPDATE orders SET status='ok_confirmed' WHERE order_ref=?", (ref,))
    conn.commit()
    conn.close()

    # Move card to Ok: Confirmed + add customer comment
    try:
        card_id = get_card_by_order_ref(ref)
        if card_id:
            move_card(card_id, 'ok_confirmed')
            comment_text = f"✅ Customer confirmed delivery!\n⭐ Rating: {rating}/5"
            if message:
                comment_text += f"\n\n💬 Customer says:\n{message}"
            add_comment(card_id, comment_text)
    except Exception as e:
        print(f"[TRELLO CONFIRM ERROR] {e}")

    return jsonify({'message': 'Delivery confirmed. Thank you!'}), 200


# ── DELIVERY SLOTS AVAILABILITY ──────────────────────────
MAX_SLOTS_PER_DAY = 15

@orders_bp.route('/api/slots/availability', methods=['GET'])
def slots_availability():
    """
    Returns booked count per date for the requested dates.
    Query param: ?dates=2026-04-10,2026-04-12,...
    Response: {"2026-04-10": 3, "2026-04-12": 0, ...}
    """
    dates_param = request.args.get('dates', '')
    if not dates_param:
        return jsonify({}), 200

    dates = [d.strip() for d in dates_param.split(',') if d.strip()]
    conn  = get_db()
    result = {}

    from database import _use_postgres
    p = '%s' if _use_postgres() else '?'

    for date in dates:
        row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM orders WHERE delivery_date = {p} AND status != 'cancelled'",
            (date,)
        ).fetchone()
        result[date] = row['cnt'] if row else 0

    conn.close()
    return jsonify(result), 200