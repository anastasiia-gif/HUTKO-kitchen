"""
HUTKO — orders.py
Handles order placement and retrieval.
"""

import json
import random
import string
from flask import Blueprint, request, jsonify, session
from database import get_db
from auth import current_user

orders_bp = Blueprint('orders', __name__)

DELIVERY_PRICES = {'standard': 5.0, 'express': 12.0, 'free': 0.0}


def make_ref():
    """Generate a human-readable order reference like HK-A3X9K2."""
    chars = string.ascii_uppercase + string.digits
    return 'HK-' + ''.join(random.choices(chars, k=6))


# ── PLACE ORDER ──────────────────────────────────────────
@orders_bp.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.get_json()

    required = ['first_name', 'last_name', 'email', 'phone',
                'street', 'postcode', 'city', 'province', 'items']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    items = data['items']  # list of {name, emoji, price, label, qty}
    if not items:
        return jsonify({'error': 'Cart is empty.'}), 400

    delivery_method = data.get('delivery_method', 'standard')
    subtotal = sum(i['price'] * i['qty'] for i in items)
    delivery_cost = 0.0 if subtotal >= 60 else DELIVERY_PRICES.get(delivery_method, 5.0)
    total = subtotal + delivery_cost

    order_ref = make_ref()
    customer_name = f"{data['first_name']} {data['last_name']}"
    user_id = session.get('user_id')

    conn = get_db()
    # Ensure unique ref
    while conn.execute("SELECT id FROM orders WHERE order_ref=?", (order_ref,)).fetchone():
        order_ref = make_ref()

    conn.execute("""
        INSERT INTO orders
          (order_ref, user_id, customer_name, customer_email, customer_phone,
           addr_street, addr_postcode, addr_city, addr_province, delivery_notes,
           delivery_method, items_json, subtotal, delivery_cost, total, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'confirmed')
    """, (
        order_ref, user_id, customer_name,
        data['email'], data['phone'],
        data['street'], data['postcode'], data['city'], data['province'],
        data.get('notes', ''),
        delivery_method,
        json.dumps(items),
        subtotal, delivery_cost, total
    ))
    conn.commit()
    conn.close()

    return jsonify({
        'order_ref':     order_ref,
        'total':         total,
        'subtotal':      subtotal,
        'delivery_cost': delivery_cost,
        'status':        'confirmed',
    }), 201


# ── GET MY ORDERS (logged-in user) ───────────────────────
@orders_bp.route('/api/orders', methods=['GET'])
def get_my_orders():
    user = current_user()
    if not user:
        return jsonify({'error': 'Not logged in.'}), 401

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC",
        (user['id'],)
    ).fetchall()
    conn.close()

    orders = []
    for r in rows:
        o = dict(r)
        o['items'] = json.loads(o['items_json'])
        del o['items_json']
        orders.append(o)

    return jsonify({'orders': orders}), 200


# ── GET SINGLE ORDER ─────────────────────────────────────
@orders_bp.route('/api/orders/<ref>', methods=['GET'])
def get_order(ref):
    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE order_ref=?", (ref,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Order not found.'}), 404
    o = dict(row)
    o['items'] = json.loads(o['items_json'])
    del o['items_json']
    return jsonify({'order': o}), 200


# ── UPDATE STATUS (admin) ────────────────────────────────
@orders_bp.route('/api/orders/<ref>/status', methods=['PUT'])
def update_status(ref):
    # Simple admin check — in production replace with proper admin auth
    if not session.get('is_admin'):
        return jsonify({'error': 'Forbidden.'}), 403
    data = request.get_json()
    status = data.get('status')
    if status not in ('confirmed', 'processing', 'delivered', 'cancelled'):
        return jsonify({'error': 'Invalid status.'}), 400
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE order_ref=?", (status, ref))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Status updated.'}), 200
