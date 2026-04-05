"""
HUTKO — emails.py
Beautiful HTML email templates for all transactional emails.
Sends via Resend. Silently skips if RESEND_API_KEY not set.
"""

import os
import resend

BRAND_BLUE   = '#1B3FCE'
BRAND_ORANGE = '#E84B22'
BRAND_CREAM  = '#E8E2D5'
SITE_URL     = 'https://hutko-kitchen.com'


def _base_template(content: str, preview: str = '') -> str:
    """Wrap content in branded email shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HUTKO Kitchen</title>
  <!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#f4f0e8;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
  {'<div style="display:none;max-height:0;overflow:hidden;">' + preview + '</div>' if preview else ''}
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f0e8;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

          <!-- HEADER -->
          <tr>
            <td style="background-color:{BRAND_BLUE};border-radius:16px 16px 0 0;padding:32px 40px;text-align:center;">
              <p style="margin:0;font-size:28px;font-weight:900;color:#ffffff;letter-spacing:-0.5px;">
                HUTKO <span style="color:{BRAND_ORANGE};">Kitchen</span>
              </p>
              <p style="margin:6px 0 0;font-size:12px;color:rgba(255,255,255,0.6);letter-spacing:2px;text-transform:uppercase;">
                Ukrainian Frozen Food · Netherlands
              </p>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="background-color:#ffffff;padding:40px;border-left:1px solid #e8e2d5;border-right:1px solid #e8e2d5;">
              {content}
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background-color:{BRAND_CREAM};border-radius:0 0 16px 16px;border:1px solid #ddd6c6;border-top:none;padding:24px 40px;text-align:center;">
              <p style="margin:0 0 8px;font-size:13px;color:#666;">
                <a href="{SITE_URL}" style="color:{BRAND_BLUE};text-decoration:none;font-weight:600;">hutko-kitchen.com</a>
                &nbsp;·&nbsp;
                <a href="{SITE_URL}/contact.html" style="color:{BRAND_BLUE};text-decoration:none;">Contact us</a>
                &nbsp;·&nbsp;
                <a href="https://instagram.com/hutko.kitchen" style="color:{BRAND_BLUE};text-decoration:none;">@hutko.kitchen</a>
              </p>
              <p style="margin:0;font-size:11px;color:#999;">
                © 2025 HUTKO Kitchen · Amsterdam, Netherlands<br>
                This is an automated message — please do not reply to this email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_email(to: str, subject: str, html: str):
    """Send email via Resend. Silently skips if API key not configured."""
    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        print(f"[EMAIL SKIPPED — no RESEND_API_KEY] To: {to} | Subject: {subject}")
        return
    resend.api_key = api_key
    sender = os.environ.get('EMAIL_FROM', 'HUTKO Kitchen <noreply@hutko-kitchen.com>')
    try:
        resend.Emails.send({
            "from":    sender,
            "to":      [to],
            "subject": subject,
            "html":    html,
        })
        print(f"[EMAIL SENT] To: {to} | Subject: {subject}")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


# ── WELCOME EMAIL (on registration) ─────────────────────
def send_welcome(name: str, email: str):
    first = name.split()[0]
    content = f"""
      <h1 style="margin:0 0 8px;font-size:28px;font-weight:900;color:#111;letter-spacing:-0.5px;">
        Welcome, {first}! 👋
      </h1>
      <p style="margin:0 0 24px;font-size:15px;color:#666;line-height:1.6;">
        Your HUTKO Kitchen account is ready. We're happy to have you!
      </p>

      <div style="background:{BRAND_CREAM};border-radius:12px;padding:24px;margin:0 0 28px;">
        <p style="margin:0 0 12px;font-size:14px;font-weight:700;color:#111;">What you can do now:</p>
        <p style="margin:0 0 8px;font-size:14px;color:#444;">
          🥞 &nbsp;<strong>Browse our menu</strong> — syrnyky, borscht, chicken balls and more
        </p>
        <p style="margin:0 0 8px;font-size:14px;color:#444;">
          🚚 &nbsp;<strong>Fast delivery</strong> — Thursday & Saturday across the Netherlands
        </p>
        <p style="margin:0;font-size:14px;color:#444;">
          ❄️ &nbsp;<strong>Frozen fresh</strong> — cooked in small batches, frozen right after
        </p>
      </div>

      <table cellpadding="0" cellspacing="0" width="100%">
        <tr>
          <td align="center">
            <a href="{SITE_URL}/shop.html"
               style="display:inline-block;background:{BRAND_ORANGE};color:#fff;
                      text-decoration:none;font-size:15px;font-weight:700;
                      padding:14px 36px;border-radius:100px;">
              Browse the menu →
            </a>
          </td>
        </tr>
      </table>

      <p style="margin:28px 0 0;font-size:14px;color:#999;text-align:center;">
        Questions? Reply to this email or visit our
        <a href="{SITE_URL}/contact.html" style="color:{BRAND_BLUE};">contact page</a>.
      </p>
    """
    send_email(
        email,
        "Welcome to HUTKO Kitchen! 🇺🇦",
        _base_template(content, f"Welcome {first}! Your account is ready.")
    )


# ── ORDER CONFIRMATION (to customer) ────────────────────
def send_order_confirmation(order_ref: str, name: str, email: str,
                             items: list, subtotal: float,
                             delivery_cost: float, total: float,
                             address: str, delivery_method: str):
    first = name.split()[0]
    items_html = ''.join([
        f"""<tr>
          <td style="padding:10px 0;border-bottom:1px solid #f0ece4;font-size:14px;color:#333;">
            {item['name']}
          </td>
          <td style="padding:10px 0;border-bottom:1px solid #f0ece4;font-size:14px;color:#666;text-align:center;">
            ×{item['qty']}
          </td>
          <td style="padding:10px 0;border-bottom:1px solid #f0ece4;font-size:14px;font-weight:700;color:#111;text-align:right;">
            €{item['qty'] * item['price']}
          </td>
        </tr>"""
        for item in items
    ])

    delivery_label = {'standard': 'Standard (2–3 days)', 'express': 'Express (next day)', 'free': 'Free delivery'}.get(delivery_method, delivery_method)

    content = f"""
      <h1 style="margin:0 0 4px;font-size:26px;font-weight:900;color:#111;">
        Order confirmed! 🎉
      </h1>
      <p style="margin:0 0 24px;font-size:15px;color:#666;">
        Hi {first}, your order <strong style="color:{BRAND_BLUE};">#{order_ref}</strong> has been received.
        We'll send you a confirmation once it's packed and on its way.
      </p>

      <!-- Order items -->
      <div style="background:{BRAND_CREAM};border-radius:12px;padding:20px 24px;margin:0 0 24px;">
        <p style="margin:0 0 14px;font-size:13px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#666;">
          Your order
        </p>
        <table width="100%" cellpadding="0" cellspacing="0">
          {items_html}
          <tr>
            <td colspan="2" style="padding:10px 0 4px;font-size:13px;color:#666;">Subtotal</td>
            <td style="padding:10px 0 4px;font-size:13px;color:#666;text-align:right;">€{subtotal}</td>
          </tr>
          <tr>
            <td colspan="2" style="padding:4px 0;font-size:13px;color:#666;">Delivery ({delivery_label})</td>
            <td style="padding:4px 0;font-size:13px;color:#666;text-align:right;">{'Free' if delivery_cost == 0 else f'€{delivery_cost}'}</td>
          </tr>
          <tr>
            <td colspan="2" style="padding:12px 0 0;font-size:16px;font-weight:900;color:#111;border-top:2px solid #ddd6c6;">Total</td>
            <td style="padding:12px 0 0;font-size:16px;font-weight:900;color:{BRAND_ORANGE};text-align:right;border-top:2px solid #ddd6c6;">€{total}</td>
          </tr>
        </table>
      </div>

      <!-- Delivery address -->
      <div style="border:1px solid #e8e2d5;border-radius:12px;padding:20px 24px;margin:0 0 28px;">
        <p style="margin:0 0 8px;font-size:13px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#666;">
          Delivery address
        </p>
        <p style="margin:0;font-size:14px;color:#333;line-height:1.6;">{name}<br>{address}</p>
      </div>

      <!-- What's next -->
      <div style="background:{BRAND_BLUE};border-radius:12px;padding:20px 24px;margin:0 0 28px;">
        <p style="margin:0 0 8px;font-size:13px;font-weight:700;color:rgba(255,255,255,0.6);letter-spacing:1.5px;text-transform:uppercase;">
          What happens next
        </p>
        <p style="margin:0 0 6px;font-size:14px;color:#fff;">📦 &nbsp;We'll pack your order fresh and freeze it carefully</p>
        <p style="margin:0 0 6px;font-size:14px;color:#fff;">🚚 &nbsp;Delivered on Thursday or Saturday in insulated packaging</p>
        <p style="margin:0;font-size:14px;color:#fff;">📧 &nbsp;You'll receive an update when your order is on its way</p>
      </div>

      <table cellpadding="0" cellspacing="0" width="100%">
        <tr>
          <td align="center">
            <a href="{SITE_URL}/account.html#orders"
               style="display:inline-block;background:{BRAND_ORANGE};color:#fff;
                      text-decoration:none;font-size:14px;font-weight:700;
                      padding:13px 32px;border-radius:100px;">
              View my orders →
            </a>
          </td>
        </tr>
      </table>
    """
    send_email(
        email,
        f"Order confirmed — #{order_ref} 🎉",
        _base_template(content, f"Your order #{order_ref} is confirmed! Total: €{total}")
    )


# ── NEW ORDER NOTIFICATION (to owner) ───────────────────
def send_order_notification(order_ref: str, name: str, email: str,
                              phone: str, items: list, total: float,
                              address: str, delivery_method: str, notes: str):
    owner_email = os.environ.get('OWNER_EMAIL', 'nastiapolimasheva@hutko-kitchen.com')
    items_text = '<br>'.join([f"• {i['name']} ×{i['qty']} — €{i['qty']*i['price']}" for i in items])

    content = f"""
      <div style="background:{BRAND_ORANGE};border-radius:12px;padding:16px 24px;margin:0 0 24px;">
        <p style="margin:0;font-size:20px;font-weight:900;color:#fff;">
          🛒 New order: <strong>#{order_ref}</strong>
        </p>
        <p style="margin:4px 0 0;font-size:14px;color:rgba(255,255,255,0.8);">Total: €{total}</p>
      </div>

      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="50%" style="padding:0 12px 0 0;vertical-align:top;">
            <div style="background:{BRAND_CREAM};border-radius:12px;padding:18px 20px;">
              <p style="margin:0 0 12px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#666;">Customer</p>
              <p style="margin:0 0 4px;font-size:14px;font-weight:700;color:#111;">{name}</p>
              <p style="margin:0 0 4px;font-size:13px;color:#666;">{email}</p>
              <p style="margin:0;font-size:13px;color:#666;">{phone}</p>
            </div>
          </td>
          <td width="50%" style="padding:0 0 0 12px;vertical-align:top;">
            <div style="background:{BRAND_CREAM};border-radius:12px;padding:18px 20px;">
              <p style="margin:0 0 12px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#666;">Delivery</p>
              <p style="margin:0 0 4px;font-size:14px;font-weight:700;color:#111;">{address}</p>
              <p style="margin:0;font-size:13px;color:#666;">{delivery_method}</p>
              {'<p style="margin:6px 0 0;font-size:13px;color:#888;font-style:italic;">Note: ' + notes + '</p>' if notes else ''}
            </div>
          </td>
        </tr>
      </table>

      <div style="border:1px solid #e8e2d5;border-radius:12px;padding:18px 24px;margin:16px 0 24px;">
        <p style="margin:0 0 12px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#666;">Items ordered</p>
        <p style="margin:0;font-size:14px;color:#333;line-height:2;">{items_text}</p>
      </div>

      <table cellpadding="0" cellspacing="0" width="100%">
        <tr>
          <td align="center">
            <a href="https://hutko-kitchen.onrender.com/api/admin/stats"
               style="display:inline-block;background:{BRAND_BLUE};color:#fff;
                      text-decoration:none;font-size:14px;font-weight:700;
                      padding:13px 32px;border-radius:100px;">
              View admin dashboard →
            </a>
          </td>
        </tr>
      </table>
    """
    send_email(
        owner_email,
        f"🛒 New order #{order_ref} — €{total}",
        _base_template(content, f"New order from {name} — €{total}")
    )


# ── CONTACT FORM AUTO-REPLY (to customer) ───────────────
def send_contact_reply(name: str, email: str, topic: str, body: str):
    first = name.split()[0]
    content = f"""
      <h1 style="margin:0 0 8px;font-size:26px;font-weight:900;color:#111;">
        We got your message! 💌
      </h1>
      <p style="margin:0 0 24px;font-size:15px;color:#666;line-height:1.6;">
        Hi {first}, thanks for reaching out. We've received your message and will get back to you within <strong>2 business days</strong>.
      </p>

      <div style="background:{BRAND_CREAM};border-radius:12px;padding:20px 24px;margin:0 0 28px;">
        <p style="margin:0 0 8px;font-size:13px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#666;">
          Your message
        </p>
        <p style="margin:0 0 6px;font-size:13px;color:#888;">Topic: <strong style="color:#333;">{topic}</strong></p>
        <p style="margin:0;font-size:14px;color:#444;line-height:1.6;font-style:italic;">
          "{body[:300]}{'...' if len(body) > 300 else ''}"
        </p>
      </div>

      <div style="border-left:3px solid {BRAND_ORANGE};padding:12px 20px;margin:0 0 28px;">
        <p style="margin:0;font-size:14px;color:#666;line-height:1.6;">
          For urgent order questions, you can also reach us on Instagram
          <a href="https://instagram.com/hutko.kitchen" style="color:{BRAND_BLUE};font-weight:700;">@hutko.kitchen</a>
        </p>
      </div>

      <p style="margin:0;font-size:14px;color:#999;text-align:center;">
        З любов'ю / With love,<br>
        <strong style="color:#111;">The HUTKO Kitchen team</strong> 🇺🇦
      </p>
    """
    send_email(
        email,
        "We received your message — HUTKO Kitchen",
        _base_template(content, f"Thanks {first}! We'll reply within 2 business days.")
    )


# ── CONTACT FORM NOTIFICATION (to owner) ────────────────
def send_contact_notification(name: str, email: str, phone: str,
                               topic: str, title: str, body: str):
    owner_email = os.environ.get('OWNER_EMAIL', 'nastiapolimasheva@hutko-kitchen.com')
    content = f"""
      <div style="background:{BRAND_BLUE};border-radius:12px;padding:16px 24px;margin:0 0 24px;">
        <p style="margin:0;font-size:18px;font-weight:900;color:#fff;">
          📬 New message: <strong>{title}</strong>
        </p>
        <p style="margin:4px 0 0;font-size:13px;color:rgba(255,255,255,0.7);">Topic: {topic}</p>
      </div>

      <div style="background:{BRAND_CREAM};border-radius:12px;padding:18px 24px;margin:0 0 20px;">
        <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#666;">From</p>
        <p style="margin:0 0 4px;font-size:15px;font-weight:700;color:#111;">{name}</p>
        <p style="margin:0 0 4px;font-size:13px;color:#666;">
          <a href="mailto:{email}" style="color:{BRAND_BLUE};">{email}</a>
        </p>
        {'<p style="margin:0;font-size:13px;color:#666;">' + phone + '</p>' if phone else ''}
      </div>

      <div style="border:1px solid #e8e2d5;border-radius:12px;padding:18px 24px;margin:0 0 24px;">
        <p style="margin:0 0 10px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#666;">Message</p>
        <p style="margin:0;font-size:14px;color:#333;line-height:1.7;">{body}</p>
      </div>

      <table cellpadding="0" cellspacing="0" width="100%">
        <tr>
          <td align="center">
            <a href="mailto:{email}?subject=Re: {title}"
               style="display:inline-block;background:{BRAND_ORANGE};color:#fff;
                      text-decoration:none;font-size:14px;font-weight:700;
                      padding:13px 32px;border-radius:100px;">
              Reply to {name} →
            </a>
          </td>
        </tr>
      </table>
    """
    send_email(
        owner_email,
        f"📬 New message from {name}: {title}",
        _base_template(content, f"New contact from {name} — {topic}")
    )
