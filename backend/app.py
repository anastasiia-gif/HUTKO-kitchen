"""
HUTKO — app.py
Main Flask application.
Run locally:  python app.py
Production:   gunicorn app:app
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv

from database import init_db
from auth    import auth_bp
from orders  import orders_bp
from contact import contact_bp
from admin   import admin_bp

# ── LOAD ENVIRONMENT VARIABLES ───────────────────────────
load_dotenv()

# ── CREATE APP ────────────────────────────────────────────
app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE']   = True   # required for cross-origin cookies
app.config['SESSION_COOKIE_HTTPONLY'] = True

# ── SESSION ───────────────────────────────────────────────
Session(app)

# ── CORS ──────────────────────────────────────────────────
# Allow requests from Netlify frontend (and localhost for dev)
ALLOWED_ORIGINS = [
    "https://hutko.netlify.app",
    "https://testing--hutko.netlify.app",
    "http://localhost:3000",
    "http://127.0.0.1:5500",   # VS Code Live Server
    "null",                     # local file:// during dev
]
custom_origin = os.environ.get('FRONTEND_URL')
if custom_origin:
    ALLOWED_ORIGINS.append(custom_origin)

CORS(app,
     origins=ALLOWED_ORIGINS,
     supports_credentials=True,   # needed for session cookies
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# ── REGISTER BLUEPRINTS ───────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(admin_bp)

# ── HEALTH CHECK ──────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'HUTKO API'}), 200

# ── ERROR HANDLERS ────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found.'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error.'}), 500

# ── STARTUP ───────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"🚀 HUTKO API running on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
