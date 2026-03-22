"""
HUTKO — admin.py
Admin-only endpoints.
/api/admin/export  →  downloads a fresh Excel workbook with 4 sheets:
  Orders | Users | Messages | Newsletter
"""

import json
import os
import io
from datetime import datetime
from flask import Blueprint, jsonify, session, send_file
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from database import get_db

admin_bp = Blueprint('admin', __name__)

NAVY   = "1a2356"
ORANGE = "E8622A"
CREAM  = "F2EDE4"


def admin_required():
    """Returns True if the current session is an admin."""
    return session.get('is_admin') is True


def style_header_row(ws, headers: list, fill_color: str = NAVY):
    """Write and style a header row."""
    ws.append(headers)
    for cell in ws[ws.max_row]:
        cell.font      = Font(bold=True, color="FFFFFF", name="Calibri")
        cell.fill      = PatternFill("solid", fgColor=fill_color)
        cell.alignment = Alignment(horizontal="center", vertical="center")


# ── ADMIN LOGIN (simple — replace with proper auth in production) ──
@admin_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    from flask import request
    data     = request.get_json()
    password = data.get('password', '')
    admin_pw = os.environ.get('ADMIN_PASSWORD', 'hutko-admin-2025')
    if password != admin_pw:
        return jsonify({'error': 'Wrong password.'}), 401
    session['is_admin'] = True
    return jsonify({'message': 'Admin access granted.'}), 200


# ── EXCEL EXPORT ──────────────────────────────────────────
@admin_bp.route('/api/admin/export', methods=['GET'])
def export_excel():
    if not admin_required():
        return jsonify({'error': 'Admin access required.'}), 403

    conn = get_db()
    wb   = Workbook()

    # ── Sheet 1: Orders ──────────────────────────────
    ws_orders = wb.active
    ws_orders.title = "Orders"
    style_header_row(ws_orders, [
        "Order Ref", "Date", "Customer", "Email", "Phone",
        "Address", "City", "Province", "Delivery Method",
        "Items", "Subtotal (€)", "Delivery (€)", "Total (€)", "Status", "Notes"
    ], NAVY)

    for r in conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall():
        items = json.loads(r['items_json'])
        items_str = " | ".join(f"{i['name']} ×{i['qty']}" for i in items)
        address = f"{r['addr_street']}, {r['addr_postcode']}"
        ws_orders.append([
            r['order_ref'],
            r['created_at'],
            r['customer_name'],
            r['customer_email'],
            r['customer_phone'],
            address,
            r['addr_city'],
            r['addr_province'],
            r['delivery_method'],
            items_str,
            r['subtotal'],
            r['delivery_cost'],
            r['total'],
            r['status'],
            r['delivery_notes'],
        ])

    # ── Sheet 2: Users ───────────────────────────────
    ws_users = wb.create_sheet("Users")
    style_header_row(ws_users, [
        "ID", "Name", "Email", "Phone",
        "Street", "Postcode", "City", "Province", "Registered"
    ], ORANGE)

    for r in conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall():
        ws_users.append([
            r['id'], r['name'], r['email'], r['phone'],
            r['addr_street'], r['addr_postcode'], r['addr_city'], r['addr_province'],
            r['created_at'],
        ])

    # ── Sheet 3: Messages ────────────────────────────
    ws_msg = wb.create_sheet("Messages")
    style_header_row(ws_msg, [
        "ID", "Date", "Name", "Email", "Phone", "Social", "Topic", "Title", "Message"
    ], NAVY)

    for r in conn.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall():
        ws_msg.append([
            r['id'], r['created_at'], r['name'], r['email'],
            r['phone'], r['social'], r['topic'], r['title'], r['body'],
        ])

    # ── Sheet 4: Newsletter ──────────────────────────
    ws_nl = wb.create_sheet("Newsletter")
    style_header_row(ws_nl, ["ID", "Email", "Subscribed At"], ORANGE)

    for r in conn.execute("SELECT * FROM newsletter ORDER BY created_at DESC").fetchall():
        ws_nl.append([r['id'], r['email'], r['created_at']])

    conn.close()

    # ── Auto-size columns ────────────────────────────
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = max((len(str(c.value or '')) for c in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)

    # ── Stream as download ───────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"hutko_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ── QUICK STATS ───────────────────────────────────────────
@admin_bp.route('/api/admin/stats', methods=['GET'])
def stats():
    if not admin_required():
        return jsonify({'error': 'Admin access required.'}), 403
    conn = get_db()
    data = {
        'total_orders':     conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        'total_revenue':    conn.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status != 'cancelled'").fetchone()[0],
        'total_users':      conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        'newsletter_subs':  conn.execute("SELECT COUNT(*) FROM newsletter").fetchone()[0],
        'unread_messages':  conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        'pending_orders':   conn.execute("SELECT COUNT(*) FROM orders WHERE status='confirmed'").fetchone()[0],
    }
    conn.close()
    return jsonify(data), 200
