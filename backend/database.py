"""
HUTKO — database.py
SQLite, stored on Render persistent disk at /data/hutko.db

v2: adds catalog (products, product_variants, bundles), settings,
    admin_audit; extends delivery_slots and admin_tokens.
    The public shop now reads products from these tables instead of Excel.
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


def _safe_alter(conn, sql):
    """Run an ALTER that may already have been applied; ignore duplicates."""
    try:
        conn.execute(sql)
    except Exception:
        pass


def init_db():
    conn = get_db()

    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except Exception:
        pass

    conn.execute("""
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS delivery_slots (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_date  TEXT NOT NULL UNIQUE,
            booked     INTEGER NOT NULL DEFAULT 0,
            max_slots  INTEGER NOT NULL DEFAULT 15,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS newsletter (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_tokens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            token      TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id              TEXT PRIMARY KEY,
            category        TEXT,
            name_en         TEXT, name_ua         TEXT, name_nl         TEXT,
            desc_en         TEXT, desc_ua         TEXT, desc_nl         TEXT,
            about_en        TEXT, about_ua        TEXT, about_nl        TEXT,
            prepare_en      TEXT, prepare_ua      TEXT, prepare_nl      TEXT,
            ingredients_en  TEXT, ingredients_ua  TEXT, ingredients_nl  TEXT,
            hutko_tip_en    TEXT, hutko_tip_ua    TEXT, hutko_tip_nl    TEXT,
            storage_en      TEXT, storage_ua      TEXT, storage_nl      TEXT,
            base_price      REAL DEFAULT 0,
            unit            TEXT,
            badge           TEXT,
            photo           TEXT,
            gallery         TEXT,
            dietary         TEXT,
            active          INTEGER NOT NULL DEFAULT 1,
            sort_order      INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS product_variants (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  TEXT NOT NULL,
            label       TEXT,
            price       REAL DEFAULT 0,
            active      INTEGER NOT NULL DEFAULT 1,
            sort_order  INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bundles (
            id              TEXT PRIMARY KEY,
            name_en         TEXT, name_ua        TEXT, name_nl        TEXT,
            size_label      TEXT,
            items           TEXT,
            original_price  REAL DEFAULT 0,
            discount_price  REAL DEFAULT 0,
            photo           TEXT,
            badge           TEXT,
            choice_en       TEXT, choice_ua      TEXT, choice_nl      TEXT,
            active          INTEGER NOT NULL DEFAULT 1,
            sort_order      INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key        TEXT PRIMARY KEY,
            value      TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_audit (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            actor      TEXT,
            action     TEXT,
            detail     TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    for sql in [
        "ALTER TABLE orders ADD COLUMN trello_card_id TEXT",
        "ALTER TABLE orders ADD COLUMN delivery_date TEXT",
        "ALTER TABLE orders ADD COLUMN payment_id TEXT",
        "ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'pending'",
        "ALTER TABLE admin_tokens ADD COLUMN expires_at TEXT",
        "ALTER TABLE delivery_slots ADD COLUMN is_open INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE delivery_slots ADD COLUMN note TEXT",
    ]:
        _safe_alter(conn, sql)

    conn.commit()
    conn.close()
    print(f"[DB] Initialised (SQLite) at {DB_PATH}")
