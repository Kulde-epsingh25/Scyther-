#!/usr/bin/env python3
"""
dashboard.py — Security operations dashboard
Scyther CLI Authentication & Authorisation Research Platform
"""

import os
import re
from database import get_stats, init_db

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
GRAPHS_DIR  = os.path.join(os.path.dirname(__file__), "..", "attack_graphs")

PROTOCOLS = [
    ("Needham-Schroeder", "ns_result.txt"),
    ("Kerberos",          "kerberos_result.txt"),
    ("OAuth",             "oauth_result.txt"),
    ("Zero Trust",        "zero_trust_result.txt"),
]


# ─────────────────────────────────────────────────────────
# PROTOCOL RESULTS PARSER
# ─────────────────────────────────────────────────────────

def parse_result(filepath: str) -> dict:
    """Parse a Scyther result file and return claim statistics."""
    if not os.path.exists(filepath):
        return {"exists": False, "pass": 0, "fail": 0, "claims": []}

    result = {"exists": True, "pass": 0, "fail": 0, "claims": []}

    with open(filepath) as f:
        for line in f:
            line_clean = re.sub(r"\x1b\[[0-9;]*m", "", line)  # strip ANSI
            if line_clean.startswith("claim"):
                parts = line_clean.strip().split("\t")
                if len(parts) >= 5:
                    claim_id = parts[2] if len(parts) > 2 else "?"
                    nonce    = parts[3] if len(parts) > 3 else "-"
                    status   = parts[4] if len(parts) > 4 else "?"
                    passed   = "Ok" in status
                    result["claims"].append({
                        "id": claim_id, "nonce": nonce,
                        "status": status.strip(), "passed": passed
                    })
                    if passed:
                        result["pass"] += 1
                    else:
                        result["fail"] += 1

    return result


# ─────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────

def sep(char="─", width=62) -> str:
    return "  " + char * width


def header(title: str) -> None:
    print()
    print("  ╔" + "═" * 60 + "╗")
    print(f"  ║  {title:<58}║")
    print("  ╚" + "═" * 60 + "╝")


def main() -> None:
    init_db()
    stats = get_stats()

    # ── Title ────────────────────────────────────────────
    print("\n")
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║        Scyther Research Platform -- Security Dashboard       ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")

    # ── User Statistics ──────────────────────────────────
    header("User Statistics")
    print(f"  {'Total registered':<30} {stats['total_users']}")
    print(f"  {'Approved accounts':<30} {stats['approved']}")
    print(f"  {'Pending approval':<30} {stats['pending']}")
    print(f"  {'Locked accounts':<30} {stats['locked']}")
    print(f"  {'Blacklisted users':<30} {stats['blacklisted']}")

    # ── Login Events ─────────────────────────────────────
    header("Login Audit Summary")
    total = stats["success_logins"] + stats["failed_logins"]
    rate  = (stats["success_logins"] / total * 100) if total else 0
    print(f"  {'Successful logins':<30} [OK]  {stats['success_logins']}")
    print(f"  {'Failed login attempts':<30} [FAIL] {stats['failed_logins']}")
    print(f"  {'Account lock events':<30} [LOCKED] {stats['locked_events']}")
    print(f"  {'Total events logged':<30} {stats['total_logs']}")
    print(f"  {'Login success rate':<30} {rate:.1f}%")

    # ── Protocol Verification ────────────────────────────
    header("Scyther Protocol Verification Results")
    print(f"  {'Protocol':<22} {'Claims Pass':<14} {'Claims Fail':<14} {'Status'}")
    print(sep())

    total_pass = total_fail = verified = 0
    for name, fname in PROTOCOLS:
        fpath  = os.path.join(RESULTS_DIR, fname)
        result = parse_result(fpath)

        if not result["exists"]:
            print(f"  {name:<22} {'—':<14} {'—':<14} [WARN]  Not run yet")
            continue

        p = result["pass"]
        f = result["fail"]
        total_pass += p
        total_fail += f
        verified   += 1

        status = "[SECURE]" if f == 0 else f"[FAIL] {f} FAIL"
        print(f"  {name:<22} {p:<14} {f:<14} {status}")

    print(sep())
    print(f"  {'TOTAL':<22} {total_pass:<14} {total_fail:<14} "
          f"{'[SECURE] All Secure' if total_fail == 0 and verified > 0 else '[FAIL] Issues found'}")

    # ── Attack Graphs ────────────────────────────────────
    header("Attack Graphs")
    dot_files = []
    png_files = []
    if os.path.exists(GRAPHS_DIR):
        dot_files = [f for f in os.listdir(GRAPHS_DIR) if f.endswith(".dot")]
        png_files = [f for f in os.listdir(GRAPHS_DIR) if f.endswith(".png")]

    print(f"  {'DOT graph files':<30} {len(dot_files)}")
    print(f"  {'PNG renders available':<30} {len(png_files)}")
    if dot_files:
        print(f"\n  Files in attack_graphs/:")
        for f in sorted(dot_files):
            has_png = f.replace(".dot", ".png") in png_files
            png_tag = "PNG: Yes" if has_png else "PNG: No"
            print(f"    • {f:<40} {png_tag}")

    # ── Security Summary ─────────────────────────────────
    header("Overall Security Assessment")
    issues = []
    if stats["pending"]  > 0: issues.append(f"{stats['pending']} user(s) awaiting approval")
    if stats["locked"]   > 0: issues.append(f"{stats['locked']} account(s) locked")
    if total_fail        > 0: issues.append(f"{total_fail} protocol claim(s) failing")
    if not dot_files:         issues.append("No attack graphs generated yet")

    if not issues:
        print("  [OK] All systems nominal. No security issues detected.\n")
    else:
        print("  [WARN]  Action required:")
        for issue in issues:
            print(f"     • {issue}")
        print()

    print(sep("═"))
    print()


if __name__ == "__main__":
    main()
