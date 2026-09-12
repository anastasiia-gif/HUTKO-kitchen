"""
HUTKO — orders.py

v2.0 (2026-09-12) — ORDER LINES ARE NOW VALIDATED SERVER-SIDE.
  Every item must name the product/bundle it refers to (`id`) and the exact option
  the customer chose (`variant` for products, `choice` for bundles). The server
  looks each one up in the live catalogue and REFUSES the order if the choice is
  missing or isn't a real option. The number of options a product has is
  irrelevant — 1, 2 or 50, the rule is identical: if the catalogue offers options,
  the order must name one. That is what stops a flavour being silently lost.

  Prices are re-derived from the catalogue, not trusted from the browser.

  ROLL-OUT SAFETY: an item with no `id` at all is treated as a legacy line from an
  older cached copy of the website and is allowed through with a log warning, so
  deploying this backend BEFORE the new frontend cannot break live checkout.
  Once the frontend is deployed everywhere, set STRICT_ITEMS=1 on Render to
  reject legacy lines too.

v1.1:
  • Area/zone delivery pricing (fee_local / fee_regional, free over threshold).
  • Fixed the admin guard on PUT /orders/<ref>/status.
"""

import json
import os
import random
import string
import time
from flask import Blueprint, request, jsonify, g, redirect
from database import get_db
from auth import optional_token, token_required
from emails import send_order_confirmation, send_order_notification, send_delivery_dispatch
from trello import create_order_card, move_card, add_comment, get_card_by_order_ref
from settings_store import get_float
from validators import (validate_email, validate_phone, validate_name, validate_postcode,
                        validate_house_number, validate_street, validate_city,
                        validate_province, validate_notes)

orders_bp = Blueprint('orders', __name__)

# Reject order lines that don't identify their product. Leave off until the new
# frontend is live everywhere, then set STRICT_ITEMS=1.
STRICT_ITEMS = os.environ.get('STRICT_ITEMS', '') not in ('', '0', 'false', 'False')

PRICE_TOLERANCE = 0.02   # euros — guards against float noise, not against tampering

# Pick-up was withdrawn on 2026-09-12 (manager's decision). The switch is an
# env var rather than deleted code so it can come back without a deploy:
# set PICKUP_ENABLED=1 on Render and put the two options back on checkout.html.
# Orders ALREADY placed for collection are untouched and still export normally.
PICKUP_ENABLED = os.environ.get('PICKUP_ENABLED', '') in ('1', 'true', 'True', 'yes')


# ──────────────────────────────────────────────────────────────────────────
#  Catalogue index — what the customer is allowed to have chosen
# ──────────────────────────────────────────────────────────────────────────
_cat_cache = {'at': 0.0, 'data': None}
_CAT_TTL = 30.0     # seconds; admin edits show up within half a minute


def _catalogue():
    """{'products': {id: product}, 'bundles': {id: bundle}} from the live catalogue."""
    now = time.time()
    if _cat_cache['data'] is not None and (now - _cat_cache['at']) < _CAT_TTL:
        return _cat_cache['data']
    from shop_data import get_products, get_bundles, choice_options
    prods = {p['id']: p for p in get_products(active_only=False)}
    bundles = {}
    for b in get_bundles(active_only=False):
        b = dict(b)
        b['_options'] = b.get('choice_options') or choice_options(b)
        bundles[b['id']] = b
    data = {'products': prods, 'bundles': bundles}
    _cat_cache['data'] = data
    _cat_cache['at'] = now
    return data


def invalidate_catalogue_cache():
    _cat_cache['data'] = None


def _variant_labels(product):
    return [str(v.get('label') or '') for v in (product.get('variants') or [])]


def _variant_price(product, label):
    for v in (product.get('variants') or []):
        if str(v.get('label') or '') == label:
            return float(v.get('price') or 0)
    return None


def _clean(s):
    return str(s if s is not None else '').strip()


def _validate_items(items):
    """Returns (clean_items, error_message).

    clean_items have server-derived prices and a rebuilt display name, so what is
    stored on the order can no longer disagree with what the customer chose.
    """
    if not isinstance(items, list) or not items:
        return None, 'Cart is empty.'

    cat = _catalogue()
    out = []

    for raw in items:
        if not isinstance(raw, dict):
            return None, 'Malformed cart item.'

        item_id = _clean(raw.get('id'))
        kind = _clean(raw.get('kind')).lower()
        variant = _clean(raw.get('variant'))
        choice = _clean(raw.get('choice'))
        name = _clean(raw.get('name'))

        try:
            qty = int(raw.get('qty') or 0)
        except (TypeError, ValueError):
            qty = 0
        if qty < 1:
            return None, f'Invalid quantity for "{name or item_id}".'

        # ── Legacy line from an older cached frontend ────────────────────
        if not item_id:
            if STRICT_ITEMS:
                return None, ('Your saved basket is out of date. Please refresh the page '
                              'and add your items again.')
            print(f'[CHECKOUT] legacy item with no id: {name!r} — passed through unvalidated')
            out.append({'name': name, 'qty': qty, 'price': float(raw.get('price') or 0),
                        'legacy': True})
            continue

        # ── Work out what this line actually is ─────────────────────────
        if not kind:
            kind = 'bundle' if item_id in cat['bundles'] else 'product'

        if kind == 'bundle':
            bundle = cat['bundles'].get(item_id)
            if not bundle:
                return None, f'"{name or item_id}" is no longer available. Please remove it from your basket.'
            options = bundle.get('_options') or []
            # THE RULE: if the catalogue offers options at all, one must be named.
            # No special case for "only one option" — that is how flavours got lost.
            if options and not choice:
                return None, (f'Please choose an option for "{name or bundle.get("name_en") or item_id}" '
                              'before ordering.')
            if options and choice not in options:
                return None, (f'"{choice}" is not an available option for '
                              f'"{name or bundle.get("name_en") or item_id}". Please choose again.')
            price = float(bundle.get('discount_price') or 0)
            display = _clean(name) or _clean(bundle.get('name_en')) or item_id
            if choice and choice not in display:
                display = f'{display} — {choice}'
            out.append({'id': item_id, 'kind': 'bundle', 'name': display,
                        'choice': choice, 'size': _clean(bundle.get('size_label')),
                        'qty': qty, 'price': price})

        else:
            product = cat['products'].get(item_id)
            if not product:
                return None, f'"{name or item_id}" is no longer available. Please remove it from your basket.'
            labels = _variant_labels(product)
            if labels and not variant:
                return None, (f'Please choose an option for "{name or product.get("name_en") or item_id}" '
                              'before ordering.')
            if labels and variant not in labels:
                return None, (f'"{variant}" is not an available option for '
                              f'"{name or product.get("name_en") or item_id}". Please choose again.')
            price = _variant_price(product, variant) if variant else float(product.get('base_price') or 0)
            if price is None:
                price = float(product.get('base_price') or 0)
            display = _clean(name) or _clean(product.get('name_en')) or item_id
            if variant and variant not in display:
                display = f'{display} — {variant}'
            out.append({'id': item_id, 'kind': 'product', 'name': display,
                        'variant': variant, 'qty': qty, 'price': price})

        # Tell the customer if the price moved under them rather than silently
        # charging the new one.
        submitted = raw.get('price')
        if submitted is not None and not out[-1].get('legacy'):
            try:
                if abs(float(submitted) - out[-1]['price']) > PRICE_TOLERANCE:
                    return None, ('Some prices have changed since you added them. '
                                  'Please refresh the page and check your basket.')
            except (TypeError, ValueError):
                pass

    return out, None


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
    delivery_method = (data.get('delivery_method') or 'delivery_local').strip()
    is_pickup = delivery_method.startswith('pickup')

    # Pick-up is withdrawn. A stale cached copy of the site can still offer it,
    # so refuse it here rather than saving an order nobody will collect.
    if is_pickup and not PICKUP_ENABLED:
        return jsonify({'error': 'Collection in person is no longer available — '
                                 'please enter a delivery address.'}), 400

    if not data.get('items'):
        return jsonify({'error': 'Cart is empty.'}), 400

    # ── Every field the kitchen and the driver rely on ──────────────────
    # All of these used to be checked only for "is it non-empty". An address
    # that cannot be delivered to is as useless as an email that bounces, and
    # the driver finds out on the day. The page checks the same things first;
    # this is the copy that a stale cached page or a direct POST cannot skip.
    first, err = validate_name(data.get('first_name'), 'first name')
    if err:
        return jsonify({'error': err}), 400
    last, err = validate_name(data.get('last_name'), 'last name')
    if err:
        return jsonify({'error': err}), 400
    email, err = validate_email(data.get('email'))
    if err:
        return jsonify({'error': err}), 400
    phone, err = validate_phone(data.get('phone'))
    if err:
        return jsonify({'error': err}), 400
    notes, err = validate_notes(data.get('notes'))
    if err:
        return jsonify({'error': err}), 400

    if is_pickup:
        # Only reachable with PICKUP_ENABLED=1.
        street   = str(data.get('street') or '').strip()
        postcode = str(data.get('postcode') or '').strip()
        city     = str(data.get('city') or '').strip()
        province = str(data.get('province') or '').strip()
    else:
        street, err = validate_street(data.get('street'))
        if err:
            return jsonify({'error': err}), 400
        postcode, err = validate_postcode(data.get('postcode'))
        if err:
            return jsonify({'error': err}), 400
        city, err = validate_city(data.get('city'))
        if err:
            return jsonify({'error': err}), 400
        province, err = validate_province(data.get('province'))
        if err:
            return jsonify({'error': err}), 400

    # ── Every line must name a real product and a real choice ───────────
    items, err = _validate_items(data.get('items'))
    if err:
        return jsonify({'error': err}), 400

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

    # Pick-up orders keep their chosen date too — the customer is shown a date
    # picker for pick-up, so throwing the answer away made the slot meaningless.
    delivery_date = data.get('delivery_date', '')

    conn.execute("""
        INSERT INTO orders
          (order_ref, user_id, customer_name, customer_email, customer_phone,
           addr_street, addr_postcode, addr_city, addr_province, delivery_notes,
           delivery_method, delivery_date, items_json, subtotal, delivery_cost, total, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending_payment')
    """, (
        order_ref, user_id, f"{first} {last}",
        email, phone, street, postcode, city, province,
        notes, delivery_method, delivery_date,
        json.dumps(items), subtotal, delivery_cost, total))
    conn.commit()
    conn.close()

    print(f"[ORDER] Created {order_ref} — awaiting payment — {len(items)} line(s)")
    return jsonify({'order_ref': order_ref, 'total': total, 'items': items,
                    'subtotal': subtotal, 'delivery_cost': delivery_cost,
                    'status': 'pending_payment'}), 201


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
        # Unpaid, abandoned checkouts must not eat a delivery slot forever.
        row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM orders WHERE delivery_date = {p} "
            f"AND status NOT IN ('cancelled', 'pending_payment')",
            (date,)).fetchone()
        result[date] = row['cnt'] if row else 0
    conn.close()
    return jsonify(result), 200
