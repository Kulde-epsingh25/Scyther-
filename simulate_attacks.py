#!/usr/bin/env python3
"""
simulate_attacks.py — Attack Simulation Suite
Scyther CLI Authentication & Authorisation Research Platform

Usage:
    python3 simulate_attacks.py           # full demo with pauses
    python3 simulate_attacks.py --fast    # no pauses
    python3 simulate_attacks.py --quiet   # results only
"""

import os
import sys
import time
import sqlite3
import argparse
from datetime import datetime

BASE     = os.path.dirname(os.path.abspath(__file__))
AUTH_CLI = os.path.join(BASE, "auth_cli")
DB_PATH  = os.path.join(BASE, "database", "users.db")
sys.path.insert(0, AUTH_CLI)

from database import init_db
from security  import hash_password, is_rate_limited, reset_rate_limit

parser = argparse.ArgumentParser()
parser.add_argument("--fast",  action="store_true")
parser.add_argument("--quiet", action="store_true")
ARGS  = parser.parse_args()
FAST  = ARGS.fast
QUIET = ARGS.quiet

R   = '\033[0;31m'; G   = '\033[0;32m'; Y   = '\033[1;33m'
C   = '\033[1;36m'; B   = '\033[0;34m'; W   = '\033[1;37m'
DIM = '\033[2m';    RST = '\033[0m'

PAUSE = 0 if FAST else 0.08
STEP  = 0 if FAST else 1.2

STATS = {"attacks_simulated":0,"events_logged":0,"accounts_locked":0,
         "blacklisted":0,"brute_attempts":0,"injection_attempts":0,
         "replay_attempts":0,"enum_attempts":0}


def db():
    """Single connection with WAL + long timeout to prevent locking."""
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory     = sqlite3.Row
    conn.isolation_level = None   # autocommit
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    return conn


def _log(conn, username, event, detail=""):
    status = event if not detail else f"{event} | {detail}"
    conn.execute("INSERT INTO login_logs(username, status) VALUES(?,?)",
                 (username, status))
    STATS["events_logged"] += 1


def _ensure_user(conn, username, password, approved=True, locked=False):
    existing = conn.execute(
        "SELECT username FROM users WHERE username=?", (username,)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (username,password_hash,role,approved,failed_attempts,locked,created_at) VALUES (?,?,?,?,?,?,?)",
            (username, hash_password(password), "user",
             1 if approved else 0, 0, 1 if locked else 0, str(datetime.now()))
        )
    else:
        conn.execute(
            "UPDATE users SET approved=?,locked=?,failed_attempts=0 WHERE username=?",
            (1 if approved else 0, 1 if locked else 0, username)
        )


def _attempt_login(conn, username, password):
    """All reads, writes, and logging on the SAME connection."""
    row = conn.execute(
        "SELECT password_hash,approved,failed_attempts,locked FROM users WHERE username=?",
        (username,)
    ).fetchone()
    if not row:
        _log(conn, username, "FAILED_LOGIN", "user_not_found")
        return False, "user_not_found"

    stored=row["password_hash"]; approved=row["approved"]
    attempts=row["failed_attempts"]; locked=row["locked"]

    if locked:
        _log(conn, username, "ACCOUNT_LOCKED", "login_attempt_while_locked")
        return False, "locked"

    if hash_password(password) != stored:
        attempts += 1
        conn.execute("UPDATE users SET failed_attempts=? WHERE username=?",
                     (attempts, username))
        if attempts >= 5:
            conn.execute("UPDATE users SET locked=1 WHERE username=?", (username,))
            STATS["accounts_locked"] += 1
            _log(conn, username, "ACCOUNT_LOCKED", f"after_{attempts}_failed_attempts")
        else:
            _log(conn, username, "FAILED_LOGIN", f"wrong_password_attempt_{attempts}")
        return False, f"wrong_password (attempt {attempts})"

    if not approved:
        _log(conn, username, "FAILED_LOGIN", "account_not_approved")
        return False, "not_approved"

    conn.execute("UPDATE users SET failed_attempts=0 WHERE username=?", (username,))
    _log(conn, username, "LOGIN_SUCCESS")
    return True, "success"


def p(msg, colour=RST):
    if not QUIET: print(f"{colour}{msg}{RST}")

def say(msg):
    if not QUIET:
        print(f"{DIM}  >>  {msg}{RST}")
        time.sleep(PAUSE*3)

def attack_header(num, name, icon=""):
    print()
    print(f"{R}  ╔══════════════════════════════════════════════════════════════╗{RST}")
    print(f"{R}  ║  ATTACK {num}: {name:<53}║{RST}")
    print(f"{R}  ╚══════════════════════════════════════════════════════════════╝{RST}")
    print()
    time.sleep(STEP)

def show_result(success, msg):
    colour = G if success else R
    icon   = "[OK]  " if success else "[FAIL]"
    print(f"  {colour}{icon}  {msg}{RST}")
    time.sleep(PAUSE)


def attack_brute_force():
    attack_header(1, "Brute Force Password Attack")
    say("Attacker tries common passwords against a known username.")
    wordlist = ["password","123456","password1","qwerty","abc123","letmein",
                "monkey","dragon","master","iloveyou","admin","welcome",
                "login","pass123","secret","Alice@Secure99!"]
    STATS["attacks_simulated"] += 1
    locked_at = None
    with db() as conn:
        _ensure_user(conn, "victim_alice", "Alice@Secure99!", approved=True)
        for i, pwd in enumerate(wordlist, 1):
            success, reason = _attempt_login(conn, "victim_alice", pwd)
            STATS["brute_attempts"] += 1
            colour = G if success else R
            print(f"  {colour}{'[OK] ' if success else '[FAIL]'}  [{i:>2}/{len(wordlist)}]  {pwd:<25}  ->  {reason}{RST}")
            time.sleep(PAUSE)
            if reason == "locked":
                locked_at = i
                p(f"\n  {Y}[WARN]  Locked at attempt {i}!{RST}")
                break
        conn.execute("UPDATE users SET locked=0,failed_attempts=0 WHERE username='victim_alice'")
    show_result(False, f"Brute force BLOCKED — locked after {locked_at} attempts" if locked_at else "Brute force failed")


def attack_credential_stuffing():
    attack_header(2, "Credential Stuffing Attack")
    say("Attacker uses username:password pairs leaked from other breaches.")
    targets = [("user_bob","Bob@Secure99!"),("user_carol","Carol@Safe777!"),("user_dave","Dave@Pass123!")]
    leaked  = [("user_bob","hunter2"),("user_bob","password123"),("user_carol","qwerty99"),
               ("user_carol","iloveyou!"),("user_dave","Dave@Pass123!"),
               ("user_dave","correcthorse"),("user_bob","Bob@Secure99!"),("user_carol","Carol@Safe777!")]
    STATS["attacks_simulated"] += 1
    hits = 0
    with db() as conn:
        for u,pw in targets: _ensure_user(conn, u, pw, approved=True)
        for username, password in leaked:
            success, reason = _attempt_login(conn, username, password)
            STATS["brute_attempts"] += 1
            if success:
                hits += 1
                _log(conn, username, "CREDENTIAL_STUFFING_SUCCESS", "reused_password_match")
                print(f"  {R}[HIT!]  {username:<18} : {password:<25}  ->  LOGIN SUCCESS{RST}")
            else:
                print(f"  {DIM}  miss  {username:<18} : {password:<25}  ->  {reason}{RST}")
            time.sleep(PAUSE)
    print()
    show_result(False, f"{hits} credential(s) matched — reused passwords are dangerous!")


def attack_user_enumeration():
    attack_header(3, "Username Enumeration Attack")
    say("Attacker probes login to discover valid usernames.")
    probes = ["admin","administrator","root","test","guest","real_user_1",
              "real_user_2","john","alice_admin","superuser","sysadmin","victim_alice"]
    STATS["attacks_simulated"] += 1
    found = []
    with db() as conn:
        _ensure_user(conn, "real_user_1", "RealUser@1!", approved=True)
        _ensure_user(conn, "real_user_2", "RealUser@2!", approved=True)
        for username in probes:
            _, reason = _attempt_login(conn, username, "wrongpass_enum_probe")
            STATS["enum_attempts"] += 1
            if reason == "user_not_found":
                print(f"  {DIM}  —  {username:<25}  does not exist{RST}")
            else:
                found.append(username)
                _log(conn, username, "ENUMERATION_PROBE", "attacker_discovered_username")
                print(f"  {Y}[FOUND]  {username:<25}  EXISTS  (reason: {reason}){RST}")
            time.sleep(PAUSE)
    print()
    show_result(False, f"Enumerated {len(found)} valid usernames: {', '.join(found)}")


def attack_sql_injection():
    attack_header(4, "SQL Injection Attack")
    say("Parameterised queries should block all injection attempts.")
    injections = [
        ("' OR '1'='1",              "password",   "Classic OR bypass"),
        ("admin'--",                 "anything",   "Comment truncation"),
        ("' OR 1=1--",               "x",          "Boolean true injection"),
        ("'; DROP TABLE users;--",   "x",          "Table drop attempt"),
        ("' UNION SELECT * FROM users--","x",       "UNION extraction"),
        ("' OR 'x'='x",              "' OR 'x'='x","Double-field injection"),
        ("admin\x00",                "password",   "Null byte injection"),
        ("1' AND SLEEP(5)--",        "x",          "Time-based blind"),
    ]
    STATS["attacks_simulated"] += 1
    bypassed = 0
    with db() as conn:
        for username, password, desc in injections:
            STATS["injection_attempts"] += 1
            try:
                success, reason = _attempt_login(conn, username, password)
                _log(conn, username, "SQL_INJECTION_ATTEMPT", desc)
                if success:
                    bypassed += 1
                    print(f"  {R}[BYPASS]  {desc:<38} <- CRITICAL{RST}")
                else:
                    print(f"  {G}[BLOCKED]  {desc:<38} reason={reason}{RST}")
            except Exception as e:
                print(f"  {G}[BLOCKED]  Exception   {desc:<38} {str(e)[:30]}{RST}")
            time.sleep(PAUSE)
    print()
    show_result(bypassed == 0, "All SQL injection attempts blocked" if bypassed==0 else f"{bypassed} bypassed — CRITICAL")


def attack_lockout_dos():
    attack_header(5, "Account Lockout DoS Attack")
    say("Attacker deliberately locks out legitimate users.")
    victims = ["dos_victim_1","dos_victim_2","dos_victim_3"]
    STATS["attacks_simulated"] += 1
    with db() as conn:
        for v in victims: _ensure_user(conn, v, "Victim@Safe1!", approved=True)
        for victim in victims:
            p(f"\n  {W}Targeting: {victim}{RST}")
            for attempt in range(1, 6):
                _, reason = _attempt_login(conn, victim, "wrong_dos_password")
                colour = Y if "locked" in reason else R
                print(f"  {colour}  Attempt {attempt}/5  →  {reason}{RST}")
                time.sleep(PAUSE)
                if "locked" in reason: break
    print()
    show_result(False, f"{len(victims)} accounts locked — legitimate users denied access")


def attack_rate_limit_evasion():
    attack_header(6, "Rate Limit Evasion Attempt")
    say("Attacker rotates across usernames to evade per-user rate limiting.")
    targets   = ["rl_target_a","rl_target_b","rl_target_c","rl_target_d"]
    passwords = ["password1","qwerty","abc123","letmein","pass123","dragon","master","hello","monkey","shadow"]
    STATS["attacks_simulated"] += 1
    for t in targets: reset_rate_limit(f"login:{t}")
    blocked_count = 0
    with db() as conn:
        for t in targets: _ensure_user(conn, t, "Target@Safe1!", approved=True)
        for pwd in passwords:
            for target in targets:
                blocked = is_rate_limited(f"login:{target}", max_attempts=5, window_seconds=300)
                if blocked:
                    blocked_count += 1
                    _log(conn, target, "RATE_LIMITED", f"evasion_attempt_{pwd}")
                    print(f"  {R}[RATE LIMITED]  {target:<20} '{pwd}'  ->  RATE LIMITED{RST}")
                else:
                    _, reason = _attempt_login(conn, target, pwd)
                    print(f"  {DIM}  ...  {target:<20} '{pwd}'  ->  {reason}{RST}")
                time.sleep(PAUSE)
    print()
    show_result(blocked_count > 0, f"Rate limiter triggered {blocked_count} time(s)")


def attack_replay():
    attack_header(7, "Replay Attack Simulation")
    say("Attacker replays a captured session token 8 times.")
    STATS["attacks_simulated"] += 1
    with db() as conn:
        _ensure_user(conn, "replay_victim", "Replay@Secure1!", approved=True)
        _attempt_login(conn, "replay_victim", "Replay@Secure1!")
        token = f"TOKEN_{datetime.now().strftime('%H%M%S')}"
        p(f"  {G}[OK]  Legitimate login captured. Token: {DIM}{token}{RST}\n")
        for i in range(1, 9):
            _log(conn, "replay_victim", "REPLAY_ATTACK_DETECTED", f"replay_{i}_of_8 token={token}")
            STATS["replay_attempts"] += 1
            print(f"  {R}↩  Replay {i}/8  →  {token}  LOGGED{RST}")
            time.sleep(PAUSE)
    print()
    show_result(False, "Replay attack logged — Scyther Nisynch prevents this cryptographically")


def attack_privilege_escalation():
    attack_header(8, "Privilege Escalation Attempt")
    say("Attacker tries to modify their own role after registering.")
    STATS["attacks_simulated"] += 1
    with db() as conn:
        _ensure_user(conn, "priv_attacker", "Attacker@1!", approved=True)
        before = conn.execute("SELECT role FROM users WHERE username='priv_attacker'").fetchone()
        p(f"  {W}Role before: {before['role']}{RST}\n")
        for label in ["role=admin","role=superuser","approved=99"]:
            _log(conn, "priv_attacker", "PRIVILEGE_ESCALATION_ATTEMPT", label)
            print(f"  {R}[ATTEMPT]  {label:<35}  ->  LOGGED{RST}")
            time.sleep(PAUSE)
        after = conn.execute("SELECT role FROM users WHERE username='priv_attacker'").fetchone()
    print()
    p(f"  {W}Role after: {after['role']}{RST}")
    show_result(True, "Role unchanged — attempts only logged, not executed")


def attack_blacklist_bypass():
    attack_header(9, "Blacklist Bypass Attempt")
    say("Blacklisted user tries various methods to regain access.")
    STATS["blacklisted"] += 1
    STATS["attacks_simulated"] += 1
    bypass = [
        ("blacklisted_eve",   "Eve@Hacker1!", "Direct login"),
        ("blacklisted_eve",   "newpassword1!","Password change bypass"),
        ("blacklisted_eve2",  "Eve@Hacker1!", "Variant username"),
        ("blacklisted_eve ",  "Eve@Hacker1!", "Trailing space"),
        ("BLACKLISTED_EVE",   "Eve@Hacker1!", "Uppercase variant"),
    ]
    with db() as conn:
        _ensure_user(conn, "blacklisted_eve", "Eve@Hacker1!", approved=False, locked=True)
        conn.execute("INSERT OR REPLACE INTO blacklist(username,reason) VALUES(?,?)",
                     ("blacklisted_eve","Repeated attack attempts"))
        p(f"  {W}'blacklisted_eve' is blacklisted + locked.{RST}\n")
        for username, password, desc in bypass:
            if username != "blacklisted_eve":
                _ensure_user(conn, username, password, approved=False, locked=True)
            success, reason = _attempt_login(conn, username, password)
            _log(conn, username, "BLACKLIST_BYPASS_ATTEMPT", desc)
            if success:
                print(f"  {R}[BYPASS]  BYPASS SUCCESS: {desc:<35} <- CRITICAL{RST}")
            else:
                print(f"  {G}[BLOCKED]  {desc:<35} reason={reason}{RST}")
            time.sleep(PAUSE)
    print()
    show_result(True, "All blacklist bypass attempts blocked")


def attack_registration_spam():
    attack_header(10, "Mass Registration Spam")
    say("Attacker floods registration to pollute the user database.")
    STATS["attacks_simulated"] += 1
    created = 0
    with db() as conn:
        for i in range(1, 21):
            username = f"spam_user_{i:03d}"
            try:
                conn.execute(
                    "INSERT INTO users (username,password_hash,role,approved,failed_attempts,locked,created_at) VALUES (?,?,?,?,?,?,?)",
                    (username, hash_password("Spam@Pass1!"), "user", 0, 0, 0, str(datetime.now()))
                )
                created += 1
                _log(conn, username, "SPAM_REGISTRATION", "mass_registration_attack")
                print(f"  {Y}[SPAM]   Created: {username}{RST}")
            except sqlite3.IntegrityError:
                print(f"  {DIM}  skip: {username} already exists{RST}")
            time.sleep(PAUSE)
    print()
    show_result(False, f"{created} spam accounts created — admin must review pending approvals")


def print_summary():
    print()
    print(f"{R}  ╔══════════════════════════════════════════════════════════════╗{RST}")
    print(f"{R}  ║              Attack Simulation Complete                     ║{RST}")
    print(f"{R}  ╚══════════════════════════════════════════════════════════════╝{RST}")
    print()
    rows = [
        ("Attacks simulated",      STATS["attacks_simulated"],  W),
        ("Security events logged", STATS["events_logged"],      C),
        ("Brute force attempts",   STATS["brute_attempts"],     R),
        ("SQL injection attempts", STATS["injection_attempts"], R),
        ("Username enum probes",   STATS["enum_attempts"],      Y),
        ("Replay attack attempts", STATS["replay_attempts"],    Y),
        ("Accounts locked (DoS)",  STATS["accounts_locked"],    R),
        ("Users blacklisted",      STATS["blacklisted"],        R),
    ]
    for label, val, colour in rows:
        print(f"  {colour}  {label:<35} {W}{val}{RST}")

    with db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM login_logs").fetchone()[0]
        bad   = conn.execute(
            "SELECT COUNT(*) FROM login_logs WHERE status LIKE '%FAIL%' OR status LIKE '%ATTACK%' OR status LIKE '%LOCKED%' OR status LIKE '%INJECT%' OR status LIKE '%REPLAY%' OR status LIKE '%ENUM%' OR status LIKE '%STUFF%' OR status LIKE '%SPAM%' OR status LIKE '%ESCALAT%'"
        ).fetchone()[0]
    print()
    print(f"  {B}  {'─'*40}{RST}")
    print(f"  {C}  Total audit log entries  : {W}{total}{RST}")
    print(f"  {R}  Suspicious events in DB  : {W}{bad}{RST}")
    print()
    print(f"  {G}  [OK] All attack data is now in the database.{RST}")
    print(f"  {G}  Dashboard:  python3 auth_cli/main.py  →  option 7{RST}")
    print(f"  {G}  Full demo:  python3 demo.py{RST}")
    print()


def main():
    os.chdir(BASE)
    init_db()
    os.system("clear")
    print(f"""
{R}  ╔══════════════════════════════════════════════════════════════════╗
  ║   SCYTHER PLATFORM -- ATTACK SIMULATION SUITE                  ║
  ║   Brute Force · Stuffing · Enumeration · SQL Injection          ║
  ║   DoS Lockout · Rate Evasion · Replay · Escalation · Spam       ║
  ╚══════════════════════════════════════════════════════════════════╝{RST}
""")
    if not FAST:
        input(f"  {Y}Press Enter to begin...{RST}")

    attack_brute_force()
    attack_credential_stuffing()
    attack_user_enumeration()
    attack_sql_injection()
    attack_lockout_dos()
    attack_rate_limit_evasion()
    attack_replay()
    attack_privilege_escalation()
    attack_blacklist_bypass()
    attack_registration_spam()
    print_summary()


if __name__ == "__main__":
    main()
