"""
HUTKO — auth.py
Handles user registration, login, logout and profile updates.
Passwords are hashed with bcrypt — never stored in plain text.
Sessions are stored server-side via Flask-Session.
"""

import bcrypt
from flask import Blueprint, request, jsonify, session
from database import get_db

auth_bp = Blueprint('auth', __name__)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def current_user():
    """Return the logged-in user row, or None."""
    uid = session.get('user_id')
    if not uid:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return user


def user_to_dict(user):
    """Convert a user row to a safe dict (no password)."""
    return {
        'id':           user['id'],
        'name':         user['name'],
        'email':        user['email'],
        'phone':        user['phone'],
        'addr_street':  user['addr_street'],
        'addr_postcode':user['addr_postcode'],
        'addr_city':    user['addr_city'],
        'addr_province':user['addr_province'],
        'created_at':   user['created_at'],
    }


# ── REGISTER ────────────────────────────────────────────
@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name     = (data.get('name') or '').strip()
    email    = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '')
    phone    = (data.get('phone') or '').strip()

    if not name or not email or not password:
        return jsonify({'error': 'Name, email and password are required.'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'An account with this email already exists.'}), 409

    pw_hash = hash_password(password)
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, phone) VALUES (?, ?, ?, ?)",
        (name, email, pw_hash, phone)
    )
    conn.commit()
    user_id = cursor.lastrowid
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    session['user_id'] = user_id
    return jsonify({'user': user_to_dict(user)}), 201


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

    session['user_id'] = user['id']
    return jsonify({'user': user_to_dict(user)}), 200


# ── LOGOUT ───────────────────────────────────────────────
@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out.'}), 200


# ── GET CURRENT USER ─────────────────────────────────────
@auth_bp.route('/api/me', methods=['GET'])
def me():
    user = current_user()
    if not user:
        return jsonify({'error': 'Not logged in.'}), 401
    return jsonify({'user': user_to_dict(user)}), 200


# ── UPDATE PROFILE ───────────────────────────────────────
@auth_bp.route('/api/profile', methods=['PUT'])
def update_profile():
    user = current_user()
    if not user:
        return jsonify({'error': 'Not logged in.'}), 401

    data = request.get_json()
    name     = (data.get('name') or '').strip()
    phone    = (data.get('phone') or '').strip()
    password = (data.get('password') or '')

    if not name:
        return jsonify({'error': 'Name cannot be empty.'}), 400

    conn = get_db()
    if password:
        if len(password) < 6:
            conn.close()
            return jsonify({'error': 'Password must be at least 6 characters.'}), 400
        pw_hash = hash_password(password)
        conn.execute(
            "UPDATE users SET name=?, phone=?, password_hash=? WHERE id=?",
            (name, phone, pw_hash, user['id'])
        )
    else:
        conn.execute(
            "UPDATE users SET name=?, phone=? WHERE id=?",
            (name, phone, user['id'])
        )
    conn.commit()
    updated = conn.execute("SELECT * FROM users WHERE id=?", (user['id'],)).fetchone()
    conn.close()
    return jsonify({'user': user_to_dict(updated)}), 200


# ── SAVE ADDRESS ─────────────────────────────────────────
@auth_bp.route('/api/address', methods=['PUT'])
def update_address():
    user = current_user()
    if not user:
        return jsonify({'error': 'Not logged in.'}), 401

    data = request.get_json()
    conn = get_db()
    conn.execute("""
        UPDATE users
        SET addr_street=?, addr_postcode=?, addr_city=?, addr_province=?
        WHERE id=?
    """, (
        data.get('street', ''),
        data.get('postcode', ''),
        data.get('city', ''),
        data.get('province', ''),
        user['id']
    ))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Address saved.'}), 200
