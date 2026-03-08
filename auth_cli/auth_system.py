#!/usr/bin/env python3
"""
auth_system.py — User registration and login
Scyther CLI Authentication & Authorisation Research Platform
"""

import sqlite3
import sys
from datetime import datetime

from database import get_db, init_db, log_event
from security  import (
    hash_password, verify_password,
    password_strength, sanitise_username,
    is_rate_limited, reset_rate_limit,
)


# ─────────────────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────────────────

def register_user() -> None:

    print("\n╔══════════════════════════════╗")
    print("║      User Registration       ║")
    print("╚══════════════════════════════╝\n")

    raw_username = input("  Username : ").strip()
    try:
        username = sanitise_username(raw_username)
    except ValueError as e:
        print(f"\n  ❌ {e}\n")
        return

    password = input("  Password : ").strip()
    ok, msg  = password_strength(password)
    if not ok:
        print(f"\n  ❌ {msg}\n")
        return

    hashed = hash_password(password)
    init_db()
    conn   = get_db()

    try:
        conn.execute(
            """INSERT INTO users
               (username, password_hash, role, approved,
                failed_attempts, locked, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (username, hashed, "user", 0, 0, 0, str(datetime.now()))
        )
        conn.commit()
        print(f"\n  ✅ User '{username}' registered successfully.")
        print("  ⏳ Account is pending admin approval.\n")
        log_event(username, "REGISTERED")

    except sqlite3.IntegrityError:
        print(f"\n  ❌ Username '{username}' is already taken.\n")

    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────

def login_user() -> None:

    print("\n╔══════════════════════════════╗")
    print("║          User Login          ║")
    print("╚══════════════════════════════╝\n")

    username = input("  Username : ").strip()
    password = input("  Password : ").strip()

    if is_rate_limited(f"login:{username}"):
        print("\n  🔴 Too many attempts. Please wait 5 minutes.\n")
        log_event(username, "RATE_LIMITED")
        return

    init_db()
    conn = get_db()

    try:
        row = conn.execute(
            """SELECT password_hash, approved, failed_attempts, locked
               FROM users WHERE username = ?""",
            (username,)
        ).fetchone()

        if not row:
            print("\n  ❌ User not found.\n")
            return

        stored_hash = row["password_hash"]
        approved    = row["approved"]
        attempts    = row["failed_attempts"]
        locked      = row["locked"]

        if locked:
            print("\n  🔒 Account locked. Contact an administrator.\n")
            log_event(username, "ACCOUNT_LOCKED")
            return

        if not verify_password(password, stored_hash):
            attempts += 1
            conn.execute(
                "UPDATE users SET failed_attempts = ? WHERE username = ?",
                (attempts, username)
            )
            if attempts >= 5:
                conn.execute(
                    "UPDATE users SET locked = 1 WHERE username = ?", (username,)
                )
                conn.commit()
                print(f"\n  🔒 Account locked after {attempts} failed attempts.\n")
                log_event(username, "ACCOUNT_LOCKED")
            else:
                conn.commit()
                remaining = 5 - attempts
                print(f"\n  ❌ Wrong password. {remaining} attempt(s) remaining.\n")
                log_event(username, "FAILED_LOGIN")
            return

        if not approved:
            print("\n  ⏳ Account pending admin approval.\n")
            return

        conn.execute(
            "UPDATE users SET failed_attempts = 0 WHERE username = ?", (username,)
        )
        conn.commit()
        reset_rate_limit(f"login:{username}")
        print(f"\n  ✅ Welcome, {username}! Login successful.\n")
        log_event(username, "LOGIN_SUCCESS")

    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python3 auth_system.py register")
        print("  python3 auth_system.py login\n")
        return

    cmd = sys.argv[1].lower()

    if cmd == "register":
        register_user()
    elif cmd == "login":
        login_user()
    else:
        print(f"\n  ❌ Unknown command: '{cmd}'\n")


if __name__ == "__main__":
    main()
