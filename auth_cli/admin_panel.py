#!/usr/bin/env python3
"""
admin_panel.py — Administrator control panel
Scyther CLI Authentication & Authorisation Research Platform
"""

import sqlite3
import sys

from database import get_db, init_db, log_event
from security  import hash_password, verify_password

# ─────────────────────────────────────────────────────────
# Admin credential — stored as SHA-256 hash (not plaintext)
# Default password: Admin@Scyther1  (change after first login)
# ─────────────────────────────────────────────────────────
ADMIN_HASH = hash_password("Admin@Scyther1")


# ─────────────────────────────────────────────────────────
# ADMIN LOGIN
# ─────────────────────────────────────────────────────────

def admin_login() -> None:
    print("\n╔══════════════════════════════╗")
    print("║       Admin Panel Login      ║")
    print("╚══════════════════════════════╝\n")

    password = input("  Admin password : ").strip()

    if not verify_password(password, ADMIN_HASH):
        print("\n  ❌ Access denied — incorrect admin password.\n")
        sys.exit(1)

    print("\n  ✅ Admin authenticated.\n")


# ─────────────────────────────────────────────────────────
# APPROVE USER
# ─────────────────────────────────────────────────────────

def approve_user() -> None:
    username = input("  Username to approve: ").strip()
    conn     = get_db()
    try:
        cur = conn.execute(
            "UPDATE users SET approved = 1 WHERE username = ?", (username,)
        )
        conn.commit()
        if cur.rowcount:
            print(f"\n  ✅ '{username}' approved successfully.\n")
            log_event(username, "ADMIN_APPROVED")
        else:
            print(f"\n  ❌ User '{username}' not found.\n")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# UNLOCK USER
# ─────────────────────────────────────────────────────────

def unlock_user() -> None:
    username = input("  Username to unlock: ").strip()
    conn     = get_db()
    try:
        cur = conn.execute(
            "UPDATE users SET locked = 0, failed_attempts = 0 WHERE username = ?",
            (username,)
        )
        conn.commit()
        if cur.rowcount:
            print(f"\n  ✅ '{username}' unlocked.\n")
            log_event(username, "ADMIN_UNLOCKED")
        else:
            print(f"\n  ❌ User '{username}' not found.\n")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# BLACKLIST USER
# ─────────────────────────────────────────────────────────

def blacklist_user() -> None:
    username = input("  Username to blacklist: ").strip()
    reason   = input("  Reason              : ").strip()
    conn     = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO blacklist(username, reason) VALUES(?, ?)",
            (username, reason)
        )
        conn.execute(
            "UPDATE users SET locked = 1 WHERE username = ?", (username,)
        )
        conn.commit()
        print(f"\n  ✅ '{username}' blacklisted and locked.\n")
        log_event(username, f"BLACKLISTED | {reason}")
    except sqlite3.Error as e:
        print(f"\n  ❌ Database error: {e}\n")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# REMOVE USER
# ─────────────────────────────────────────────────────────

def remove_user() -> None:
    username = input("  Username to remove: ").strip()
    confirm  = input(f"  Confirm removal of '{username}'? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("\n  ⚠  Cancelled.\n")
        return
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        if cur.rowcount:
            print(f"\n  ✅ '{username}' removed from system.\n")
            log_event(username, "ADMIN_REMOVED")
        else:
            print(f"\n  ❌ User '{username}' not found.\n")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# VIEW USERS — formatted table
# ─────────────────────────────────────────────────────────

def view_users() -> None:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT username, role, approved, locked, failed_attempts, created_at FROM users"
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("\n  No users registered yet.\n")
        return

    print("\n  ┌─────────────────────────────────────────────────────────────────────────┐")
    print(f"  │ {'Username':<18} {'Role':<8} {'Approved':<10} {'Locked':<8} {'Fails':<6} {'Created':<20} │")
    print("  ├─────────────────────────────────────────────────────────────────────────┤")
    for r in rows:
        approved = "✅ Yes" if r["approved"] else "⏳ No"
        locked   = "🔒 Yes" if r["locked"]   else "🟢 No"
        created  = str(r["created_at"])[:19]
        print(f"  │ {r['username']:<18} {r['role']:<8} {approved:<10} {locked:<8} {str(r['failed_attempts']):<6} {created:<20} │")
    print("  └─────────────────────────────────────────────────────────────────────────┘\n")


# ─────────────────────────────────────────────────────────
# VIEW LOGS — last 20 events
# ─────────────────────────────────────────────────────────

def view_logs() -> None:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT username, status, timestamp FROM login_logs ORDER BY rowid DESC LIMIT 20"
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("\n  No log entries yet.\n")
        return

    print("\n  ┌──────────────────────────────────────────────────────────────┐")
    print(f"  │ {'Username':<18} {'Event':<25} {'Timestamp':<20} │")
    print("  ├──────────────────────────────────────────────────────────────┤")
    for r in rows:
        ts = str(r["timestamp"])[:19]
        print(f"  │ {r['username']:<18} {r['status']:<25} {ts:<20} │")
    print("  └──────────────────────────────────────────────────────────────┘\n")


# ─────────────────────────────────────────────────────────
# MENU
# ─────────────────────────────────────────────────────────

def menu() -> str:
    print("  ┌─────────────────────────────┐")
    print("  │       Admin Panel           │")
    print("  ├─────────────────────────────┤")
    print("  │  1  Approve User            │")
    print("  │  2  Unlock User             │")
    print("  │  3  Blacklist User          │")
    print("  │  4  Remove User             │")
    print("  │  5  View All Users          │")
    print("  │  6  View Audit Logs         │")
    print("  │  7  Exit                    │")
    print("  └─────────────────────────────┘")
    return input("\n  Choice > ").strip()


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

def main() -> None:
    init_db()
    admin_login()

    actions = {
        "1": approve_user,
        "2": unlock_user,
        "3": blacklist_user,
        "4": remove_user,
        "5": view_users,
        "6": view_logs,
    }

    while True:
        choice = menu()
        if choice == "7":
            print("\n  Exiting admin panel.\n")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("\n  ❌ Invalid option.\n")


if __name__ == "__main__":
    main()
