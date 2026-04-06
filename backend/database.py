"""
HUTKO — database.py
Creates and manages the SQLite database.
All tables are created automatically on first run.
"""

import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH', 'hutko.db')


def get_db():
    """Open a database connection with row_factory for dict-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    conn = get_db()
    c = conn.cursor()

    # ── USERS ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            phone         TEXT,
            addr_street   TEXT,
            addr_postcode TEXT,
            addr_city     TEXT,
            addr_province TEXT,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── ORDERS ─────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_ref       TEXT    NOT NULL UNIQUE,
            user_id         INTEGER REFERENCES users(id),
            customer_name   TEXT    NOT NULL,
            customer_email  TEXT    NOT NULL,
            customer_phone  TEXT,
            addr_street     TEXT    NOT NULL,
            addr_postcode   TEXT    NOT NULL,
            addr_city       TEXT    NOT NULL,
            addr_province   TEXT    NOT NULL,
            delivery_notes  TEXT,
            delivery_method TEXT    NOT NULL DEFAULT 'standard',
            items_json      TEXT    NOT NULL,
            subtotal        REAL    NOT NULL,
            delivery_cost   REAL    NOT NULL,
            total           REAL    NOT NULL,
            status          TEXT    NOT NULL DEFAULT 'confirmed',
            trello_card_id  TEXT,
            created_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── MIGRATE: add trello_card_id if upgrading existing DB ───
    try:
        c.execute("ALTER TABLE orders ADD COLUMN trello_card_id TEXT")
        conn.commit()
    except Exception:
        pass  # Column already exists

    # ── MESSAGES (contact form) ─────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT NOT NULL,
            phone      TEXT,
            social     TEXT,
            topic      TEXT NOT NULL,
            title      TEXT NOT NULL,
            body       TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── NEWSLETTER ──────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS newsletter (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("✓ Database initialised")
