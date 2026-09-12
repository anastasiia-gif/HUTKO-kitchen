"""
HUTKO — validators.py  (new, 2026-09-12)

Contact details are the only way to reach a customer about their order, and
until now nothing checked them — not the page, not the server.

  • The email box is <input type="email">, but that only validates during a
    native form submit and the checkout button is an onclick handler, so the
    browser check never ran. A phone number typed into the email box was
    accepted, and the confirmation email went nowhere.
  • Order HK-1XT1EP has "antonyka@hotmail.com" in the PHONE column.

These live on the server as well as the page for the same reason the item
choices do: a page check is a courtesy, a server check is a guarantee. A stale
cached copy of the site, or anything posting straight to the API, bypasses the
page entirely.

Honest limit: no amount of checking proves an address or number is real —
only sending something to it does. These reject what cannot possibly be
right, which is a different and smaller claim.
"""

import re

# Deliberately not RFC 5322. That grammar accepts things no mail server will,
# and rejecting a real customer's address is worse than accepting a fake one.
_EMAIL_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")

MAX_EMAIL_LEN = 254      # RFC 5321 path limit
MIN_PHONE_DIGITS = 8
MAX_PHONE_DIGITS = 15    # E.164


def normalise_email(raw):
    return str(raw or '').strip().lower()


def validate_email(raw):
    """Returns (cleaned, error_or_None)."""
    email = normalise_email(raw)
    if not email:
        return '', 'Please enter your email address.'
    if len(email) > MAX_EMAIL_LEN:
        return email, 'That email address is too long.'
    if ' ' in email:
        return email, 'An email address cannot contain spaces.'
    if email.count('@') != 1:
        return email, ('That does not look like an email address — it needs exactly one @ '
                       '(for example anna@email.com).')
    local, _, domain = email.partition('@')
    if not local or not domain:
        return email, 'That does not look like an email address (for example anna@email.com).'
    if '.' not in domain:
        return email, 'The part after the @ needs a dot in it, like gmail.com.'
    if '..' in email or local.startswith('.') or local.endswith('.') \
            or domain.startswith('.') or domain.endswith('.') or domain.startswith('-'):
        return email, 'That email address has a dot or dash in a place it cannot be.'
    if not _EMAIL_RE.match(email):
        return email, 'That does not look like a valid email address.'
    return email, None


def validate_phone(raw, field_name='phone number'):
    """Returns (cleaned, error_or_None).

    Kept permissive on FORM so international customers are not turned away;
    strict about the things that are certainly not a phone number.
    """
    phone = str(raw or '').strip()
    if not phone:
        return '', f'Please enter your {field_name}.'
    if '@' in phone:
        return phone, 'That looks like an email address. Please enter a phone number we can call.'
    digits = re.sub(r'\D', '', phone)
    if len(digits) < MIN_PHONE_DIGITS:
        return phone, f'That phone number is too short — we need at least {MIN_PHONE_DIGITS} digits.'
    if len(digits) > MAX_PHONE_DIGITS:
        return phone, 'That phone number is too long.'
    # Anything outside digits and the usual punctuation is not a phone number.
    if re.search(r'[^0-9+()\-.\s/]', phone):
        return phone, 'A phone number can only contain digits, spaces and + ( ) - characters.'
    if phone.count('+') > 1 or ('+' in phone and not phone.lstrip().startswith('+')):
        return phone, 'The + belongs at the start of an international number.'
    # 00000000 / 12345678 and friends: syntactically fine, obviously filler.
    if len(set(digits)) == 1:
        return phone, 'Please enter a real phone number we can reach you on.'
    if digits in ('0123456789', '1234567890', '012345678', '123456789'):
        return phone, 'Please enter a real phone number we can reach you on.'
    return phone, None


# Common typos in the domains HUTKO's customers actually use. Used as a
# SUGGESTION on the page, never to block an order — someone really could own
# an address at an unusual domain.
DOMAIN_TYPOS = {
    'gmial.com': 'gmail.com', 'gmai.com': 'gmail.com', 'gmail.co': 'gmail.com',
    'gmail.con': 'gmail.com', 'gnail.com': 'gmail.com', 'gmail.cm': 'gmail.com',
    'hotmai.com': 'hotmail.com', 'hotmial.com': 'hotmail.com', 'hotmail.co': 'hotmail.com',
    'hotmail.con': 'hotmail.com', 'hotnail.com': 'hotmail.com',
    'outlok.com': 'outlook.com', 'outloo.com': 'outlook.com', 'outlook.con': 'outlook.com',
    'yaho.com': 'yahoo.com', 'yahoo.co': 'yahoo.com',
    'iclould.com': 'icloud.com', 'icloud.co': 'icloud.com',
    'live.co': 'live.com', 'zigo.nl': 'ziggo.nl', 'gmailcom': 'gmail.com',
}


def suggest_email(raw):
    """Returns a corrected address, or None. Advisory only."""
    email = normalise_email(raw)
    if '@' not in email:
        return None
    local, _, domain = email.partition('@')
    fixed = DOMAIN_TYPOS.get(domain)
    return f'{local}@{fixed}' if fixed else None


# ──────────────────────────────────────────────────────────────────────────
#  Address & name fields (added 2026-09-12)
#  Until now every one of these was checked only for "is it non-empty".
#  A delivery address that cannot be delivered to is as useless as an email
#  that bounces, and the driver finds out on the day.
# ──────────────────────────────────────────────────────────────────────────

# A letter in ANY alphabet — Ukrainian customers, Dutch tussenvoegsels.
_HAS_LETTER = re.compile(r'[^\W\d_]', re.UNICODE)
_NAME_BAD = re.compile(r'[0-9<>@{}\[\]\\/|`~^*=_+]')
_URLISH = re.compile(r'(https?://|www\.)', re.IGNORECASE)

# The 12 Dutch provinces, with the English spellings people actually type.
PROVINCES = {
    'drenthe': 'Drenthe', 'flevoland': 'Flevoland',
    'friesland': 'Friesland', 'fryslan': 'Friesland', 'fryslân': 'Friesland',
    'gelderland': 'Gelderland', 'groningen': 'Groningen', 'limburg': 'Limburg',
    'noord-brabant': 'Noord-Brabant', 'north brabant': 'Noord-Brabant',
    'noord brabant': 'Noord-Brabant',
    'noord-holland': 'Noord-Holland', 'north holland': 'Noord-Holland',
    'noord holland': 'Noord-Holland',
    'overijssel': 'Overijssel', 'utrecht': 'Utrecht', 'zeeland': 'Zeeland',
    'zuid-holland': 'Zuid-Holland', 'south holland': 'Zuid-Holland',
    'zuid holland': 'Zuid-Holland',
}


def validate_name(raw, label='name'):
    name = ' '.join(str(raw or '').split())          # collapse runs of spaces
    if not name:
        return '', f'Please enter your {label}.'
    if len(name) > 60:
        return name, f'That {label} is too long.'
    if not _HAS_LETTER.search(name):
        return name, f'Please enter your real {label}.'
    if _URLISH.search(name) or _NAME_BAD.search(name):
        return name, f'That {label} contains characters a name cannot have.'
    return name, None


def validate_postcode(raw):
    """Dutch postcode: 1234 AB. Stored normalised, so '1234ab' and '1234 AB'
       are the same postcode when you sort a delivery run by area."""
    pc = str(raw or '').strip().upper().replace('-', ' ')
    compact = re.sub(r'\s+', '', pc)
    if not compact:
        return '', 'Please enter your postcode.'
    m = re.fullmatch(r'([1-9][0-9]{3})\s*([A-Z]{2})', compact)
    if not m:
        return pc, 'A Dutch postcode looks like 5223 AP — four digits then two letters.'
    # SA / SD / SS were never issued (wartime associations).
    if m.group(2) in ('SA', 'SD', 'SS'):
        return pc, 'That postcode does not exist — please check it.'
    return f'{m.group(1)} {m.group(2)}', None


def validate_house_number(raw):
    house = ' '.join(str(raw or '').split())
    if not house:
        return '', 'Please enter your house number.'
    if len(house) > 12:
        return house, 'That house number is too long.'
    if not re.search(r'\d', house):
        return house, 'A house number needs at least one digit — for example 103, or 12A.'
    # 103 · 12A · 12-2 · 12 bis · 4hs
    if not re.fullmatch(r'\d{1,5}\s*[-/]?\s*[A-Za-z0-9]{0,6}', house):
        return house, 'That house number does not look right — for example 103, 12A or 12-2.'
    return house, None


def validate_street(raw):
    street = ' '.join(str(raw or '').split())
    if not street:
        return '', 'Please enter your street.'
    if len(street) > 100:
        return street, 'That street name is too long.'
    if not _HAS_LETTER.search(street):
        return street, 'Please enter a street name.'
    if _URLISH.search(street):
        return street, 'That does not look like a street name.'
    return street, None


def validate_city(raw):
    city = ' '.join(str(raw or '').split())
    if not city:
        return '', 'Please enter your city.'
    if len(city) > 60:
        return city, 'That city name is too long.'
    if not _HAS_LETTER.search(city):
        return city, 'Please enter a city name.'
    if _URLISH.search(city):
        return city, 'That does not look like a city name.'
    return city, None


def validate_province(raw):
    """HUTKO delivers inside the Netherlands only, so this is a closed list of
       twelve. Anything else is a typo or a country we cannot reach."""
    prov = ' '.join(str(raw or '').split())
    if not prov:
        return '', 'Please choose your province.'
    canonical = PROVINCES.get(prov.lower())
    if not canonical:
        return prov, (f'"{prov}" is not a Dutch province. Please choose one of: '
                      + ', '.join(sorted(set(PROVINCES.values()))) + '.')
    return canonical, None


def validate_notes(raw, limit=1000):
    """Free text, so the only rules are length and no control characters.
       Must stay friendly to Cyrillic — real customers write in Ukrainian."""
    notes = str(raw or '').strip()
    if not notes:
        return '', None                       # optional
    if len(notes) > limit:
        return notes[:limit], f'Please keep the delivery note under {limit} characters.'
    notes = ''.join(ch for ch in notes if ch == '\n' or ch == '\t' or ord(ch) >= 32)
    return notes, None
