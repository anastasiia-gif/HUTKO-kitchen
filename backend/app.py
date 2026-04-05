"""
HUTKO — app.py
Token-based auth. No session dependency.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from database import init_db
from auth    import auth_bp
from orders  import orders_bp
from contact import contact_bp
from admin   import admin_bp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

ALLOWED_ORIGINS = [
    "https://hutko-kitchen.pages.dev",
    "https://hutko-kitchen.com",
    "https://www.hutko-kitchen.com",
    "https://hutko.netlify.app",
    "https://testing--hutko.netlify.app",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "null",
]
if os.environ.get('FRONTEND_URL'):
    ALLOWED_ORIGINS.append(os.environ['FRONTEND_URL'])

CORS(app,
     origins=ALLOWED_ORIGINS,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

app.register_blueprint(auth_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(admin_bp)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'HUTKO API'}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found.'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error.'}), 500

# Always init DB on startup — works with gunicorn AND direct run
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"HUTKO API running on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
