"""
HUTKO — orders.py
Token-based auth via Authorization header.

v1.1:
  • Delivery pricing is area/zone based (fee_local / fee_regional) with free delivery
    over free_delivery_over — the same settings the checkout page reads, so the recorded
    fee matches what the customer is charged.
  • Fixed the admin guard on PUT /orders/<ref>/status (was a dead stub).
"""

import json
import os
import random
import string
from flask import Blueprint, request, jsonify, g, redirect
from database import get_db
from auth import optional_token, token_required
from emails import send_order_confirmation, send_order_notification, send_delivery_dispatch
from trello import create_order_card, move_card, add_comment, get_card_by_order_ref
from settings_store import get_float

orders_bp = Blueprint('orders', __name__)

def compute_delivery_cost(subtotal, method):
    """Area/zone delivery fee, matching the checkout page.
       local (Amsterdam/Den Bosch/Den Haag) → fee_local; other provinces → fee_regional;
       pickup → free; free over the configured threshold (all zones)."""
    method = (method or '').strip()
    if method.startswith('pickup'):
        return 0.0
    free_over = get_float('free_delivery_over', 100.0)
    if free_over > 0 and subtotal >= free_over:
        return 0.0
    if method == 'delivery_local':
        return get_float('fee_local', 10.0)
    # delivery_other / delivery_contact / fallback → regional
    return get_float('fee_regional', 15.0)


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

    delivery_method = data.get('delivery_method', 'delivery_local')
    subtotal        = sum(i['price'] * i['qty'] for i in items)
    delivery_cost   = compute_delivery_cost(subtotal, delivery_method)
    total           = subtotal + delivery_cost
    order_ref       = make_ref()
    user_id         = g.user['id'] if g.user else None

    from database import _use_postgres
    p = '%s' if _use_postgres() else '?'

    conn = get_db()
    while conn.execute(f"SELECT id FROM orders WHERE order_ref={p}", (order_ref,)).fetchone():
        order_ref = make_ref()

    delivery_date = data.get('delivery_date', '')

    conn.execute("""
        INSERT INTO orders
          (order_ref, user_id, customer_name, customer_email, customer_phone,
           addr_street, addr_postcode, addr_city, addr_province, delivery_notes,
           delivery_method, delivery_date, items_json, subtotal, delivery_cost, total, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending_payment')
    """, (
        order_ref, user_id, f"{data['first_name']} {data['last_name']}",
        data['email'], data['phone'], data['street'], data['postcode'], data['city'], data['province'],
        data.get('notes', ''), delivery_method, delivery_date,
        json.dumps(items), subtotal, delivery_cost, total))
    conn.commit()
    conn.close()

    print(f"[ORDER] Created {order_ref} — awaiting payment")
    return jsonify({'order_ref': order_ref, 'total': total,
                    'subtotal': subtotal, 'delivery_cost': delivery_cost, 'status': 'confirmed'}), 201


@orders_bp.route('/api/orders', methods=['GET'])
@token_required
def get_my_orders():
    from database import _use_postgres
    conn = get_db()
    p = '%s' if _use_postgres() else '?'
    rows = conn.execute(f"SELECT * FROM orders WHERE user_id={p} ORDER BY created_at DESC", (g.user['id'],)).fetchall()
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
    from database import _use_postgres
    p = '%s' if _use_postgres() else '?'
    row = conn.execute(f"SELECT * FROM orders WHERE order_ref={p}", (ref,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Order not found.'}), 404
    o = dict(row)
    o['items'] = json.loads(o['items_json'])
    del o['items_json']
    return jsonify({'order': o}), 200


@orders_bp.route('/api/orders/<ref>/status', methods=['PUT'])
def update_order_status(ref):
    from admin import _admin_token_valid
    from database import _use_postgres
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    webhook_secret = request.headers.get('X-Webhook-Secret', '')
    expected_secret = os.environ.get('WEBHOOK_SECRET', '')
    if not _admin_token_valid(token) and not (expected_secret and webhook_secret == expected_secret):
        return jsonify({'error': 'Admin access required.'}), 403

    data = request.get_json()
    new_status = data.get('status', '')
    comment = data.get('comment', '')
    valid = ['confirmed', 'cooking', 'storage', 'delivery', 'delivered', 'ok_confirmed', 'cancelled']
    if new_status not in valid:
        return jsonify({'error': f'Invalid status. Use: {valid}'}), 400
    trello_map = {'confirmed': 'confirmed', 'cooking': 'confirmed', 'storage': 'in_storage',
                  'delivery': 'out_for_delivery', 'delivered': 'delivered',
                  'ok_confirmed': 'ok_confirmed', 'cancelled': 'cancelled'}

    conn = get_db()
    p = '%s' if _use_postgres() else '?'
    row = conn.execute(f"SELECT * FROM orders WHERE order_ref={p}", (ref,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
    conn.execute(f"UPDATE orders SET status={p} WHERE order_ref={p}", (new_status, ref))
    conn.commit()

    if new_status == 'delivery':
        try:
            send_delivery_dispatch(ref, row['customer_name'], row['customer_email'],
                                   row['delivery_date'] if 'delivery_date' in dict(row) else '')
        except Exception as e:
            print(f"[DISPATCH EMAIL ERROR] {e}")
    try:
        card_id = row['trello_card_id'] if 'trello_card_id' in dict(row) else None
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


@orders_bp.route('/api/orders/<ref>/confirm-delivery-link', methods=['GET'])
def confirm_delivery_link(ref):
    frontend = os.environ.get('FRONTEND_URL', 'https://hutko-kitchen.com').rstrip('/')
    conn = get_db()
    from database import _use_postgres
    p = '%s' if _use_postgres() else '?'
    row = conn.execute(f"SELECT * FROM orders WHERE order_ref={p}", (ref,)).fetchone()
    if not row:
        conn.close()
        return redirect(f"{frontend}/?confirm=notfound&ref={ref}")
    if row['status'] in ('ok_confirmed', 'delivered'):
        conn.close()
        return redirect(f"{frontend}/?confirm=already&ref={ref}")
    conn.execute(f"UPDATE orders SET status='ok_confirmed' WHERE order_ref={p}", (ref,))
    conn.commit()
    conn.close()
    try:
        card_id = row['trello_card_id'] if 'trello_card_id' in dict(row) else None
        if not card_id:
            card_id = get_card_by_order_ref(ref)
        if card_id:
            move_card(card_id, 'ok_confirmed')
            add_comment(card_id, "✅ Customer confirmed delivery via email link!")
    except Exception as e:
        print(f"[TRELLO CONFIRM LINK ERROR] {e}")
    return redirect(f"{frontend}/?confirm=success&ref={ref}")


@orders_bp.route('/api/orders/<ref>/confirm-delivery', methods=['POST'])
def confirm_delivery(ref):
    data = request.get_json()
    message = (data.get('message') or '').strip()
    rating = data.get('rating', 5)
    conn = get_db()
    from database import _use_postgres
    p = '%s' if _use_postgres() else '?'
    row = conn.execute(f"SELECT * FROM orders WHERE order_ref={p}", (ref,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
    conn.execute(f"UPDATE orders SET status='ok_confirmed' WHERE order_ref={p}", (ref,))
    conn.commit()
    conn.close()
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


@orders_bp.route('/api/slots/availability', methods=['GET'])
def slots_availability():
    dates_param = request.args.get('dates', '')
    if not dates_param:
        return jsonify({}), 200
    dates = [d.strip() for d in dates_param.split(',') if d.strip()]
    conn = get_db()
    result = {}
    from database import _use_postgres
    p = '%s' if _use_postgres() else '?'
    for date in dates:
        row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM orders WHERE delivery_date = {p} AND status != 'cancelled'",
            (date,)).fetchone()
        result[date] = row['cnt'] if row else 0
    conn.close()
    return jsonify(result), 200
