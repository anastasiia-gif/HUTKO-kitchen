"""
HUTKO — contact.py
Contact form submissions and newsletter signups.
"""

import os
from flask import Blueprint, request, jsonify
from database import get_db, _placeholder, _use_postgres
from emails import send_contact_reply, send_contact_notification, send_email

contact_bp = Blueprint('contact', __name__)


def _exec(conn, sql, params=()):
    if _use_postgres():
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur
    else:
        return conn.execute(sql, params)


def _p():
    return _placeholder()


@contact_bp.route('/api/contact', methods=['POST'])
def contact():
    data  = request.get_json()
    name  = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    topic = (data.get('topic') or '').strip()
    title = (data.get('title') or '').strip()
    body  = (data.get('body') or '').strip()

    if not name or not email or not topic or not title or not body:
        return jsonify({'error': 'All required fields must be filled in.'}), 400

    conn = get_db()
    _exec(conn, f"""
        INSERT INTO messages (name, email, phone, social, topic, title, body)
        VALUES ({_p()}, {_p()}, {_p()}, {_p()}, {_p()}, {_p()}, {_p()})
    """, (name, email, data.get('phone', ''), data.get('social', ''), topic, title, body))
    conn.commit()
    conn.close()

    try:
        send_contact_reply(name, email, topic, body)
        send_contact_notification(name, email, data.get('phone', ''), topic, title, body)
    except Exception as e:
        print(f"[CONTACT EMAIL ERROR] {e}")

    return jsonify({'message': 'Message received. Thank you!'}), 201


@contact_bp.route('/api/newsletter', methods=['POST'])
def newsletter():
    data  = request.get_json()
    email = (data.get('email') or '').strip().lower()

    if not email or '@' not in email:
        return jsonify({'error': 'Please provide a valid email address.'}), 400

    conn = get_db()
    existing = _exec(conn, f"SELECT id FROM newsletter WHERE email={_p()}", (email,)).fetchone()

    if existing:
        conn.close()
        return jsonify({'message': 'You are already subscribed!'}), 200

    _exec(conn, f"INSERT INTO newsletter (email) VALUES ({_p()})", (email,))
    conn.commit()
    conn.close()

    try:
        send_email(email, "Welcome to the HUTKO Kitchen newsletter! 🇺🇦", """
            <!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#f4f0e8;padding:40px 20px;">
            <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:16px;padding:40px;">
            <h2 style="color:#1B3FCE;margin:0 0 16px;">You're subscribed! 🎉</h2>
            <p style="color:#666;line-height:1.7;">
                Expect Ukrainian food stories, new dish announcements, seasonal recipes and exclusive offers.
            </p>
            <p style="color:#999;font-size:13px;margin-top:24px;">З любов'ю / With love,<br><strong style="color:#111;">The HUTKO Kitchen team</strong></p>
            </div></body></html>
        """)
    except Exception as e:
        print(f"[NEWSLETTER EMAIL ERROR] {e}")

    return jsonify({'message': 'Subscribed successfully!'}), 201
