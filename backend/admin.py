"""
HUTKO — admin.py
Token-based admin auth. Works with SQLite and PostgreSQL.
"""

import json, os, io, secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from database import get_db, _placeholder, _use_postgres

admin_bp = Blueprint('admin', __name__)


def _exec(conn, sql, params=()):
    if _use_postgres():
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur
    else:
        return conn.execute(sql, params)


def _p():
    return _placeholder()


def _ensure_admin_tokens_table(conn):
    from database import _autoincrement, _datetime_default
    ai = _autoincrement()
    dt = _datetime_default()
    _exec(conn, f"""
        CREATE TABLE IF NOT EXISTS admin_tokens (
            id         {ai},
            token      TEXT NOT NULL UNIQUE,
            created_at TEXT {dt}
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


# Expose for orders.py import
def _admin_tokens():
    pass  # kept for compatibility — use _admin_token_valid instead


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
        if not _admin_token_valid(token):
            return jsonify({'error': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated


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
    conn = get_db()
    _ensure_admin_tokens_table(conn)
    _exec(conn, f"INSERT INTO admin_tokens (token) VALUES ({_p()})", (token,))
    conn.commit()
    conn.close()
    return jsonify({'token': token}), 200


@admin_bp.route('/api/admin/stats', methods=['GET'])
@admin_required
def stats():
    conn = get_db()
    def count(sql):
        row = _exec(conn, sql).fetchone()
        return list(row.values())[0] if isinstance(row, dict) else row[0]
    data = {
        'total_orders':    count("SELECT COUNT(*) FROM orders"),
        'total_revenue':   count("SELECT COALESCE(SUM(total),0) FROM orders WHERE status != 'cancelled'"),
        'total_users':     count("SELECT COUNT(*) FROM users"),
        'newsletter_subs': count("SELECT COUNT(*) FROM newsletter"),
        'unread_messages': count("SELECT COUNT(*) FROM messages"),
        'pending_orders':  count("SELECT COUNT(*) FROM orders WHERE status='confirmed'"),
    }
    conn.close()
    return jsonify(data), 200


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

    ws1 = wb.active
    ws1.title = "Orders"
    header(ws1, ["Order Ref","Date","Customer","Email","Phone","Address","City","Province","Method","Items","Subtotal","Delivery","Total","Status","Notes"])
    for r in _exec(conn, "SELECT * FROM orders ORDER BY created_at DESC").fetchall():
        items_str = " | ".join(f"{i['name']} x{i['qty']}" for i in json.loads(r['items_json']))
        ws1.append([r['order_ref'], str(r['created_at']), r['customer_name'], r['customer_email'],
                    r['customer_phone'], f"{r['addr_street']}, {r['addr_postcode']}",
                    r['addr_city'], r['addr_province'], r['delivery_method'], items_str,
                    r['subtotal'], r['delivery_cost'], r['total'], r['status'], r['delivery_notes']])

    ws2 = wb.create_sheet("Users")
    header(ws2, ["ID","Name","Email","Phone","Street","Postcode","City","Province","Registered"], "E8622A")
    for r in _exec(conn, "SELECT * FROM users ORDER BY created_at DESC").fetchall():
        ws2.append([r['id'], r['name'], r['email'], r['phone'],
                    r['addr_street'], r['addr_postcode'], r['addr_city'], r['addr_province'], str(r['created_at'])])

    ws3 = wb.create_sheet("Messages")
    header(ws3, ["ID","Date","Name","Email","Topic","Title","Message"])
    for r in _exec(conn, "SELECT * FROM messages ORDER BY created_at DESC").fetchall():
        ws3.append([r['id'], str(r['created_at']), r['name'], r['email'], r['topic'], r['title'], r['body']])

    ws4 = wb.create_sheet("Newsletter")
    header(ws4, ["ID","Email","Subscribed At"], "E8622A")
    for r in _exec(conn, "SELECT * FROM newsletter ORDER BY created_at DESC").fetchall():
        ws4.append([r['id'], r['email'], str(r['created_at'])])

    conn.close()
    for ws in wb.worksheets:
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(
                max(len(str(c.value or '')) for c in col) + 4, 60)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True,
        download_name=f"hutko_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
