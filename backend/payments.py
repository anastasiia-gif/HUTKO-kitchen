"""
HUTKO — payments.py  (Stripe Checkout)

Flow:
  1. POST /api/payment/create  — creates Stripe session, returns URL
  2. Customer pays on Stripe hosted page
  3. Stripe calls POST /api/stripe-webhook — marks paid, creates Trello card + sends email
  4. Customer redirected to confirm-delivery.html?ref=HK-XXXX&paid=1

Render environment variables to set:
  STRIPE_SECRET_KEY      sk_live_51TVbx...
  STRIPE_PUBLISHABLE_KEY pk_live_51TVbx...
  STRIPE_WEBHOOK_SECRET  whsec_... (after adding webhook in Stripe Dashboard)
"""

import os, json
import stripe
from flask import Blueprint, request, jsonify
from database import get_db, _use_postgres

payments_bp    = Blueprint('payments', __name__)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WH_KEY  = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
SITE_URL       = os.environ.get('FRONTEND_URL', 'https://hutko-kitchen.com')


def _p():
    return '%s' if _use_postgres() else '?'


def _exec(conn, sql, params=()):
    if _use_postgres():
        cur = conn.cursor(); cur.execute(sql, params); return cur
    return conn.execute(sql, params)


def _process_paid_order(order_ref):
    """Send confirmation email + notification + create Trello card after payment."""
    conn = get_db()
    row  = _exec(conn, f"""
        SELECT order_ref, customer_name, customer_email, customer_phone,
               addr_street, addr_postcode, addr_city, addr_province,
               delivery_notes, delivery_method, delivery_date,
               items_json, subtotal, delivery_cost, total
        FROM orders WHERE order_ref={_p()}
    """, (order_ref,)).fetchone()
    conn.close()
    if not row:
        return print(f'[STRIPE] order not found: {order_ref}')

    items = json.loads(row['items_json'])
    addr  = f"{row['addr_street']}, {row['addr_postcode']} {row['addr_city']}"

    try:
        from emails import send_order_confirmation, send_order_notification
        send_order_confirmation(row['order_ref'], row['customer_name'], row['customer_email'],
                                items, row['subtotal'], row['delivery_cost'], row['total'],
                                addr, row['delivery_method'], row['delivery_date'])
        send_order_notification(row['order_ref'], row['customer_name'], row['customer_email'],
                                row['customer_phone'], items, row['total'],
                                addr, row['delivery_method'], row['delivery_notes'] or '', row['delivery_date'])
    except Exception as e:
        print(f'[STRIPE EMAIL ERROR] {e}')

    try:
        from trello import create_order_card
        card_id = create_order_card(row['order_ref'], row['customer_name'], row['customer_email'],
                                    row['customer_phone'], items, row['subtotal'],
                                    row['delivery_cost'], row['total'],
                                    addr, row['delivery_method'], row['delivery_notes'] or '')
        if card_id:
            conn2 = get_db()
            _exec(conn2, f"UPDATE orders SET trello_card_id={_p()} WHERE order_ref={_p()}", (card_id, order_ref))
            conn2.commit(); conn2.close()
    except Exception as e:
        print(f'[STRIPE TRELLO ERROR] {e}')


@payments_bp.route('/api/payment/create', methods=['POST'])
def create_payment():
    if not stripe.api_key:
        return jsonify({'error': 'Payment not configured.'}), 503

    data          = request.get_json()
    order_ref     = data.get('order_ref', '')
    items         = data.get('items', [])
    delivery_fee  = float(data.get('delivery_fee', 0))
    customer_email = data.get('customer_email', '')

    if not order_ref:
        return jsonify({'error': 'Missing order_ref.'}), 400

    line_items = [{'price_data': {'currency': 'eur',
                                   'product_data': {'name': i['name']},
                                   'unit_amount': int(float(i['price']) * 100)},
                   'quantity': int(i.get('qty', 1))} for i in items]

    if delivery_fee > 0:
        line_items.append({'price_data': {'currency': 'eur',
                                           'product_data': {'name': 'Delivery / Bezorging'},
                                           'unit_amount': int(delivery_fee * 100)},
                           'quantity': 1})
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer_email=customer_email or None,
            success_url=f'{SITE_URL}/confirm-delivery.html?ref={order_ref}&paid=1',
            cancel_url=f'{SITE_URL}/checkout.html?cancelled=1',
            metadata={'order_ref': order_ref},
            locale='auto',
        )
        conn = get_db()
        _exec(conn, f"UPDATE orders SET payment_id={_p()} WHERE order_ref={_p()}", (session.id, order_ref))
        conn.commit(); conn.close()
        return jsonify({'payment_url': session.url}), 200
    except stripe.error.StripeError as e:
        print(f'[STRIPE ERROR] {e}')
        return jsonify({'error': str(e)}), 502
    except Exception as e:
        print(f'[PAYMENT ERROR] {e}')
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig     = request.headers.get('Stripe-Signature', '')
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WH_KEY) if STRIPE_WH_KEY \
                else stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except Exception as e:
        return '', 400

    if event['type'] == 'checkout.session.completed':
        s         = event['data']['object']
        metadata  = s['metadata'] if 'metadata' in s else {}
        order_ref = metadata.get('order_ref', '') if isinstance(metadata, dict) else getattr(metadata, 'order_ref', '')
        pay_status = s['payment_status'] if 'payment_status' in s else ''
        if order_ref and pay_status == 'paid':
            conn = get_db()
            _exec(conn, f"UPDATE orders SET payment_status='paid', status='confirmed' WHERE order_ref={_p()}", (order_ref,))
            conn.commit(); conn.close()
            _process_paid_order(order_ref)

    elif event['type'] == 'checkout.session.expired':
        s         = event['data']['object']
        metadata  = s['metadata'] if 'metadata' in s else {}
        order_ref = metadata.get('order_ref', '') if isinstance(metadata, dict) else getattr(metadata, 'order_ref', '')
        if order_ref:
            conn = get_db()
            _exec(conn, f"UPDATE orders SET payment_status='expired' WHERE order_ref={_p()}", (order_ref,))
            conn.commit(); conn.close()

    return '', 200


@payments_bp.route('/api/payment/status/<order_ref>', methods=['GET'])
def payment_status(order_ref):
    conn = get_db()
    row  = _exec(conn, f"SELECT payment_status, total FROM orders WHERE order_ref={_p()}", (order_ref,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'payment_status': row['payment_status'] or 'pending', 'total': row['total']}), 200
