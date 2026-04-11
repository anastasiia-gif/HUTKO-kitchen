"""
HUTKO — payments.py
Mollie iDEAL / credit card payment integration for Netherlands.
Requires MOLLIE_API_KEY env var (get from mollie.com — free account).

Flow:
  1. POST /api/payment/create  — creates Mollie payment, returns checkout URL
  2. Customer pays on Mollie hosted page
  3. Mollie calls POST /api/payment/webhook  — updates order status
  4. Customer redirected to GET /api/payment/return?ref=HK-XXXX
"""

import os
import json
import requests
from flask import Blueprint, request, jsonify, redirect
from database import get_db, _use_postgres

payments_bp = Blueprint('payments', __name__)

MOLLIE_API_KEY  = os.environ.get('MOLLIE_API_KEY', '')
MOLLIE_API_BASE = 'https://api.mollie.com/v2'
SITE_URL        = os.environ.get('FRONTEND_URL', 'https://hutko-kitchen.com')
BACKEND_URL     = os.environ.get('RENDER_EXTERNAL_URL', 'https://hutko-kitchen.onrender.com')


def _mollie_headers():
    return {
        'Authorization': f'Bearer {MOLLIE_API_KEY}',
        'Content-Type':  'application/json',
    }


def _p():
    return '%s' if _use_postgres() else '?'


def _exec(conn, sql, params=()):
    if _use_postgres():
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur
    return conn.execute(sql, params)


@payments_bp.route('/api/payment/create', methods=['POST'])
def create_payment():
    """
    Called from checkout after order is placed.
    Body: { order_ref, total, description, customer_email }
    Returns: { payment_url } — redirect the customer here
    """
    if not MOLLIE_API_KEY:
        return jsonify({'error': 'Online payment not configured yet.'}), 503

    data        = request.get_json()
    order_ref   = data.get('order_ref', '')
    total       = data.get('total', 0)
    email       = data.get('customer_email', '')
    description = data.get('description', f'HUTKO order #{order_ref}')

    if not order_ref or not total:
        return jsonify({'error': 'Missing order_ref or total.'}), 400

    try:
        res = requests.post(
            f'{MOLLIE_API_BASE}/payments',
            headers=_mollie_headers(),
            json={
                'amount':      {'currency': 'EUR', 'value': f'{float(total):.2f}'},
                'description': description,
                'redirectUrl': f'{SITE_URL}/confirm-delivery.html?ref={order_ref}&paid=1',
                'webhookUrl':  f'{BACKEND_URL}/api/payment/webhook',
                'metadata':    {'order_ref': order_ref, 'email': email},
                'method':      ['ideal', 'creditcard', 'bancontact'],
                'locale':      'nl_NL',
            },
            timeout=10
        )
        res.raise_for_status()
        payment = res.json()
        payment_id  = payment['id']
        payment_url = payment['_links']['checkout']['href']

        # Save payment_id to order
        conn = get_db()
        p    = _p()
        _exec(conn, f"UPDATE orders SET payment_id={p} WHERE order_ref={p}", (payment_id, order_ref))
        conn.commit()
        conn.close()

        return jsonify({'payment_url': payment_url, 'payment_id': payment_id}), 200

    except requests.HTTPError as e:
        print(f'[MOLLIE ERROR] {e.response.text}')
        return jsonify({'error': 'Payment service error. Please try again.'}), 502
    except Exception as e:
        print(f'[PAYMENT ERROR] {e}')
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/api/payment/webhook', methods=['POST'])
def payment_webhook():
    """
    Mollie calls this when payment status changes.
    Body (form-encoded): id=<payment_id>
    """
    if not MOLLIE_API_KEY:
        return '', 200

    payment_id = request.form.get('id') or (request.get_json(silent=True) or {}).get('id')
    if not payment_id:
        return '', 200

    try:
        res = requests.get(
            f'{MOLLIE_API_BASE}/payments/{payment_id}',
            headers=_mollie_headers(),
            timeout=10
        )
        res.raise_for_status()
        payment    = res.json()
        status     = payment.get('status')       # paid / failed / canceled / expired
        order_ref  = payment.get('metadata', {}).get('order_ref', '')

        print(f'[MOLLIE WEBHOOK] payment {payment_id} status={status} order={order_ref}')

        if not order_ref:
            return '', 200

        conn = get_db()
        p    = _p()

        if status == 'paid':
            _exec(conn, f"UPDATE orders SET payment_status='paid' WHERE order_ref={p}", (order_ref,))
            conn.commit()
        elif status in ('failed', 'canceled', 'expired'):
            _exec(conn, f"UPDATE orders SET payment_status={p} WHERE order_ref={p}", (status, order_ref))
            conn.commit()

        conn.close()
        return '', 200

    except Exception as e:
        print(f'[MOLLIE WEBHOOK ERROR] {e}')
        return '', 200


@payments_bp.route('/api/payment/status/<order_ref>', methods=['GET'])
def payment_status(order_ref):
    """Check payment status for an order."""
    conn = get_db()
    p    = _p()
    row  = _exec(conn, f"SELECT payment_status, total FROM orders WHERE order_ref={p}", (order_ref,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'payment_status': row['payment_status'] or 'pending', 'total': row['total']}), 200
