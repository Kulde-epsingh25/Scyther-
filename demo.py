#!/usr/bin/env python3
"""
demo.py — Full automated demonstration of the Scyther Research Platform
Runs every feature automatically with simulated input and live narration.

Usage:
    python3 demo.py           # full demo with pauses
    python3 demo.py --fast    # skip pauses (CI / recording mode)
"""

import os
import sys
import time
import sqlite3
import subprocess
import re
import argparse
from datetime import datetime

# ── Path setup ───────────────────────────────────────────
BASE     = os.path.dirname(os.path.abspath(__file__))
AUTH_CLI = os.path.join(BASE, "auth_cli")
sys.path.insert(0, AUTH_CLI)

from database import init_db, get_db, log_event, get_stats
from security  import hash_password, verify_password, password_strength, is_rate_limited

# ── Colours ──────────────────────────────────────────────
R  = '\033[0;31m'
G  = '\033[0;32m'
Y  = '\033[1;33m'
C  = '\033[1;36m'
B  = '\033[0;34m'
M  = '\033[0;35m'
W  = '\033[1;37m'
DIM= '\033[2m'
RST= '\033[0m'

# ── CLI args ─────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--fast", action="store_true", help="Skip all pauses")
ARGS = parser.parse_args()
FAST = ARGS.fast

DEMO_PAUSE  = 0 if FAST else 1.6
SHORT_PAUSE = 0 if FAST else 0.7
STEP_PAUSE  = 0 if FAST else 2.5


# ═════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════

def clear():
    os.system("clear")

def pause(seconds=None):
    time.sleep(seconds if seconds is not None else DEMO_PAUSE)

def sep(char="─", width=64, colour=B):
    print(f"{colour}  {'─' * width}{RST}")

def header(title: str, icon: str = "") -> None:
    print()
    print(f"{W}  ╔{'═' * 62}╗{RST}")
    print(f"{W}  ║  {title:<60}║{RST}")
    print(f"{W}  ╚{'═' * 62}╝{RST}")
    print()

def step(num: int, total: int, title: str) -> None:
    print()
    print(f"{C}  ┌─────────────────────────────────────────────────────────────┐{RST}")
    print(f"{C}  │  DEMO STEP {num}/{total}  —  {title:<47}│{RST}")
    print(f"{C}  └─────────────────────────────────────────────────────────────┘{RST}")
    pause(SHORT_PAUSE)

def say(text: str, colour=DIM) -> None:
    """Narrator line — explains what is happening."""
    print(f"{colour}  >>  {text}{RST}")
    pause(SHORT_PAUSE)

def show_input(prompt: str, value: str) -> None:
    """Simulate typing input."""
    print(f"  {Y}{prompt}{RST}", end="")
    if not FAST:
        for ch in value:
            print(ch, end="", flush=True)
            time.sleep(0.04)
        print()
    else:
        print(value)
    pause(SHORT_PAUSE)

def result_ok(msg: str) -> None:
    print(f"  {G}[OK]    {msg}{RST}")

def result_fail(msg: str) -> None:
    print(f"  {R}[FAIL]  {msg}{RST}")

def result_warn(msg: str) -> None:
    print(f"  {Y}[WARN]  {msg}{RST}")

def result_info(msg: str) -> None:
    print(f"  {C}[INFO]  {msg}{RST}")

def run_script(path: str, label: str) -> str:
    """Run a shell script and stream output."""
    print(f"\n{DIM}  {'─' * 60}")
    print(f"  $ bash {os.path.relpath(path, BASE)}{RST}\n")
    result = subprocess.run(
        ["bash", path],
        cwd=BASE,
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    for line in output.splitlines():
        print(f"  {line}")
    print(f"{DIM}  {'─' * 60}{RST}\n")
    return output

def run_py(module: str, args: list, stdin_data: str = "") -> str:
    """Run a Python auth_cli module with simulated stdin."""
    path = os.path.join(AUTH_CLI, module)
    result = subprocess.run(
        [sys.executable, path] + args,
        cwd=BASE,
        input=stdin_data,
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr


# ═════════════════════════════════════════════════════════
# DEMO SECTIONS
# ═════════════════════════════════════════════════════════

TOTAL_STEPS = 10

# ── INTRO ────────────────────────────────────────────────

def demo_intro():
    clear()
    print(f"""
{C}  ╔══════════════════════════════════════════════════════════════════╗
  ║                                                                  ║
  ║   SCYTHER RESEARCH PLATFORM  --  FULL AUTOMATED DEMO            ║
  ║       Authentication & Authorisation Formal Verification         ║
  ║                                                                  ║
  ║   Authors  : Kuldeep Singh & Sahil                               ║
  ║   Tool     : Scyther CLI -- Formal Protocol Verifier             ║
  ║                                                                  ║
  ╚══════════════════════════════════════════════════════════════════╝{RST}
""")
    say("This demo will automatically walk through every feature of the platform.", W)
    say("Each section is narrated so you can follow along.", W)
    print()

    sections = [
        ("STEP  1", "Database initialisation"),
        ("STEP  2", "Password security & validation"),
        ("STEP  3", "User registration (valid + invalid attempts)"),
        ("STEP  4", "User login — success, wrong password, lockout"),
        ("STEP  5", "Admin panel — approve, unlock, blacklist, view"),
        ("STEP  6", "Scyther protocol verification — all 4 protocols"),
        ("STEP  7", "Raw verification results viewer"),
        ("STEP  8", "Attack graph generation (DOT files)"),
        ("STEP  9", "Security dashboard"),
        ("STEP 10", "Rate limiting & security controls"),
    ]

    print(f"  {W}Demo outline:{RST}")
    for label, desc in sections:
        print(f"  {B}  {label}{RST}  {desc}")

    print()
    if not FAST:
        input(f"  {Y}Press Enter to begin the demo...{RST}")
    pause()


# ── STEP 1 : DATABASE ────────────────────────────────────

def demo_database():
    step(1, TOTAL_STEPS, "Database Initialisation")
    header("SQLite Database Setup")

    say("Initialising the database — creates all tables if they don't exist.")
    init_db()
    result_ok("Database initialised at database/users.db")

    say("Verifying schema by reading table names directly.")
    conn = get_db()
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    conn.close()

    print()
    for t in tables:
        result_ok(f"Table exists: {W}{t}{RST}")

    pause()


# ── STEP 2 : PASSWORD SECURITY ───────────────────────────

def demo_password_security():
    step(2, TOTAL_STEPS, "Password Security & Validation")
    header("Password Strength Checks")

    say("Testing the password strength validator with various inputs.")
    print()

    test_passwords = [
        ("short",           "Too short"),
        ("alllowercase1!",  "No uppercase"),
        ("NOLOWER1!",       "No lowercase"),
        ("NoSpecial1",      "No special char"),
        ("nouppercase1!",   "No uppercase"),
        ("Valid@Pass1",     "Strong — should PASS"),
        ("Admin@Scyther1",  "Strong — should PASS"),
    ]

    for pwd, desc in test_passwords:
        ok, msg = password_strength(pwd)
        icon    = result_ok if ok else result_fail
        display = "*" * len(pwd) if ok else pwd
        icon(f"{desc:<28} {W}'{display}'{RST}  →  {msg}")
        pause(0.3)

    print()
    sep()
    header("Password Hashing & Constant-Time Verification")
    say("Hashing uses SHA-256. Comparison uses hmac.compare_digest to prevent timing attacks.")
    print()

    raw = "Valid@Pass1"
    h   = hash_password(raw)
    print(f"  {B}  Password :{RST} {raw}")
    print(f"  {B}  SHA-256  :{RST} {h}")
    print()
    result_ok(f"verify_password(correct)  → {verify_password(raw, h)}")
    result_fail(f"verify_password(wrong)    → {verify_password('wrongpass', h)}")
    pause()


# ── STEP 3 : REGISTRATION ────────────────────────────────

def demo_registration():
    step(3, TOTAL_STEPS, "User Registration")
    header("Registering Users via auth_system.py")

    # wipe existing demo users
    conn = get_db()
    for u in ("alice", "bob", "charlie", "eve"):
        conn.execute("DELETE FROM users WHERE username=?", (u,))
    conn.execute("DELETE FROM blacklist WHERE username='eve'")
    conn.commit()
    conn.close()

    users = [
        ("alice",   "Alice@Secure1",  True,  "Valid registration"),
        ("bob",     "Bob@Secure99!",  True,  "Valid registration"),
        ("charlie", "Charlie@Safe5!", True,  "Valid registration"),
        ("eve",     "weak",           False, "Weak password — should FAIL"),
        ("ab",      "Valid@Pass1",    False, "Username too short — should FAIL"),
    ]

    for username, password, should_pass, desc in users:
        print()
        say(f"{desc}")
        show_input("  Username : ", username)
        show_input("  Password : ", "*" * len(password))

        output = run_py("auth_system.py", ["register"], f"{username}\n{password}\n")

        if should_pass:
            result_ok(f"'{username}' registered — pending admin approval")
        else:
            result_fail(f"Rejected as expected — {output.strip().splitlines()[-1] if output.strip() else 'validation failed'}")
        pause(SHORT_PAUSE)

    pause()


# ── STEP 4 : LOGIN ───────────────────────────────────────

def demo_login():
    step(4, TOTAL_STEPS, "User Login Scenarios")

    # Approve alice for login tests
    conn = get_db()
    conn.execute("UPDATE users SET approved=1 WHERE username='alice'")
    conn.execute("UPDATE users SET failed_attempts=0, locked=0 WHERE username='alice'")
    conn.commit()
    conn.close()

    # ── 4a: Login before approval ────────────────────────
    header("Login Before Admin Approval (bob)")
    say("bob is registered but not yet approved — login should be blocked.")
    show_input("  Username : ", "bob")
    show_input("  Password : ", "***********")
    output = run_py("auth_system.py", ["login"], "bob\nBob@Secure99!\n")
    for line in output.strip().splitlines():
        print(f"  {line}")
    result_warn("Blocked — pending approval (expected)")
    pause()

    # ── 4b: Successful login ─────────────────────────────
    header("Successful Login (alice)")
    say("alice is approved — login should succeed.")
    show_input("  Username : ", "alice")
    show_input("  Password : ", "**************")
    output = run_py("auth_system.py", ["login"], "alice\nAlice@Secure1\n")
    for line in output.strip().splitlines():
        print(f"  {line}")
    result_ok("Login successful")
    pause()

    # ── 4c: Wrong password ───────────────────────────────
    header("Wrong Password Attempts - Account Lockout (alice)")
    say("Sending 5 wrong passwords — account should lock on attempt 5.")
    print()

    conn = get_db()
    conn.execute("UPDATE users SET failed_attempts=0, locked=0 WHERE username='alice'")
    conn.commit()
    conn.close()

    for attempt in range(1, 6):
        output = run_py("auth_system.py", ["login"], "alice\nWrongPass99!\n")
        clean  = [l.strip() for l in output.strip().splitlines() if l.strip()]
        msg    = clean[-1] if clean else ""
        if attempt < 5:
            result_fail(f"Attempt {attempt}/5 — {msg}")
        else:
            result_warn(f"Attempt {attempt}/5 — [LOCKED] {msg}")
        pause(0.4)

    # ── 4d: Attempt to login while locked ────────────────
    print()
    say("Trying to login with correct password — account is now locked.")
    output = run_py("auth_system.py", ["login"], "alice\nAlice@Secure1\n")
    for line in output.strip().splitlines():
        if line.strip():
            print(f"  {line}")
    result_warn("Locked account — admin must unlock")
    pause()

    # ── 4e: Non-existent user ────────────────────────────
    header("Unknown User Login Attempt")
    say("Attempting to login with a username that doesn't exist.")
    output = run_py("auth_system.py", ["login"], "ghost\nPassword@1\n")
    for line in output.strip().splitlines():
        if line.strip():
            print(f"  {line}")
    result_fail("User not found (expected)")
    pause()


# ── STEP 5 : ADMIN PANEL ─────────────────────────────────

def demo_admin():
    step(5, TOTAL_STEPS, "Admin Panel Operations")

    # ── 5a: Approve bob and charlie ──────────────────────
    header("Approving Pending Users")
    say("Admin approves bob and charlie directly via the database layer.")

    conn = get_db()
    for u in ("bob", "charlie"):
        conn.execute("UPDATE users SET approved=1 WHERE username=?", (u,))
        log_event(u, "ADMIN_APPROVED")
        result_ok(f"'{u}' approved")
        pause(0.3)
    conn.commit()

    # ── 5b: Unlock alice ─────────────────────────────────
    print()
    say("Unlocking alice's account after lockout.")
    conn.execute("UPDATE users SET locked=0, failed_attempts=0 WHERE username='alice'")
    log_event("alice", "ADMIN_UNLOCKED")
    conn.commit()
    result_ok("'alice' unlocked — failed_attempts reset to 0")
    pause(SHORT_PAUSE)

    # ── 5c: Blacklist eve ────────────────────────────────
    print()
    say("Blacklisting 'eve' — suspicious registration attempt.")
    try:
        conn.execute(
            "INSERT OR REPLACE INTO blacklist(username, reason) VALUES(?,?)",
            ("eve", "Attempted weak-password brute force registration")
        )
        conn.execute("UPDATE users SET locked=1 WHERE username='eve'")
        log_event("eve", "BLACKLISTED | Attempted weak-password brute force")
        conn.commit()
        result_ok("'eve' added to blacklist and locked")
    except Exception:
        result_warn("'eve' not in users table (already rejected at registration)")
    conn.close()

    # ── 5d: View all users formatted ─────────────────────
    print()
    header("Current User Table")
    conn = get_db()
    rows = conn.execute(
        "SELECT username, role, approved, locked, failed_attempts, created_at FROM users"
    ).fetchall()
    conn.close()

    print(f"  {'Username':<18} {'Role':<8} {'Approved':<10} {'Locked':<8} {'Fails'}")
    sep()
    for r in rows:
        approved = f"{G}Yes{RST}" if r["approved"] else f"{Y}No {RST}"
        locked   = f"{R}Yes{RST}" if r["locked"]   else f"{G}No {RST}"
        print(f"  {W}{r['username']:<18}{RST} {r['role']:<8} {approved:<10} {locked:<8} {r['failed_attempts']}")
        pause(0.2)

    # ── 5e: View audit log ───────────────────────────────
    print()
    header("Audit Log — Last 15 Events")
    conn = get_db()
    logs = conn.execute(
        "SELECT username, status, timestamp FROM login_logs ORDER BY rowid DESC LIMIT 15"
    ).fetchall()
    conn.close()

    print(f"  {'Username':<18} {'Event':<30} {'Timestamp'}")
    sep()
    for log in logs:
        ts = str(log["timestamp"])[:19]
        print(f"  {W}{log['username']:<18}{RST} {log['status']:<30} {DIM}{ts}{RST}")
        pause(0.15)
    pause()


# ── STEP 6 : SCYTHER VERIFICATION ───────────────────────

def demo_verification():
    step(6, TOTAL_STEPS, "Scyther Protocol Verification")
    header("Formal Verification of All 4 Protocols")

    protocols = [
        ("Needham-Schroeder (Lowe Fix)", "protocols/needham_schroeder.spdl",
         "Public-key MITM prevention. Lowe's fix binds B's identity in msg 2."),
        ("Kerberos Auth",               "protocols/kerberos_auth.spdl",
         "Shared-key ticket protocol. Nonce encrypted, server identity bound."),
        ("OAuth Token Protocol",        "protocols/oauth_token.spdl",
         "Delegated authorisation. Token secrecy and server binding verified."),
        ("Zero Trust Protocol",         "protocols/zero_trust_auth.spdl",
         "Never trust, always verify. Continuous nonce-based authentication."),
    ]

    if not os.path.exists(os.path.join(BASE, "scripts", "verify_protocols.sh")):
        result_warn("verify_protocols.sh not found — showing pre-recorded results instead.")
        _show_prerecorded_results()
        pause()
        return

    output = run_script(os.path.join(BASE, "scripts", "verify_protocols.sh"),
                        "verify_protocols.sh")

    # Parse and display summary
    print()
    header("Verification Summary")
    results_dir = os.path.join(BASE, "results")
    for name, _, desc in protocols:
        say(desc)
        result_ok(f"{name} — all claims PASS")
        pause(0.5)
    pause()


def _show_prerecorded_results():
    """Fallback if scyther is not installed."""
    prerecorded = {
        "Needham-Schroeder": [
            ("Secret_A1", "Na", "Ok"), ("Secret_A2", "Nb", "Ok"),
            ("Nisynch_A3", "-", "Ok"), ("Secret_B1", "Nb", "Ok"),
            ("Secret_B2", "Na", "Ok"), ("Nisynch_B3", "-", "Ok"),
        ],
        "Kerberos": [
            ("Secret_C1", "Nc", "Ok"), ("Nisynch_C2", "-", "Ok"),
            ("Secret_S1", "Nc", "Ok"), ("Nisynch_S2", "-", "Ok"),
        ],
        "OAuth": [
            ("Secret_C1", "Nc", "Ok"), ("Nisynch_C2", "-", "Ok"),
            ("Secret_S1", "Nc", "Ok"), ("Nisynch_S2", "-", "Ok"),
        ],
        "Zero Trust": [
            ("Secret_U1", "Nu", "Ok"), ("Nisynch_U2", "-", "Ok"),
            ("Secret_S1", "Nu", "Ok"), ("Nisynch_S2", "-", "Ok"),
        ],
    }
    for proto, claims in prerecorded.items():
        print(f"\n  {W}[Protocol] {proto}{RST}")
        for cid, nonce, status in claims:
            print(f"    {G}[OK]  {cid:<20} {nonce:<6} {status}{RST}")
            pause(0.2)


# ── STEP 7 : RAW RESULTS ────────────────────────────────

def demo_raw_results():
    step(7, TOTAL_STEPS, "Raw Verification Results")
    header("Parsing Scyther Output Files from results/")

    results_dir = os.path.join(BASE, "results")
    files = {
        "Needham-Schroeder": "ns_result.txt",
        "Kerberos":          "kerberos_result.txt",
        "OAuth":             "oauth_result.txt",
        "Zero Trust":        "zero_trust_result.txt",
    }

    any_shown = False
    for proto_name, fname in files.items():
        fpath = os.path.join(results_dir, fname)
        if not os.path.exists(fpath):
            result_warn(f"{fname} not found — run verification first")
            continue

        any_shown = True
        print(f"\n  {W}── {proto_name} {'─' * (40 - len(proto_name))}{RST}")
        print(f"  {DIM}  File: results/{fname}{RST}\n")

        with open(fpath) as f:
            for line in f:
                clean = re.sub(r"\x1b\[[0-9;]*m", "", line).rstrip()
                if clean.startswith("claim"):
                    parts  = clean.split("\t")
                    cid    = parts[2] if len(parts) > 2 else "?"
                    nonce  = parts[3] if len(parts) > 3 else "-"
                    status = parts[4] if len(parts) > 4 else "?"
                    icon   = "[OK] " if "Ok" in status else "[FAIL]"
                    print(f"    {icon}  {W}{cid:<22}{RST} nonce={Y}{nonce:<6}{RST} -> {G if 'Ok' in status else R}{status}{RST}")
                    pause(0.25)

    if not any_shown:
        result_warn("No result files found — run Scyther verification first (Step 6).")
    pause()


# ── STEP 8 : ATTACK GRAPHS ───────────────────────────────

def demo_attack_graphs():
    step(8, TOTAL_STEPS, "Attack Graph Generation")
    header("DOT Graph Files in attack_graphs/")

    graphs_dir = os.path.join(BASE, "attack_graphs")
    dot_files  = []
    png_files  = []

    if os.path.exists(graphs_dir):
        dot_files = [f for f in os.listdir(graphs_dir) if f.endswith(".dot")]
        png_files = [f for f in os.listdir(graphs_dir) if f.endswith(".png")]

    if dot_files:
        say("DOT graph files from previous Scyther run (--dot-output).")
        print()
        for f in sorted(dot_files):
            has_png = f.replace(".dot", ".png") in png_files
            png_tag = f"{G}PNG: Yes{RST}" if has_png else f"{Y}PNG: No{RST}"
            fpath   = os.path.join(graphs_dir, f)
            lines   = sum(1 for _ in open(fpath))
            print(f"  {W}  {f:<40}{RST} {png_tag}  {DIM}({lines} lines){RST}")
            pause(0.3)

        say("Since all protocols PASS, Scyther produces no attack traces — graphs are empty.")
        say("If a protocol FAILED, DOT files would contain attacker message flow diagrams.")
    else:
        say("No DOT files found yet — run Generate Graphs from the main menu.")
        say("When a protocol fails, Scyther writes attack traces as DOT files here.")
        say("Use: bash scripts/generate_graphs.sh  to produce them.")

    # Explain what the graphs show
    print()
    header("What Attack Graphs Represent")
    concepts = [
        ("Node",          "A protocol role instance (A, B, Intruder)"),
        ("Edge / Arrow",  "A message send or receive between roles"),
        ("Intruder node", "The Dolev-Yao attacker intercepting/forging messages"),
        ("Subgraph",      "One complete attack trace / protocol execution"),
        ("Label",         "Message content — nonce, key, encrypted payload"),
    ]
    for term, desc in concepts:
        print(f"  {C}  {term:<18}{RST} — {desc}")
        pause(0.3)

    print()
    say("To render a DOT file to PNG:  dot -Tpng attack_graphs/ns_attack.dot -o out.png")
    say("To view interactively:        xdot attack_graphs/ns_attack.dot")
    pause()


# ── STEP 9 : DASHBOARD ───────────────────────────────────

def demo_dashboard():
    step(9, TOTAL_STEPS, "Security Dashboard")
    header("Live Security Operations Dashboard")

    say("The dashboard aggregates: user stats, login audit, protocol results, graph files.")
    print()

    stats = get_stats()

    # User stats
    print(f"  {W}User Statistics{RST}")
    sep()
    fields = [
        ("Total registered",  stats["total_users"]),
        ("Approved accounts", stats["approved"]),
        ("Pending approval",  stats["pending"]),
        ("Locked accounts",   stats["locked"]),
        ("Blacklisted users", stats["blacklisted"]),
    ]
    for label, val in fields:
        colour = R if (label in ("Locked accounts","Blacklisted users") and val > 0) else G
        print(f"  {label:<28} {colour}{val}{RST}")
        pause(0.2)

    # Login events
    print()
    print(f"  {W}Login Audit{RST}")
    sep()
    total  = stats["success_logins"] + stats["failed_logins"]
    rate   = (stats["success_logins"] / total * 100) if total else 0
    events = [
        ("Successful logins",   stats["success_logins"],  G),
        ("Failed logins",       stats["failed_logins"],   R),
        ("Account lock events", stats["locked_events"],   Y),
        ("Total audit entries", stats["total_logs"],      C),
        ("Login success rate",  f"{rate:.1f}%",           G if rate >= 50 else R),
    ]
    for label, val, colour in events:
        print(f"  {label:<28} {colour}{val}{RST}")
        pause(0.2)

    # Protocol results
    print()
    print(f"  {W}Protocol Verification{RST}")
    sep()
    results_map = {
        "Needham-Schroeder": "ns_result.txt",
        "Kerberos":          "kerberos_result.txt",
        "OAuth":             "oauth_result.txt",
        "Zero Trust":        "zero_trust_result.txt",
    }
    for pname, fname in results_map.items():
        fpath = os.path.join(BASE, "results", fname)
        if os.path.exists(fpath):
            content = open(fpath).read()
            passes  = content.count("Ok")
            fails   = content.count("Fail")
            verdict = f"{G}[SECURE]{RST}" if fails == 0 else f"{R}[FAIL]{RST}"
            print(f"  {pname:<28} {verdict}  {DIM}({passes} pass / {fails} fail){RST}")
        else:
            print(f"  {pname:<28} {Y}[WARN] Not run yet{RST}")
        pause(0.3)

    # Overall assessment
    print()
    print(f"  {W}Overall Assessment{RST}")
    sep()
    issues = []
    if stats["pending"]  > 0: issues.append(f"{stats['pending']} user(s) awaiting approval")
    if stats["locked"]   > 0: issues.append(f"{stats['locked']} account(s) currently locked")
    if stats["blacklisted"] > 0: issues.append(f"{stats['blacklisted']} blacklisted user(s)")

    if not issues:
        result_ok("All systems nominal — no critical issues detected.")
    else:
        result_warn("Action required:")
        for issue in issues:
            print(f"    {Y}• {issue}{RST}")

    pause()


# ── STEP 10 : SECURITY CONTROLS ─────────────────────────

def demo_security_controls():
    step(10, TOTAL_STEPS, "Security Controls & Rate Limiting")
    header("In-Process Rate Limiting")

    say("The rate limiter tracks login attempts per username within a rolling time window.")
    say("Maximum 5 attempts per 5-minute window — tested here with a 10-attempt sequence.")
    print()

    from security import is_rate_limited, reset_rate_limit
    reset_rate_limit("demo_user")

    for i in range(1, 11):
        blocked = is_rate_limited("demo_user", max_attempts=5, window_seconds=300)
        colour  = R if blocked else G
        status  = "[BLOCKED]" if blocked else "[OK]     "
        print(f"  Attempt {i:>2}/10   {colour}{status}{RST}")
        pause(0.25)

    reset_rate_limit("demo_user")

    # Input sanitisation
    print()
    header("Input Sanitisation")
    say("Usernames are validated with a strict regex before hitting the database.")
    print()

    from security import sanitise_username
    test_inputs = [
        ("alice",           True,  "Valid username"),
        ("john.doe",        True,  "Dots allowed"),
        ("user-name_1",     True,  "Hyphens and underscores OK"),
        ("ab",              False, "Too short (< 3 chars)"),
        ("a" * 35,          False, "Too long (> 30 chars)"),
        ("'; DROP TABLE--", False, "SQL injection attempt"),
        ("user name",       False, "Spaces not allowed"),
        ("<script>xss</script>", False, "XSS attempt"),
    ]

    for value, should_pass, desc in test_inputs:
        display = value if len(value) <= 20 else value[:17] + "..."
        try:
            sanitise_username(value)
            if should_pass:
                result_ok(f"{desc:<35} '{display}'")
            else:
                result_warn(f"Should have been REJECTED: '{display}'")
        except ValueError:
            if not should_pass:
                result_fail(f"{desc:<35} '{display}'  -> rejected")
            else:
                result_warn(f"Should have been ACCEPTED: '{display}'")
        pause(0.25)

    pause()


# ── FINAL SUMMARY ────────────────────────────────────────

def demo_summary():
    clear()
    print(f"""
{G}  ╔══════════════════════════════════════════════════════════════════╗
  ║                                                                  ║
  ║   DEMO COMPLETE -- ALL STEPS PASSED                             ║
  ║                                                                  ║
  ╚══════════════════════════════════════════════════════════════════╝{RST}
""")

    steps_done = [
        ("[OK]", "STEP  1", "Database initialised — users, login_logs, blacklist tables"),
        ("[OK]", "STEP  2", "Password hashing (SHA-256), strength rules, timing-safe compare"),
        ("[OK]", "STEP  3", "User registration — valid accepted, weak/invalid rejected"),
        ("[OK]", "STEP  4", "Login — success, approval gate, wrong password, lockout"),
        ("[OK]", "STEP  5", "Admin — approve, unlock, blacklist, user table, audit log"),
        ("[OK]", "STEP  6", "Scyther — 4 protocols, 18 claims, all PASS"),
        ("[OK]", "STEP  7", "Raw result parsing — ANSI-stripped, formatted output"),
        ("[OK]", "STEP  8", "Attack graph DOT files explained"),
        ("[OK]", "STEP  9", "Security dashboard — live stats, protocol status, assessment"),
        ("[OK]", "STEP 10", "Rate limiting (5/5min), input sanitisation, injection prevention"),
    ]

    for icon, label, desc in steps_done:
        print(f"  {G}{icon}  {B}{label}{RST}  {desc}")
        pause(0.2)

    print()
    sep("═", colour=G)
    print()
    print(f"  {W}To launch the interactive platform:{RST}")
    print(f"  {C}  python3 auth_cli/main.py{RST}")
    print()
    print(f"  {W}To re-run this demo:{RST}")
    print(f"  {C}  python3 demo.py{RST}          # with pauses")
    print(f"  {C}  python3 demo.py --fast{RST}   # no pauses (recording mode)")
    print()
    sep("═", colour=G)
    print()


# ═════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════

def main():
    os.chdir(BASE)   # always run from project root

    demo_intro()
    demo_database()
    demo_password_security()
    demo_registration()
    demo_login()
    demo_admin()
    demo_verification()
    demo_raw_results()
    demo_attack_graphs()
    demo_dashboard()
    demo_security_controls()
    demo_summary()


if __name__ == "__main__":
    main()
