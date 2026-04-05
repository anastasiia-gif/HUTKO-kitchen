"""
HUTKO — trello_webhook.py
Handles Trello webhooks — when cards move between lists,
sends appropriate emails to customers.
"""

import os
import json
from flask import Blueprint, request, jsonify
from database import get_db
from emails import send_email, _base_template
from trello import add_comment

webhook_bp = Blueprint('webhook', __name__)

BRAND_BLUE   = '#1B3FCE'
BRAND_ORANGE = '#E84B22'
SITE_URL     = os.environ.get('FRONTEND_URL', 'https://hutko-kitchen.com')

# Trello List IDs → internal status names
LIST_STATUS = {
    '69d29b50f81815133e083e42': 'new_orders',
    '69d29b5c4d746c0f0a4a201f': 'confirmed',
    '69d29b6e70155674b2fe1157': 'in_storage',
    '69d29b792569d8d839a78dc3': 'out_for_delivery',
    '69d29b87e98a49718dddd4a5': 'delivered',
    '69d29b94c21f6521a96e613a': 'cancelled',
    '69d29b9df9e5bae1a52fa0e0': 'ok_confirmed',
}


def get_order_by_card(card_name: str):
    """Extract order ref from card name like '#HK-XXXXX — Name — €XX'"""
    try:
        ref = card_name.split('—')[0].strip().replace('#', '')
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM orders WHERE order_ref=?", (ref,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[WEBHOOK] get_order_by_card error: {e}")
        return None


def send_cooking_notification(order: dict):
    """Email when order moves to Confirmed & Cooking."""
    first = order['customer_name'].split()[0]
    content = f"""
      <h1 style="margin:0 0 8px;font-size:26px;font-weight:900;color:#111;">
        Your order is being prepared! 👩‍🍳
      </h1>
      <p style="margin:0 0 24px;font-size:15px;color:#666;line-height:1.6;">
        Hi {first}! Great news — order <strong style="color:{BRAND_BLUE};">#{order['order_ref']}</strong>
        has been confirmed and our kitchen is preparing your food right now.
      </p>

      <div style="background:{BRAND_BLUE};border-radius:12px;padding:20px 24px;margin:0 0 24px;">
        <p style="margin:0 0 8px;font-size:13px;font-weight:700;color:rgba(255,255,255,0.6);letter-spacing:1.5px;text-transform:uppercase;">Status update</p>
        <p style="margin:0 0 6px;font-size:14px;color:#fff;">✅ &nbsp;Order confirmed</p>
        <p style="margin:0 0 6px;font-size:14px;color:#fff;">👩‍🍳 &nbsp;Kitchen is preparing your food</p>
        <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.5);">❄️ &nbsp;Freezing & packing — coming soon</p>
        <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.5);">🚚 &nbsp;Delivery — coming soon</p>
      </div>

      <p style="margin:0 0 24px;font-size:14px;color:#666;line-height:1.6;">
        Everything is made fresh in small batches. We'll send you another update when your order is on its way!
      </p>

      <table cellpadding="0" cellspacing="0" width="100%">
        <tr><td align="center">
          <a href="{SITE_URL}/account.html#orders"
             style="display:inline-block;background:{BRAND_ORANGE};color:#fff;
                    text-decoration:none;font-size:14px;font-weight:700;
                    padding:13px 32px;border-radius:100px;">
            Track my order →
          </a>
        </td></tr>
      </table>
    """
    send_email(
        order['customer_email'],
        f"Your order #{order['order_ref']} is being prepared! 👩‍🍳",
        _base_template(content, f"Order #{order['order_ref']} confirmed — kitchen is preparing your food!")
    )


def send_delivery_notification(order: dict):
    """Email when order moves to Out for Delivery."""
    first = order['customer_name'].split()[0]
    driver_email = os.environ.get('DRIVER_EMAIL', os.environ.get('OWNER_EMAIL', ''))

    content = f"""
      <h1 style="margin:0 0 8px;font-size:26px;font-weight:900;color:#111;">
        Your order is on its way! 🚚
      </h1>
      <p style="margin:0 0 24px;font-size:15px;color:#666;line-height:1.6;">
        Hi {first}! Order <strong style="color:{BRAND_BLUE};">#{order['order_ref']}</strong>
        has left our kitchen and is on its way to you.
      </p>

      <div style="background:{BRAND_BLUE};border-radius:12px;padding:20px 24px;margin:0 0 24px;">
        <p style="margin:0 0 8px;font-size:13px;font-weight:700;color:rgba(255,255,255,0.6);letter-spacing:1.5px;text-transform:uppercase;">Status update</p>
        <p style="margin:0 0 6px;font-size:14px;color:#fff;">✅ &nbsp;Order confirmed</p>
        <p style="margin:0 0 6px;font-size:14px;color:#fff;">✅ &nbsp;Prepared & frozen</p>
        <p style="margin:0 0 6px;font-size:14px;color:{BRAND_ORANGE};font-weight:700;">🚚 &nbsp;Out for delivery — TODAY!</p>
        <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.5);">✅ &nbsp;Delivered — soon</p>
      </div>

      <div style="border:1px solid #e8e2d5;border-radius:12px;padding:18px 24px;margin:0 0 24px;">
        <p style="margin:0 0 8px;font-size:13px;font-weight:700;color:#666;letter-spacing:1.5px;text-transform:uppercase;">Delivery address</p>
        <p style="margin:0;font-size:14px;color:#333;line-height:1.6;">
          {order['customer_name']}<br>
          {order['addr_street']}, {order['addr_postcode']} {order['addr_city']}
        </p>
      </div>

      <p style="margin:0 0 24px;font-size:14px;color:#666;line-height:1.6;">
        Please make sure someone is available to receive the package. It arrives in insulated packaging to keep everything frozen.
      </p>

      <table cellpadding="0" cellspacing="0" width="100%">
        <tr><td align="center">
          <a href="{SITE_URL}/confirm-delivery.html?ref={order['order_ref']}"
             style="display:inline-block;background:{BRAND_ORANGE};color:#fff;
                    text-decoration:none;font-size:14px;font-weight:700;
                    padding:13px 32px;border-radius:100px;">
            Confirm delivery when received →
          </a>
        </td></tr>
      </table>
    """
    send_email(
        order['customer_email'],
        f"Your order #{order['order_ref']} is on its way! 🚚",
        _base_template(content, f"Order #{order['order_ref']} is out for delivery today!")
    )

    # Also notify driver
    if driver_email:
        driver_content = f"""
          <h2 style="margin:0 0 16px;color:#111;">🚚 Delivery assignment: #{order['order_ref']}</h2>
          <div style="background:#f4f0e8;border-radius:12px;padding:18px 24px;margin:0 0 20px;">
            <p style="margin:0 0 6px;font-size:14px;"><strong>Customer:</strong> {order['customer_name']}</p>
            <p style="margin:0 0 6px;font-size:14px;"><strong>Phone:</strong> {order['customer_phone']}</p>
            <p style="margin:0 0 6px;font-size:14px;"><strong>Address:</strong> {order['addr_street']}, {order['addr_postcode']} {order['addr_city']}</p>
            {'<p style="margin:0;font-size:14px;"><strong>Note:</strong> ' + order.get('delivery_notes','') + '</p>' if order.get('delivery_notes') else ''}
          </div>
          <p style="font-size:14px;color:#666;">Total order value: <strong>€{order['total']}</strong></p>
        """
        send_email(
            driver_email,
            f"🚚 Delivery: #{order['order_ref']} — {order['customer_name']}",
            _base_template(driver_content)
        )


def send_delivered_notification(order: dict):
    """Email when order moves to Delivered — ask for confirmation."""
    first = order['customer_name'].split()[0]
    confirm_url = f"{SITE_URL}/confirm-delivery.html?ref={order['order_ref']}"

    content = f"""
      <h1 style="margin:0 0 8px;font-size:26px;font-weight:900;color:#111;">
        Did you receive your order? 📦
      </h1>
      <p style="margin:0 0 24px;font-size:15px;color:#666;line-height:1.6;">
        Hi {first}! We believe order <strong style="color:{BRAND_BLUE};">#{order['order_ref']}</strong>
        has been delivered. Please confirm receipt and let us know how everything was!
      </p>

      <div style="background:{BRAND_BLUE};border-radius:12px;padding:20px 24px;margin:0 0 28px;">
        <p style="margin:0 0 6px;font-size:14px;color:#fff;">✅ &nbsp;Order confirmed</p>
        <p style="margin:0 0 6px;font-size:14px;color:#fff;">✅ &nbsp;Prepared & frozen</p>
        <p style="margin:0 0 6px;font-size:14px;color:#fff;">✅ &nbsp;Delivered</p>
        <p style="margin:0;font-size:14px;color:{BRAND_ORANGE};font-weight:700;">⭐ &nbsp;Please confirm & leave a review!</p>
      </div>

      <table cellpadding="0" cellspacing="0" width="100%">
        <tr><td align="center" style="padding-bottom:12px;">
          <a href="{confirm_url}"
             style="display:inline-block;background:{BRAND_ORANGE};color:#fff;
                    text-decoration:none;font-size:15px;font-weight:700;
                    padding:15px 36px;border-radius:100px;">
            ✅ Confirm delivery & leave review →
          </a>
        </td></tr>
        <tr><td align="center">
          <p style="font-size:12px;color:#999;">
            Or visit: <a href="{confirm_url}" style="color:{BRAND_BLUE};">{confirm_url}</a>
          </p>
        </td></tr>
      </table>

      <p style="margin:24px 0 0;font-size:14px;color:#999;text-align:center;">
        З любов'ю / With love,<br>
        <strong style="color:#111;">The HUTKO Kitchen team</strong> 🇺🇦
      </p>
    """
    send_email(
        order['customer_email'],
        f"Did you receive order #{order['order_ref']}? Please confirm! ⭐",
        _base_template(content, f"Confirm delivery of order #{order['order_ref']} and leave a review!")
    )


def send_cancelled_notification(order: dict):
    """Email when order is cancelled."""
    first = order['customer_name'].split()[0]
    content = f"""
      <h1 style="margin:0 0 8px;font-size:26px;font-weight:900;color:#111;">
        Order cancelled
      </h1>
      <p style="margin:0 0 24px;font-size:15px;color:#666;line-height:1.6;">
        Hi {first}, order <strong>#{order['order_ref']}</strong> has been cancelled.
        If you have any questions, please contact us.
      </p>
      <table cellpadding="0" cellspacing="0" width="100%">
        <tr><td align="center">
          <a href="{SITE_URL}/contact.html"
             style="display:inline-block;background:{BRAND_BLUE};color:#fff;
                    text-decoration:none;font-size:14px;font-weight:700;
                    padding:13px 32px;border-radius:100px;">
            Contact us →
          </a>
        </td></tr>
      </table>
    """
    send_email(
        order['customer_email'],
        f"Order #{order['order_ref']} cancelled",
        _base_template(content)
    )


# ── TRELLO WEBHOOK ENDPOINT ──────────────────────────────
@webhook_bp.route('/api/trello-webhook', methods=['HEAD', 'GET', 'POST'])
def trello_webhook():
    # Trello sends HEAD request to verify webhook — must return 200
    if request.method in ('HEAD', 'GET'):
        return '', 200

    try:
        data   = request.get_json(force=True, silent=True) or {}
        action = data.get('action', {})

        # Only care about card moves
        if action.get('type') != 'updateCard':
            return '', 200

        after  = action.get('data', {}).get('listAfter', {})
        card   = action.get('data', {}).get('card', {})

        if not after or not card:
            return '', 200

        list_id   = after.get('id', '')
        card_name = card.get('name', '')
        status    = LIST_STATUS.get(list_id)

        print(f"[WEBHOOK] Card '{card_name}' moved to '{after.get('name')}' (status: {status})")

        if not status:
            return '', 200

        # Find order
        order = get_order_by_card(card_name)
        if not order:
            print(f"[WEBHOOK] Order not found for card: {card_name}")
            return '', 200

        # Update order status in DB
        conn = get_db()
        conn.execute(
            "UPDATE orders SET status=? WHERE order_ref=?",
            (status, order['order_ref'])
        )
        conn.commit()
        conn.close()

        # Send appropriate email
        if status == 'confirmed':
            send_cooking_notification(order)
            print(f"[WEBHOOK] Cooking notification sent for #{order['order_ref']}")

        elif status == 'out_for_delivery':
            send_delivery_notification(order)
            print(f"[WEBHOOK] Delivery notification sent for #{order['order_ref']}")

        elif status == 'delivered':
            send_delivered_notification(order)
            print(f"[WEBHOOK] Delivered notification sent for #{order['order_ref']}")

        elif status == 'cancelled':
            send_cancelled_notification(order)
            print(f"[WEBHOOK] Cancellation notification sent for #{order['order_ref']}")

        return '', 200

    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
        return '', 200  # Always return 200 to Trello


# ── REGISTER WEBHOOK (call once) ────────────────────────
@webhook_bp.route('/api/trello-webhook/register', methods=['POST'])
def register_webhook():
    """
    Call this once to register the Trello webhook.
    POST /api/trello-webhook/register
    """
    import requests as req

    api_key = os.environ.get('TRELLO_API_KEY')
    token   = os.environ.get('TRELLO_TOKEN')
    board_id = '69c83bc12f4c3402415b14d3'

    backend_url = os.environ.get('BACKEND_URL', 'https://hutko-kitchen.onrender.com')
    callback_url = f"{backend_url}/api/trello-webhook"

    try:
        res = req.post(
            'https://api.trello.com/1/webhooks',
            params={'key': api_key, 'token': token},
            json={
                'callbackURL': callback_url,
                'idModel':     board_id,
                'description': 'HUTKO Kitchen order tracking',
            },
            timeout=10
        )
        if res.ok:
            return jsonify({'message': 'Webhook registered!', 'data': res.json()}), 200
        else:
            return jsonify({'error': res.text}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
