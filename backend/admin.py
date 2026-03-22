"""
HUTKO — admin.py
Token-based admin auth.
"""

import json, os, io, secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, g
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from database import get_db

admin_bp = Blueprint('admin', __name__)

_admin_tokens = {}

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
        if token not in _admin_tokens:
            return jsonify({'error': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    data     = request.get_json()
    password = data.get('password', '')
    admin_pw = os.environ.get('ADMIN_PASSWORD', 'hutko-admin-2025')
    if password != admin_pw:
        return jsonify({'error': 'Wrong password.'}), 401
    token = secrets.token_hex(32)
    _admin_tokens[token] = True
    return jsonify({'token': token}), 200


@admin_bp.route('/api/admin/stats', methods=['GET'])
@admin_required
def stats():
    conn = get_db()
    data = {
        'total_orders':    conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        'total_revenue':   conn.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status != 'cancelled'").fetchone()[0],
        'total_users':     conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        'newsletter_subs': conn.execute("SELECT COUNT(*) FROM newsletter").fetchone()[0],
        'unread_messages': conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        'pending_orders':  conn.execute("SELECT COUNT(*) FROM orders WHERE status='confirmed'").fetchone()[0],
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
    for r in conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall():
        items_str = " | ".join(f"{i['name']} x{i['qty']}" for i in json.loads(r['items_json']))
        ws1.append([r['order_ref'], r['created_at'], r['customer_name'], r['customer_email'],
                    r['customer_phone'], f"{r['addr_street']}, {r['addr_postcode']}",
                    r['addr_city'], r['addr_province'], r['delivery_method'], items_str,
                    r['subtotal'], r['delivery_cost'], r['total'], r['status'], r['delivery_notes']])

    ws2 = wb.create_sheet("Users")
    header(ws2, ["ID","Name","Email","Phone","Street","Postcode","City","Province","Registered"], "E8622A")
    for r in conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall():
        ws2.append([r['id'], r['name'], r['email'], r['phone'],
                    r['addr_street'], r['addr_postcode'], r['addr_city'], r['addr_province'], r['created_at']])

    ws3 = wb.create_sheet("Messages")
    header(ws3, ["ID","Date","Name","Email","Topic","Title","Message"])
    for r in conn.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall():
        ws3.append([r['id'], r['created_at'], r['name'], r['email'], r['topic'], r['title'], r['body']])

    ws4 = wb.create_sheet("Newsletter")
    header(ws4, ["ID","Email","Subscribed At"], "E8622A")
    for r in conn.execute("SELECT * FROM newsletter ORDER BY created_at DESC").fetchall():
        ws4.append([r['id'], r['email'], r['created_at']])

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
