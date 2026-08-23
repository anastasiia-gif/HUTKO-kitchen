"""
HUTKO — admin_settings.py  (v1.1)
Read/update editable settings: delivery rules + company / site details.
Keys match what the public site reads, so edits show live.
(Password handled in admin.py; notification-email wiring lands with the
email/Trello increment, so those keys are hidden here for now.)
"""

from flask import Blueprint, request, jsonify
from database import get_db, _placeholder
from admin import admin_required, audit
import settings_store as S

settings_bp = Blueprint('admin_settings', __name__)
_p = _placeholder()

# Delivery settings (area/zone model). delivery_days is display text.
RULE_KEYS = ['fee_local', 'fee_regional', 'free_delivery_over', 'delivery_days', 'max_per_day']
NUMERIC_RULES = {'fee_local', 'fee_regional', 'free_delivery_over', 'max_per_day'}

# Never editable here
PROTECTED = {'admin_password_hash'}
# Not shown in the Contact/site section: notification emails (not wired yet) +
# legacy delivery keys that are mirrored automatically from the fields above.
HIDDEN_FROM_SITE = {'owner_email', 'driver_email',
                    'delivery_cost', 'free_delivery_at', 'delivery_price_express',
                    'delivery_capacity_default', 'delivery_weekdays', 'min_order'}


@settings_bp.route('/api/admin/settings', methods=['GET'])
@admin_required
def get_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    stored = {r['key']: (r['value'] or '') for r in rows}
    rules = {k: stored.get(k, S.DEFAULTS.get(k, '')) for k in RULE_KEYS}
    site = {k: v for k, v in stored.items()
            if k not in RULE_KEYS and k not in PROTECTED and k not in HIDDEN_FROM_SITE}
    return jsonify({'rules': rules, 'site': site}), 200


@settings_bp.route('/api/admin/settings', methods=['PUT'])
@admin_required
def update_settings():
    data = request.get_json(silent=True) or {}
    updates = data.get('updates') if isinstance(data.get('updates'), dict) else data
    clean = {}
    for key, value in updates.items():
        if key in PROTECTED:
            continue
        if key in NUMERIC_RULES:
            try:
                num = float(value)
            except (TypeError, ValueError):
                return jsonify({'error': f'{key} must be a number.'}), 400
            if num < 0:
                return jsonify({'error': f'{key} cannot be negative.'}), 400
            value = int(num) if key in ('max_per_day',) else num
        clean[key] = value
    if not clean:
        return jsonify({'error': 'No valid settings to update.'}), 400
    # Mirror to legacy keys so the delivery-page description text stays consistent
    if 'fee_local' in clean:
        clean['delivery_cost'] = clean['fee_local']
    if 'free_delivery_over' in clean:
        clean['free_delivery_at'] = clean['free_delivery_over']
    S.set_many(clean)
    audit('settings_update', ', '.join(sorted(clean.keys())))
    return jsonify({'message': 'Settings saved.', 'updated': sorted(clean.keys())}), 200
