"""
HUTKO — delivery_zones.py
Delivery zones and the delivery calendar. Same rules as the checkout page
(HUTKO_ZONES / zoneDates in frontend/checkout.html) — keep the two in sync.

  amsterdam  every Tuesday and Thursday              fee_local    (€10)
  utrecht    first Tuesday of each calendar month    fee_regional (€15)
             (Utrecht + 20 km)
  west       third Thursday of each calendar month   fee_regional (€15)
             (The Hague + 15 km, Rotterdam + 15 km, and Gouda by name)

Any other address: delivery by arrangement — no online order.

The server does not trust the zone the browser sends. It looks the address up
itself (PDOK, the free Dutch government address service) and only falls back to
the browser's zone if PDOK cannot be reached, so a checkout never fails just
because PDOK is down.
"""

import math
import re
from datetime import date, datetime, timedelta

import requests

ZONES = {
    'amsterdam': {'fee': 'local', 'rule': 'tue_thu',
                  'hubs': [(52.3676, 4.9041, 10)], 'cities': ['amsterdam'],
                  'label': 'Amsterdam'},
    'utrecht':   {'fee': 'regional', 'rule': 'first_tue',
                  'hubs': [(52.0907, 5.1214, 20)], 'cities': ['utrecht'],
                  'label': 'Utrecht & surroundings'},
    'west':      {'fee': 'regional', 'rule': 'third_thu',
                  'hubs': [(52.0705, 4.3007, 15), (51.9244, 4.4777, 15)],
                  'cities': ['den haag', "'s-gravenhage", 's-gravenhage', 'the hague', 'rotterdam', 'gouda'],
                  'label': 'The Hague, Rotterdam & Gouda'},
}
ZONE_ORDER = ['amsterdam', 'utrecht', 'west']

# One-off calendar changes, 'YYYY-MM-DD'. Empty for now.
EXTRA_DATES = {'amsterdam': [], 'utrecht': [], 'west': []}   # extra run days per zone
SKIP_DATES = []                                              # no delivery anywhere

try:
    from zoneinfo import ZoneInfo
    _AMS = ZoneInfo('Europe/Amsterdam')
except Exception:          # no tz database on the host — fall back to server time
    _AMS = None


def _today():
    """Today in the Netherlands (Render runs on UTC — near midnight that's a different day)."""
    return datetime.now(_AMS).date() if _AMS else date.today()


PDOK_URL = 'https://api.pdok.nl/bzk/locatieserver/search/v3_1/free'


def _km(lat1, lng1, lat2, lng2):
    r = 6371.0
    dlat, dlng = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def zone_for_city(city):
    c = (city or '').strip().lower()
    for zid in ZONE_ORDER:
        if c and c in ZONES[zid]['cities']:
            return zid
    return None


def zone_for(lat, lng, city=''):
    """Amsterdam first, then Gouda by name, then the radius around each hub."""
    by_city = zone_for_city(city)
    if by_city == 'amsterdam' or (city or '').strip().lower() == 'gouda':
        return by_city
    if lat is not None and lng is not None:
        for zid in ZONE_ORDER:
            for hlat, hlng, km in ZONES[zid]['hubs']:
                if _km(lat, lng, hlat, hlng) <= km:
                    return zid
    return by_city


def lookup_address(postcode, house_number, timeout=4):
    """(lat, lng, city) from PDOK, or None if it can't be reached / found."""
    pc = re.sub(r'\s+', '', postcode or '').upper()
    hn = (house_number or '').strip()
    if not pc or not hn:
        return None
    try:
        res = requests.get(PDOK_URL, params={'q': f'{pc} {hn}', 'fq': 'type:adres', 'rows': 1},
                           timeout=timeout)
        docs = res.json().get('response', {}).get('docs', [])
        if not docs:
            return None
        doc = docs[0]
        m = re.search(r'POINT\(([-0-9.]+)\s+([-0-9.]+)\)', doc.get('centroide_ll', ''))
        if not m:
            return None
        return float(m.group(2)), float(m.group(1)), doc.get('woonplaatsnaam', '')
    except Exception as e:
        print(f"[ZONE] PDOK lookup failed: {e}")
        return None


def house_number_from(street):
    """'Damrak 1A' → '1A'. Used when an older page doesn't send house_number."""
    m = re.search(r'(\d+\s*[A-Za-z]?(?:[-\s]\w+)?)\s*$', (street or '').strip())
    return m.group(1).strip() if m else ''


def rule_matches(rule, d):
    dow, dom = d.isoweekday(), d.day      # Mon=1 … Sun=7
    if rule == 'tue_thu':
        return dow in (2, 4)
    if rule == 'first_tue':
        return dow == 2 and dom <= 7
    if rule == 'third_thu':
        return dow == 4 and 15 <= dom <= 21
    return False


def is_delivery_date(zone_id, iso, today=None):
    """True if `iso` (YYYY-MM-DD) is a bookable date for the zone: from
    tomorrow on, and either on the zone's rule or an extra date, and not
    skipped."""
    if zone_id not in ZONES:
        return False
    try:
        d = date.fromisoformat((iso or '').strip())
    except ValueError:
        return False
    today = today or _today()
    if d <= today or d > today + timedelta(days=180):
        return False
    if d.isoformat() in SKIP_DATES:
        return False
    return rule_matches(ZONES[zone_id]['rule'], d) or d.isoformat() in EXTRA_DATES.get(zone_id, [])


def next_dates(zone_id, count, today=None):
    today = today or _today()
    out, d = [], today
    for _ in range(180):
        d += timedelta(days=1)
        if is_delivery_date(zone_id, d.isoformat(), today):
            out.append(d.isoformat())
            if len(out) >= count:
                break
    return out
