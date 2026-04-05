"""
HUTKO — contact.py
Contact form submissions and newsletter signups.
Optionally sends confirmation emails via Resend.
"""

import os
import resend
from flask import Blueprint, request, jsonify
from database import get_db

contact_bp = Blueprint('contact', __name__)


def send_email(to: str, subject: str, html: str):
    """Send email via Resend. Silently skips if API key not configured."""
    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        print(f"[EMAIL SKIPPED — no RESEND_API_KEY] To: {to} | Subject: {subject}")
        return
    resend.api_key = api_key
    try:
        resend.Emails.send({
            "from":    "HUTKO <noreply@hutko.nl>",
            "to":      [to],
            "subject": subject,
            "html":    html,
        })
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


# ── CONTACT FORM ─────────────────────────────────────────
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
    conn.execute("""
        INSERT INTO messages (name, email, phone, social, topic, title, body)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name, email,
        data.get('phone', ''),
        data.get('social', ''),
        topic, title, body
    ))
    conn.commit()
    conn.close()

    # Notify owner
    owner_email = os.environ.get('OWNER_EMAIL', 'nastiapolimasheva@hutko-kitchen.com')
    send_email(owner_email, f"New message: {title}", f"""
        <h2>New contact form message</h2>
        <p><strong>From:</strong> {name} ({email})</p>
        <p><strong>Phone:</strong> {data.get('phone', '—')}</p>
        <p><strong>Topic:</strong> {topic}</p>
        <p><strong>Title:</strong> {title}</p>
        <hr>
        <p>{body}</p>
    """)

    # Auto-reply to sender
    send_email(email, "We received your message — HUTKO Kitchen", f"""
        <p>Hi {name},</p>
        <p>Thanks for reaching out! We have received your message about <strong>{topic}</strong> and will get back to you within 2 business days.</p>
        <p>Your message: <em>{body[:200]}{'...' if len(body) > 200 else ''}</em></p>
        <br><p>Warm regards,<br>The HUTKO Kitchen team</p>
    """)

    return jsonify({{'message': 'Message received. Thank you!'}}), 201


# ── NEWSLETTER ───────────────────────────────────────────
@contact_bp.route('/api/newsletter', methods=['POST'])
def newsletter():
    data  = request.get_json()
    email = (data.get('email') or '').strip().lower()

    if not email or '@' not in email:
        return jsonify({'error': 'Please provide a valid email address.'}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM newsletter WHERE email=?", (email,)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({'message': 'You are already subscribed!'}), 200

    conn.execute("INSERT INTO newsletter (email) VALUES (?)", (email,))
    conn.commit()
    conn.close()

    send_email(email, "Welcome to the HUTKO newsletter!", """
        <p>You're now subscribed to HUTKO updates!</p>
        <p>Expect Ukrainian food stories, new dish announcements, seasonal recipes and exclusive offers.</p>
        <br><p>З любов'ю / With love,<br>The HUTKO team</p>
    """)

    return jsonify({'message': 'Subscribed successfully!'}), 201
