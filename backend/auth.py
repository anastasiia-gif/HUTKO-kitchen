"""
HUTKO — auth.py
Token-based auth. On login/register the server returns a token
which the frontend stores in localStorage and sends as
Authorization: Bearer <token> on every request.
"""

import bcrypt, secrets
from flask import Blueprint, request, jsonify, g
from database import get_db, _use_postgres
from functools import wraps
from emails import send_welcome

auth_bp = Blueprint('auth', __name__)


def _p():
    return '%s' if _use_postgres() else '?'


def _exec(conn, sql, params=()):
    if _use_postgres():
        cur = conn.cursor(); cur.execute(sql, params); return cur
    return conn.execute(sql, params)


def _ensure_tokens_table(conn):
    dt = "DEFAULT NOW()" if _use_postgres() else "DEFAULT (datetime('now'))"
    sql = f"""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            created_at TEXT {dt}
        )
    """
    _exec(conn, sql)
    conn.commit()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def make_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    conn  = get_db()
    _ensure_tokens_table(conn)
    _exec(conn, f"INSERT INTO auth_tokens (token, user_id) VALUES ({_p()},{_p()})", (token, user_id))
    conn.commit(); conn.close()
    return token


def get_user_from_token(token: str):
    if not token:
        return None
    conn = get_db()
    _ensure_tokens_table(conn)
    p   = _p()
    row = _exec(conn, f"""
        SELECT u.* FROM users u
        JOIN auth_tokens t ON t.user_id = u.id
        WHERE t.token = {p}
    """, (token,)).fetchone()
    conn.close()
    return row


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
        user  = get_user_from_token(token)
        if not user:
            return jsonify({'error': 'Not logged in.'}), 401
        g.user = user; g.token = token
        return f(*args, **kwargs)
    return decorated


def optional_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token  = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
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
    if _exec(conn, f"SELECT id FROM users WHERE email = {_p()}", (email,)).fetchone():
        conn.close()
        return jsonify({'error': 'An account with this email already exists.'}), 409

    pw_hash = hash_password(password)
    if _use_postgres():
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password_hash, phone) VALUES (%s,%s,%s,%s) RETURNING id",
            (name, email, pw_hash, phone)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        user = _exec(conn, "SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
    else:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, phone) VALUES (?,?,?,?)",
            (name, email, pw_hash, phone)
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()

    token = make_token(user['id'])
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
    user = _exec(conn, f"SELECT * FROM users WHERE email = {_p()}", (email,)).fetchone()
    conn.close()

    if not user or not check_password(password, user['password_hash']):
        return jsonify({'error': 'Incorrect email or password.'}), 401

    token = make_token(user['id'])
    return jsonify({'user': user_to_dict(user), 'token': token}), 200


# ── LOGOUT ───────────────────────────────────────────────
@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if token:
        conn = get_db()
        _exec(conn, f"DELETE FROM auth_tokens WHERE token = {_p()}", (token,))
        conn.commit(); conn.close()
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
        _exec(conn, f"UPDATE users SET name={_p()}, phone={_p()}, password_hash={_p()} WHERE id={_p()}",
              (name, phone, hash_password(pw), g.user['id']))
    else:
        _exec(conn, f"UPDATE users SET name={_p()}, phone={_p()} WHERE id={_p()}",
              (name, phone, g.user['id']))
    conn.commit()
    updated = _exec(conn, f"SELECT * FROM users WHERE id={_p()}", (g.user['id'],)).fetchone()
    conn.close()
    return jsonify({'user': user_to_dict(updated)}), 200


# ── SAVE ADDRESS ─────────────────────────────────────────
@auth_bp.route('/api/address', methods=['PUT'])
@token_required
def update_address():
    data = request.get_json()
    conn = get_db()
    _exec(conn, f"""
        UPDATE users
        SET addr_street={_p()}, addr_postcode={_p()}, addr_city={_p()}, addr_province={_p()}
        WHERE id={_p()}
    """, (data.get('street',''), data.get('postcode',''),
          data.get('city',''), data.get('province',''), g.user['id']))
    conn.commit(); conn.close()
    return jsonify({'message': 'Address saved.'}), 200
