"""
HUTKO — database.py
PostgreSQL in production (when DATABASE_URL is set), SQLite locally.
psycopg2 is imported lazily — only when DATABASE_URL is actually present,
so the app starts fine on SQLite even if psycopg2 isn't installed.
"""

import os
import sqlite3

DB_PATH      = os.environ.get('DB_PATH', 'hutko.db')
DATABASE_URL = os.environ.get('DATABASE_URL', '')


def _use_postgres():
    return bool(DATABASE_URL)


def get_db():
    if _use_postgres():
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL,
                                cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _placeholder():
    return '%s' if _use_postgres() else '?'


def _autoincrement():
    return 'SERIAL PRIMARY KEY' if _use_postgres() else 'INTEGER PRIMARY KEY AUTOINCREMENT'


def _datetime_default():
    return 'DEFAULT NOW()' if _use_postgres() else "DEFAULT (datetime('now'))"


def init_db():
    conn = get_db()

    if _use_postgres():
        cur  = conn.cursor()
        _exec = cur.execute
    else:
        cur  = conn
        _exec = conn.execute

    ai = _autoincrement()
    dt = _datetime_default()

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

    _exec(f"""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            created_at TEXT {dt}
        )
    """)

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

    _exec(f"""
        CREATE TABLE IF NOT EXISTS delivery_slots (
            id         {ai},
            slot_date  TEXT NOT NULL UNIQUE,
            booked     INTEGER NOT NULL DEFAULT 0,
            max_slots  INTEGER NOT NULL DEFAULT 15,
            created_at TEXT {dt}
        )
    """)

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

    _exec(f"""
        CREATE TABLE IF NOT EXISTS newsletter (
            id         {ai},
            email      TEXT NOT NULL UNIQUE,
            created_at TEXT {dt}
        )
    """)

    # Migrations — safe on both SQLite and Postgres
    _safe_alter(conn, cur, "ALTER TABLE orders ADD COLUMN trello_card_id TEXT")
    _safe_alter(conn, cur, "ALTER TABLE orders ADD COLUMN delivery_date TEXT")
    _safe_alter(conn, cur, "ALTER TABLE orders ADD COLUMN payment_id TEXT")
    _safe_alter(conn, cur, "ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'pending'")

    conn.commit()
    conn.close()
    print(f"[DB] Initialised ({'PostgreSQL' if _use_postgres() else 'SQLite'})")


def _safe_alter(conn, cur, sql):
    try:
        if _use_postgres():
            cur.execute(sql)
            conn.commit()
        else:
            conn.execute(sql)
            conn.commit()
    except Exception:
        if _use_postgres():
            try: conn.rollback()
            except: pass
