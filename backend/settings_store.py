"""
HUTKO — settings_store.py  (v1.1)
Single source of truth for editable business settings.

Key names deliberately MATCH what the public site already reads via
data-setting="..." + loadSettingsIntoPage() (contact page) and the delivery
text, so editing a value in the admin updates the live site.
"""

import json
from database import get_db, _placeholder

_p = _placeholder()

DEFAULTS = {
    # ── Contact details (contact page + footer read these) ──
    "email_contact":  "hello@hutko-kitchen.com",
    "phone":          "+31 6 27 15 52 00",
    "address_street": "Amsterdam, Netherlands",
    "instagram":      "@hutko.kitchen",
    "facebook":       "facebook.com/hutkokitchen",
    # ── Office hours (contact page reads these) ──
    "hours_weekday":  "9:00 – 18:00",
    "hours_saturday": "10:00 – 15:00",
    "hours_sunday":   "Closed",

    # ── Delivery rules (site delivery text + checkout read these) ──
    "free_delivery_at":        "60",   # € — free delivery at/above this subtotal
    "delivery_cost":           "5",    # € — standard delivery
    "delivery_price_express":  "12",   # € — express (checkout only)
    "min_order":               "0",    # € — 0 = no minimum (display only)
    "max_per_day":             "15",   # max orders per delivery day
    "delivery_days":           "Thursday & Saturday",  # display text

    # ── Notification recipients (wired to emails in a later increment) ──
    "owner_email":   "",
    "driver_email":  "",

    # ── Admin password (UI-changeable; blank = fall back to ADMIN_PASSWORD env)
    "admin_password_hash": "",
}

# Contact/site values safe to expose publicly
PUBLIC_KEYS = [
    "email_contact", "phone", "address_street", "instagram", "facebook",
    "hours_weekday", "hours_saturday", "hours_sunday",
    "free_delivery_at", "delivery_cost", "min_order", "max_per_day", "delivery_days",
]


def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute(f"SELECT value FROM settings WHERE key={_p}", (key,)).fetchone()
    conn.close()
    if row is not None and row["value"] is not None:
        return row["value"]
    if default is not None:
        return default
    return DEFAULTS.get(key, "")


def get_float(key, default=0.0):
    try:
        return float(get_setting(key))
    except (TypeError, ValueError):
        return default


def get_int(key, default=0):
    try:
        return int(float(get_setting(key)))
    except (TypeError, ValueError):
        return default


def set_setting(key, value):
    conn = get_db()
    conn.execute(
        f"INSERT INTO settings (key, value, updated_at) VALUES ({_p},{_p},datetime('now')) "
        f"ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')",
        (key, str(value)))
    conn.commit()
    conn.close()


def set_many(mapping):
    conn = get_db()
    for key, value in mapping.items():
        conn.execute(
            f"INSERT INTO settings (key, value, updated_at) VALUES ({_p},{_p},datetime('now')) "
            f"ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')",
            (key, str(value)))
    conn.commit()
    conn.close()


def get_all(keys=None):
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    stored = {r["key"]: r["value"] for r in rows}
    keys = keys if keys is not None else list(DEFAULTS.keys())
    return {k: stored.get(k, DEFAULTS.get(k, "")) for k in keys}


def public_settings():
    return get_all(PUBLIC_KEYS)
