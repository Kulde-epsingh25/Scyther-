#!/usr/bin/env python3
"""
database.py — Database initialisation and shared helpers
Scyther CLI Authentication & Authorisation Research Platform
"""

import os
import sqlite3
from datetime import datetime

DB_DIR  = os.path.join(os.path.dirname(__file__), "..", "database")
DB_PATH = os.path.join(DB_DIR, "users.db")


# ─────────────────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    """Return an open connection. Caller must close it."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL") # safer concurrent writes
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─────────────────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they do not exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db()
    cur  = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            username        TEXT PRIMARY KEY,
            password_hash   TEXT NOT NULL,
            role            TEXT NOT NULL DEFAULT 'user',
            approved        INTEGER NOT NULL DEFAULT 0,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked          INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS login_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL,
            status      TEXT    NOT NULL,
            timestamp   TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS blacklist (
            username       TEXT PRIMARY KEY,
            reason         TEXT,
            blacklisted_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
    """)

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────
# AUDIT LOGGING
# ─────────────────────────────────────────────────────────

def log_event(username: str, status: str) -> None:
    """Append a security event to login_logs."""
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO login_logs(username, status) VALUES(?, ?)",
            (username, status)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[DB] Log error: {e}")


# ─────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────

def get_stats() -> dict:
    """Return a dictionary of key database statistics."""
    init_db()
    conn = get_db()
    cur  = conn.cursor()

    stats = {}
    stats["total_users"]    = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    stats["approved"]       = cur.execute("SELECT COUNT(*) FROM users WHERE approved=1").fetchone()[0]
    stats["pending"]        = cur.execute("SELECT COUNT(*) FROM users WHERE approved=0").fetchone()[0]
    stats["locked"]         = cur.execute("SELECT COUNT(*) FROM users WHERE locked=1").fetchone()[0]
    stats["blacklisted"]    = cur.execute("SELECT COUNT(*) FROM blacklist").fetchone()[0]
    stats["total_logs"]     = cur.execute("SELECT COUNT(*) FROM login_logs").fetchone()[0]
    stats["failed_logins"]  = cur.execute(
        "SELECT COUNT(*) FROM login_logs WHERE status='FAILED_LOGIN'").fetchone()[0]
    stats["success_logins"] = cur.execute(
        "SELECT COUNT(*) FROM login_logs WHERE status='LOGIN_SUCCESS'").fetchone()[0]
    stats["locked_events"]  = cur.execute(
        "SELECT COUNT(*) FROM login_logs WHERE status='ACCOUNT_LOCKED'").fetchone()[0]

    conn.close()
    return stats


# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    stats = get_stats()
    print("\n=== Database Initialised ===")
    for k, v in stats.items():
        print(f"  {k:<20}: {v}")
    print()
