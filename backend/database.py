"""
HUTKO — database.py
SQLite, stored on Render persistent disk at /data/hutko.db
"""

import os
import sqlite3

DB_PATH = os.environ.get('DB_PATH', 'hutko.db')


def _use_postgres():
    return False


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _placeholder():
    return '?'


def _autoincrement():
    return 'INTEGER PRIMARY KEY AUTOINCREMENT'


def _datetime_default():
    return "DEFAULT (datetime('now'))"


def init_db():
    conn = get_db()

    conn.execute(f"""
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

    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_ref       TEXT    NOT NULL UNIQUE,
            user_id         INTEGER,
            customer_name   TEXT    NOT NULL,
            customer_email  TEXT    NOT NULL,
            customer_phone  TEXT,
            addr_street     TEXT    NOT NULL,
            addr_postcode   TEXT    NOT NULL,
            addr_city       TEXT    NOT NULL,
            addr_province   TEXT    NOT NULL,
            delivery_notes  TEXT,
            delivery_method TEXT    NOT NULL DEFAULT 'standard',
            delivery_date   TEXT,
            items_json      TEXT    NOT NULL,
            subtotal        REAL    NOT NULL,
            delivery_cost   REAL    NOT NULL,
            total           REAL    NOT NULL,
            status          TEXT    NOT NULL DEFAULT 'confirmed',
            trello_card_id  TEXT,
            payment_id      TEXT,
            payment_status  TEXT    DEFAULT 'pending',
            created_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS delivery_slots (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_date  TEXT NOT NULL UNIQUE,
            booked     INTEGER NOT NULL DEFAULT 0,
            max_slots  INTEGER NOT NULL DEFAULT 15,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute(f"""
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

    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS newsletter (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS admin_tokens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            token      TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Safe migrations
    for sql in [
        "ALTER TABLE orders ADD COLUMN trello_card_id TEXT",
        "ALTER TABLE orders ADD COLUMN delivery_date TEXT",
        "ALTER TABLE orders ADD COLUMN payment_id TEXT",
        "ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'pending'",
    ]:
        try:
            conn.execute(sql)
        except Exception:
            pass

    conn.commit()
    conn.close()
    print(f"[DB] Initialised (SQLite) at {DB_PATH}")
