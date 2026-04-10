"""
HUTKO — database.py
PostgreSQL in production (Render), SQLite locally.
All tables created automatically on first run.
"""

import os
import sqlite3

DB_PATH      = os.environ.get('DB_PATH', 'hutko.db')
DATABASE_URL = os.environ.get('DATABASE_URL', '')   # Set by Render PostgreSQL addon


def _use_postgres():
    return bool(DATABASE_URL)


def get_db():
    """
    Return an open DB connection.
    PostgreSQL when DATABASE_URL is set, otherwise SQLite.
    Both expose .execute() / .commit() / .close() identically.
    Rows are dict-like in both cases.
    """
    if _use_postgres():
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _placeholder():
    """? for SQLite, %s for Postgres."""
    return '%s' if _use_postgres() else '?'


def _autoincrement():
    return 'SERIAL PRIMARY KEY' if _use_postgres() else 'INTEGER PRIMARY KEY AUTOINCREMENT'


def _datetime_default():
    return 'DEFAULT NOW()' if _use_postgres() else "DEFAULT (datetime('now'))"


def init_db():
    """Create all tables if they don't exist yet."""
    conn = get_db()

    if _use_postgres():
        cur = conn.cursor()
        _exec = cur.execute
    else:
        cur = conn
        _exec = conn.execute

    ai = _autoincrement()
    dt = _datetime_default()

    # ── USERS ──────────────────────────────────────────
    _exec(f"""
        CREATE TABLE IF NOT EXISTS users (
            id            {ai},
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            phone         TEXT,
            addr_street   TEXT,
            addr_postcode TEXT,
            addr_city     TEXT,
            addr_province TEXT,
            created_at    TEXT    {dt}
        )
    """)

    # ── ORDERS ─────────────────────────────────────────
    _exec(f"""
        CREATE TABLE IF NOT EXISTS orders (
            id              {ai},
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
            created_at      TEXT    {dt}
        )
    """)

    # ── DELIVERY SLOTS ──────────────────────────────────
    # Tracks how many orders are booked per delivery date.
    # MAX_SLOTS_PER_DAY enforced at checkout (default 15).
    _exec(f"""
        CREATE TABLE IF NOT EXISTS delivery_slots (
            id         {ai},
            slot_date  TEXT NOT NULL UNIQUE,
            booked     INTEGER NOT NULL DEFAULT 0,
            max_slots  INTEGER NOT NULL DEFAULT 15,
            created_at TEXT {dt}
        )
    """)

    # ── MESSAGES (contact form) ─────────────────────────
    _exec(f"""
        CREATE TABLE IF NOT EXISTS messages (
            id         {ai},
            name       TEXT NOT NULL,
            email      TEXT NOT NULL,
            phone      TEXT,
            social     TEXT,
            topic      TEXT NOT NULL,
            title      TEXT NOT NULL,
            body       TEXT NOT NULL,
            created_at TEXT {dt}
        )
    """)

    # ── NEWSLETTER ──────────────────────────────────────
    _exec(f"""
        CREATE TABLE IF NOT EXISTS newsletter (
            id         {ai},
            email      TEXT NOT NULL UNIQUE,
            created_at TEXT {dt}
        )
    """)

    # ── MIGRATIONS: add new columns to existing DBs ─────
    _safe_alter(conn, cur, "ALTER TABLE orders ADD COLUMN trello_card_id TEXT")
    _safe_alter(conn, cur, "ALTER TABLE orders ADD COLUMN delivery_date TEXT")

    conn.commit()
    conn.close()
    print(f"✓ Database initialised ({'PostgreSQL' if _use_postgres() else 'SQLite'})")


def _safe_alter(conn, cur, sql):
    """Run ALTER TABLE silently — ignore if column already exists."""
    try:
        if _use_postgres():
            cur.execute(sql)
            conn.commit()
        else:
            conn.execute(sql)
            conn.commit()
    except Exception:
        if _use_postgres():
            conn.rollback()
