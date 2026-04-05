"""
HUTKO — auth.py
Token-based auth. On login/register the server returns a token
which the frontend stores in localStorage and sends as
Authorization: Bearer <token> on every request.
No cross-origin cookie issues.
"""

import bcrypt
import secrets
from flask import Blueprint, request, jsonify, g
from database import get_db
from functools import wraps
from emails import send_welcome

auth_bp = Blueprint('auth', __name__)

# In-memory token store: { token: user_id }
# Fine for this scale. For production use Redis or a DB table.
_tokens = {}


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def make_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    _tokens[token] = user_id
    return token


def get_user_from_token(token: str):
    if not token:
        return None
    user_id = _tokens.get(token)
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def token_required(f):
    """Decorator: extracts Bearer token, sets g.user or returns 401."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '').strip()
        user = get_user_from_token(token)
        if not user:
            return jsonify({'error': 'Not logged in.'}), 401
        g.user = user
        g.token = token
        return f(*args, **kwargs)
    return decorated


def optional_token(f):
    """Decorator: sets g.user if token present, None otherwise."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '').strip()
        g.user = get_user_from_token(token) if token else None
        g.token = token
        return f(*args, **kwargs)
    return decorated


def user_to_dict(user):
    return {
        'id':            user['id'],
        'name':          user['name'],
        'email':         user['email'],
        'phone':         user['phone'],
        'addr_street':   user['addr_street'],
        'addr_postcode': user['addr_postcode'],
        'addr_city':     user['addr_city'],
        'addr_province': user['addr_province'],
        'created_at':    user['created_at'],
    }


# ── REGISTER ────────────────────────────────────────────
@auth_bp.route('/api/register', methods=['POST'])
def register():
    data     = request.get_json()
    name     = (data.get('name') or '').strip()
    email    = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '')
    phone    = (data.get('phone') or '').strip()

    if not name or not email or not password:
        return jsonify({'error': 'Name, email and password are required.'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    conn = get_db()
    if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
        conn.close()
        return jsonify({'error': 'An account with this email already exists.'}), 409

    pw_hash = hash_password(password)
    cursor  = conn.execute(
        "INSERT INTO users (name, email, password_hash, phone) VALUES (?, ?, ?, ?)",
        (name, email, pw_hash, phone)
    )
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()

    token = make_token(user['id'])

    # Send welcome email
    try:
        send_welcome(user['name'], user['email'])
    except Exception as e:
        print(f"[WELCOME EMAIL ERROR] {e}")

    return jsonify({'user': user_to_dict(user), 'token': token}), 201


# ── LOGIN ────────────────────────────────────────────────
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not check_password(password, user['password_hash']):
        return jsonify({'error': 'Incorrect email or password.'}), 401

    token = make_token(user['id'])
    return jsonify({'user': user_to_dict(user), 'token': token}), 200


# ── LOGOUT ───────────────────────────────────────────────
@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '').strip()
    _tokens.pop(token, None)
    return jsonify({'message': 'Logged out.'}), 200


# ── GET CURRENT USER ─────────────────────────────────────
@auth_bp.route('/api/me', methods=['GET'])
@token_required
def me():
    return jsonify({'user': user_to_dict(g.user)}), 200


# ── UPDATE PROFILE ───────────────────────────────────────
@auth_bp.route('/api/profile', methods=['PUT'])
@token_required
def update_profile():
    data  = request.get_json()
    name  = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    pw    = (data.get('password') or '')

    if not name:
        return jsonify({'error': 'Name cannot be empty.'}), 400
    if pw and len(pw) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    conn = get_db()
    if pw:
        conn.execute(
            "UPDATE users SET name=?, phone=?, password_hash=? WHERE id=?",
            (name, phone, hash_password(pw), g.user['id'])
        )
    else:
        conn.execute(
            "UPDATE users SET name=?, phone=? WHERE id=?",
            (name, phone, g.user['id'])
        )
    conn.commit()
    updated = conn.execute("SELECT * FROM users WHERE id=?", (g.user['id'],)).fetchone()
    conn.close()
    return jsonify({'user': user_to_dict(updated)}), 200


# ── SAVE ADDRESS ─────────────────────────────────────────
@auth_bp.route('/api/address', methods=['PUT'])
@token_required
def update_address():
    data = request.get_json()
    conn = get_db()
    conn.execute("""
        UPDATE users
        SET addr_street=?, addr_postcode=?, addr_city=?, addr_province=?
        WHERE id=?
    """, (
        data.get('street', ''), data.get('postcode', ''),
        data.get('city', ''),   data.get('province', ''),
        g.user['id']
    ))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Address saved.'}), 200
