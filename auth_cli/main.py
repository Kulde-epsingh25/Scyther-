#!/usr/bin/env python3
"""
main.py — Entry point for the Scyther Research Platform
Scyther CLI Authentication & Authorisation Research Platform
"""

import os
import sys

# ── Ensure auth_cli is importable ───────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "auth_cli"))

from database import init_db


# ─────────────────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────────────────

def banner() -> None:
    os.system("clear")
    print("\n")
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║                                                              ║")
    print("  ║    ███████╗ ██████╗██╗   ██╗████████╗██╗  ██╗███████╗██████╗║")
    print("  ║    ██╔════╝██╔════╝╚██╗ ██╔╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗║")
    print("  ║    ███████╗██║      ╚████╔╝    ██║   ███████║█████╗  ██████╔╝║")
    print("  ║    ╚════██║██║       ╚██╔╝     ██║   ██╔══██║██╔══╝  ██╔══██╗║")
    print("  ║    ███████║╚██████╗   ██║      ██║   ██║  ██║███████╗██║  ██║║")
    print("  ║    ╚══════╝ ╚═════╝   ╚═╝      ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝║")
    print("  ║                                                              ║")
    print("  ║      Authentication & Authorisation Research Platform        ║")
    print("  ║         Formal Protocol Verification using Scyther CLI       ║")
    print("  ║                                                              ║")
    print("  ║  Authors  : Kuldeep Singh & Sahil                           ║")
    print("  ║  GitHub   : github.com/kulde-epsingh25                      ║")
    print("  ║  Tool     : Scyther CLI — Formal Security Protocol Verifier ║")
    print("  ║  Version  : 2.0                                             ║")
    print("  ╚══════════════════════════════════════════════════════════════╝\n")


# ─────────────────────────────────────────────────────────
# MENU
# ─────────────────────────────────────────────────────────

def menu() -> str:
    print("  ┌──────────────────────────────────────────────┐")
    print("  │              Main Menu                       │")
    print("  ├──────────────────────────────────────────────┤")
    print("  │                                              │")
    print("  │   Authentication                             │")
    print("  │       1   Register New User                  │")
    print("  │       2   Login                              │")
    print("  │       3   Admin Panel                        │")
    print("  │                                              │")
    print("  │   Scyther Protocol Verification              │")
    print("  │       4   Verify Protocols                   │")
    print("  │       5   Generate Attack Graphs             │")
    print("  │       6   View Attack Graphs (Interactive)   │")
    print("  │                                              │")
    print("  │   Reporting                                  │")
    print("  │       7   Security Dashboard                 │")
    print("  │       8   View Raw Verification Results      │")
    print("  │                                              │")
    print("  │       0   Exit                               │")
    print("  │                                              │")
    print("  └──────────────────────────────────────────────┘")
    return input("\n  Enter choice > ").strip()


# ─────────────────────────────────────────────────────────
# ACTION HANDLERS
# ─────────────────────────────────────────────────────────

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd: str) -> None:
    os.system(cmd)


def register_user() -> None:
    run(f"python3 {BASE}/auth_cli/auth_system.py register")


def login_user() -> None:
    run(f"python3 {BASE}/auth_cli/auth_system.py login")


def admin_panel() -> None:
    run(f"python3 {BASE}/auth_cli/admin_panel.py")


def verify_protocols() -> None:
    print("\n  Running Scyther protocol verification...\n")
    run(f"bash {BASE}/scripts/verify_protocols.sh")


def generate_graphs() -> None:
    print("\n  Generating attack graphs...\n")
    run(f"bash {BASE}/scripts/generate_graphs.sh")


def view_graphs() -> None:
    run(f"bash {BASE}/scripts/view_graphs.sh")


def security_dashboard() -> None:
    run(f"python3 {BASE}/auth_cli/dashboard.py")


def view_raw_results() -> None:
    results_dir = os.path.join(BASE, "results")
    if not os.path.exists(results_dir) or not os.listdir(results_dir):
        print("\n  [WARN]  No results found. Run option 4 first.\n")
        return

    print()
    for fname in sorted(os.listdir(results_dir)):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(results_dir, fname)
        label = fname.replace("_result.txt", "").replace("_", " ").title()
        print(f"  ── {label} " + "─" * (50 - len(label)))
        with open(fpath) as f:
            import re
            for line in f:
                clean = re.sub(r"\x1b\[[0-9;]*m", "", line).rstrip()
                if clean.startswith("claim"):
                    parts  = clean.split("\t")
                    cid    = parts[2] if len(parts) > 2 else "?"
                    nonce  = parts[3] if len(parts) > 3 else "-"
                    status = parts[4] if len(parts) > 4 else "?"
                    icon   = "[OK] " if "Ok" in status else "[FAIL]"
                    print(f"    {icon}  {cid:<20} {nonce:<8} {status}")
        print()


# ─────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────

ACTIONS = {
    "1": register_user,
    "2": login_user,
    "3": admin_panel,
    "4": verify_protocols,
    "5": generate_graphs,
    "6": view_graphs,
    "7": security_dashboard,
    "8": view_raw_results,
}


def main() -> None:
    init_db()

    while True:
        banner()
        choice = menu()

        if choice == "0":
            print("\n  Goodbye!\n")
            sys.exit(0)

        action = ACTIONS.get(choice)
        if action:
            action()
        else:
            print("\n  [ERROR]  Invalid option. Please choose 0-8.\n")

        input("\n  Press Enter to return to main menu...")


if __name__ == "__main__":
    main()
