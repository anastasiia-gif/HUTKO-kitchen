"""
HUTKO — admin.py
Token-based admin auth + full admin API.

All /api/admin/* endpoints require Bearer token from /api/admin/login.
This file is designed to be the backend for a future admin UI page.

Available endpoints:
  POST   /api/admin/login               — get admin token
  GET    /api/admin/stats               — dashboard numbers
  GET    /api/admin/orders              — list orders (filterable)
  GET    /api/admin/orders/<ref>        — single order detail
  POST   /api/admin/orders/<ref>/trigger-paid  — test: fire post-payment flow
  PUT    /api/orders/<ref>/status       — update order status (in orders.py)
  GET    /api/admin/export              — download Excel
  GET    /api/admin/messages            — list contact messages
"""

import json, os, io, secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from database import get_db, _use_postgres
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

admin_bp = Blueprint('admin', __name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _p():
    return '%s' if _use_postgres() else '?'


def _exec(conn, sql, params=()):
    if _use_postgres():
        cur = conn.cursor(); cur.execute(sql, params); return cur
    return conn.execute(sql, params)


def _ensure_admin_tokens_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_tokens (
            token      TEXT PRIMARY KEY,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def _admin_token_valid(token: str) -> bool:
    if not token:
        return False
    conn = get_db()
    _ensure_admin_tokens_table(conn)
    row = _exec(conn, f"SELECT token FROM admin_tokens WHERE token = {_p()}", (token,)).fetchone()
    conn.close()
    return row is not None


# Tokens also kept as a set for in-process checks (orders.py uses this)
_admin_tokens: set = set()


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
        if not _admin_token_valid(token):
            return jsonify({'error': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated


# ── Auth ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    data     = request.get_json()
    password = data.get('password', '')
    admin_pw = os.environ.get('ADMIN_PASSWORD', '')
    if not admin_pw:
        return jsonify({'error': 'Admin access is not configured.'}), 503
    if password != admin_pw:
        return jsonify({'error': 'Wrong password.'}), 401
    token = secrets.token_hex(32)
    conn  = get_db()
    _ensure_admin_tokens_table(conn)
    _exec(conn, f"INSERT INTO admin_tokens (token) VALUES ({_p()})", (token,))
    conn.commit(); conn.close()
    _admin_tokens.add(token)
    return jsonify({'token': token}), 200


# ── Dashboard stats ───────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/stats', methods=['GET'])
@admin_required
def stats():
    conn = get_db()
    p    = _p()
    data = {
        'total_orders':    _exec(conn, "SELECT COUNT(*) FROM orders").fetchone()[0],
        'total_revenue':   _exec(conn, "SELECT COALESCE(SUM(total),0) FROM orders WHERE payment_status='paid'").fetchone()[0],
        'pending_orders':  _exec(conn, f"SELECT COUNT(*) FROM orders WHERE status={p}", ('confirmed',)).fetchone()[0],
        'cooking_orders':  _exec(conn, f"SELECT COUNT(*) FROM orders WHERE status={p}", ('cooking',)).fetchone()[0],
        'out_for_delivery':_exec(conn, f"SELECT COUNT(*) FROM orders WHERE status={p}", ('delivery',)).fetchone()[0],
        'total_users':     _exec(conn, "SELECT COUNT(*) FROM users").fetchone()[0],
        'newsletter_subs': _exec(conn, "SELECT COUNT(*) FROM newsletter").fetchone()[0],
        'unread_messages': _exec(conn, "SELECT COUNT(*) FROM messages").fetchone()[0],
        'abandoned_today': _exec(conn, f"SELECT COUNT(*) FROM orders WHERE payment_status={p} AND DATE(created_at)=DATE('now')", ('expired',)).fetchone()[0],
    }
    conn.close()
    return jsonify(data), 200


# ── Orders list ───────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/orders', methods=['GET'])
@admin_required
def list_orders():
    """
    Query params (all optional):
      status         — filter by status (confirmed, cooking, delivery, etc.)
      payment_status — filter by payment_status (paid, pending, expired)
      search         — search by order_ref, customer name or email
      page           — page number (default 1)
      per_page       — results per page (default 25, max 100)
    """
    conn     = get_db()
    status   = request.args.get('status', '')
    pay_st   = request.args.get('payment_status', '')
    search   = request.args.get('search', '').strip()
    page     = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(1, int(request.args.get('per_page', 25))))
    offset   = (page - 1) * per_page
    p        = _p()

    where, params = [], []
    if status:
        where.append(f"status = {p}"); params.append(status)
    if pay_st:
        where.append(f"payment_status = {p}"); params.append(pay_st)
    if search:
        like = f"%{search}%"
        where.append(f"(order_ref LIKE {p} OR customer_name LIKE {p} OR customer_email LIKE {p})")
        params += [like, like, like]

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    total     = _exec(conn, f"SELECT COUNT(*) FROM orders {where_sql}", params).fetchone()[0]
    rows      = _exec(conn, f"""
        SELECT order_ref, customer_name, customer_email, customer_phone,
               delivery_method, delivery_date, subtotal, delivery_cost, total,
               status, payment_status, created_at, items_json, trello_card_id,
               addr_street, addr_postcode, addr_city
        FROM orders {where_sql}
        ORDER BY created_at DESC
        LIMIT {per_page} OFFSET {offset}
    """, params).fetchall()
    conn.close()

    orders = []
    for r in rows:
        o = dict(r)
        o['items'] = json.loads(o.pop('items_json'))
        orders.append(o)

    return jsonify({
        'orders':   orders,
        'total':    total,
        'page':     page,
        'per_page': per_page,
        'pages':    (total + per_page - 1) // per_page,
    }), 200


# ── Single order detail ───────────────────────────────────────────────────────

@admin_bp.route('/api/admin/orders/<ref>', methods=['GET'])
@admin_required
def get_order(ref):
    conn = get_db()
    row  = _exec(conn, f"SELECT * FROM orders WHERE order_ref = {_p()}", (ref,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Order not found'}), 404
    o = dict(row)
    o['items'] = json.loads(o.pop('items_json'))
    return jsonify({'order': o}), 200


# ── Test: manually fire post-payment flow ─────────────────────────────────────

@admin_bp.route('/api/admin/orders/<ref>/trigger-paid', methods=['POST'])
@admin_required
def trigger_paid(ref):
    """
    Manually fires the full post-payment flow (Trello card + emails)
    for an existing order — without going through Stripe.

    Use this to:
      - Test Trello + email integration without a real payment
      - Re-trigger if the webhook was missed (e.g. Render was sleeping)
      - Test from a future admin UI with a single button click

    Usage:
      POST /api/admin/orders/HK-XXXX/trigger-paid
      Authorization: Bearer <admin_token>
    """
    from payments import _process_paid_order, _exec as _pexec, _p as _pp

    conn = get_db()
    row  = _exec(conn, f"SELECT order_ref, payment_status FROM orders WHERE order_ref = {_p()}", (ref,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': f'Order {ref} not found'}), 404

    # Mark as paid in DB
    conn2 = get_db()
    _exec(conn2, f"UPDATE orders SET payment_status='paid', status='confirmed' WHERE order_ref = {_p()}", (ref,))
    conn2.commit(); conn2.close()

    # Fire in background so this request returns instantly
    import threading
    threading.Thread(target=_process_paid_order, args=(ref,), daemon=True).start()

    return jsonify({
        'ok': True,
        'message': f'Post-payment flow triggered for {ref}. Check Trello and email in ~5 seconds.'
    }), 200


# ── Messages ──────────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/messages', methods=['GET'])
@admin_required
def list_messages():
    conn = get_db()
    rows = _exec(conn, "SELECT * FROM messages ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify({'messages': [dict(r) for r in rows]}), 200


# ── Excel export ──────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/export', methods=['GET'])
@admin_required
def export_excel():
    conn = get_db()
    wb   = Workbook()

    def header(ws, cols, color="1a2356"):
        ws.append(cols)
        for cell in ws[ws.max_row]:
            cell.font      = Font(bold=True, color="FFFFFF", name="Calibri")
            cell.fill      = PatternFill("solid", fgColor=color)
            cell.alignment = Alignment(horizontal="center")

    ws1 = wb.active; ws1.title = "Orders"
    header(ws1, ["Order Ref","Date","Customer","Email","Phone","Address","City",
                 "Method","Items","Subtotal","Delivery","Total","Status","Payment","Notes"])
    for r in _exec(conn, "SELECT * FROM orders ORDER BY created_at DESC").fetchall():
        items_str = " | ".join(f"{i['name']} x{i['qty']}" for i in json.loads(r['items_json']))
        ws1.append([r['order_ref'], r['created_at'], r['customer_name'], r['customer_email'],
                    r['customer_phone'], f"{r['addr_street']}, {r['addr_postcode']}",
                    r['addr_city'], r['delivery_method'], items_str,
                    r['subtotal'], r['delivery_cost'], r['total'],
                    r['status'], r['payment_status'] or 'pending', r['delivery_notes']])

    ws2 = wb.create_sheet("Users")
    header(ws2, ["ID","Name","Email","Phone","Street","Postcode","City","Province","Registered"], "0F6E56")
    for r in _exec(conn, "SELECT * FROM users ORDER BY created_at DESC").fetchall():
        ws2.append([r['id'], r['name'], r['email'], r['phone'],
                    r['addr_street'], r['addr_postcode'], r['addr_city'], r['addr_province'], r['created_at']])

    ws3 = wb.create_sheet("Messages")
    header(ws3, ["ID","Date","Name","Email","Topic","Title","Message"])
    for r in _exec(conn, "SELECT * FROM messages ORDER BY created_at DESC").fetchall():
        ws3.append([r['id'], r['created_at'], r['name'], r['email'], r['topic'], r['title'], r['body']])

    ws4 = wb.create_sheet("Newsletter")
    header(ws4, ["ID","Email","Subscribed At"], "E8622A")
    for r in _exec(conn, "SELECT * FROM newsletter ORDER BY created_at DESC").fetchall():
        ws4.append([r['id'], r['email'], r['created_at']])

    conn.close()
    for ws in wb.worksheets:
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(
                max(len(str(c.value or '')) for c in col) + 4, 60)

    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return send_file(buf, as_attachment=True,
        download_name=f"hutko_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
