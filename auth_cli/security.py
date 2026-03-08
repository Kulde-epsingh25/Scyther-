#!/usr/bin/env python3
"""
security.py — Cryptographic utilities and security controls
Scyther CLI Authentication & Authorisation Research Platform
"""

import hashlib
import hmac
import re
import secrets
import time


# ─────────────────────────────────────────────────────────
# PASSWORD HASHING
# ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return SHA-256 hex digest of the given password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison — prevents timing-based side-channel attacks."""
    return hmac.compare_digest(hash_password(plain), hashed)


# ─────────────────────────────────────────────────────────
# PASSWORD STRENGTH
# ─────────────────────────────────────────────────────────

def password_strength(password: str) -> tuple:
    """
    Validate password strength.
    Returns (is_valid: bool, message: str).
    """
    checks = [
        (len(password) >= 8,                    "at least 8 characters"),
        (bool(re.search(r"[A-Z]", password)),   "an uppercase letter"),
        (bool(re.search(r"[a-z]", password)),   "a lowercase letter"),
        (bool(re.search(r"[0-9]", password)),   "a digit (0-9)"),
        (bool(re.search(r"[!@#$%^&*]",password)),"a special character (!@#$%^&*)"),
    ]
    failures = [msg for ok, msg in checks if not ok]
    if failures:
        return False, "Password must contain: " + ", ".join(failures)
    return True, "Strong password"


# ─────────────────────────────────────────────────────────
# INPUT SANITISATION
# ─────────────────────────────────────────────────────────

def sanitise_username(username: str) -> str:
    """
    Strip whitespace and enforce safe username format.
    Raises ValueError on invalid input.
    """
    username = username.strip()
    if not re.match(r"^[a-zA-Z0-9_.\-]{3,30}$", username):
        raise ValueError(
            "Username must be 3–30 characters and contain only "
            "letters, digits, underscores, dots, or hyphens."
        )
    return username


def sanitise_input(value: str, max_length: int = 255) -> str:
    """Strip whitespace and enforce a maximum length."""
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters).")
    return value


# ─────────────────────────────────────────────────────────
# TOKEN GENERATION
# ─────────────────────────────────────────────────────────

def generate_token(length: int = 32) -> str:
    """Return a cryptographically secure random hex token."""
    return secrets.token_hex(length)


def generate_session_id() -> str:
    """Return a URL-safe session identifier."""
    return secrets.token_urlsafe(32)


# ─────────────────────────────────────────────────────────
# RATE LIMITING  (in-process, per key)
# ─────────────────────────────────────────────────────────

_rate_store: dict = {}   # { key: [unix_timestamp, ...] }


def is_rate_limited(
    key: str,
    max_attempts: int = 5,
    window_seconds: int = 300
) -> bool:
    """
    Return True if `key` has exceeded `max_attempts`
    within the last `window_seconds`.
    """
    now    = time.time()
    cutoff = now - window_seconds
    hits   = [t for t in _rate_store.get(key, []) if t > cutoff]
    hits.append(now)
    _rate_store[key] = hits
    return len(hits) > max_attempts


def reset_rate_limit(key: str) -> None:
    """Clear all rate-limit history for `key` (e.g. after successful login)."""
    _rate_store.pop(key, None)


# ─────────────────────────────────────────────────────────
# SELF-TEST
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Security Module Self-Test ===\n")

    h = hash_password("MyPass@1")
    print(f"Hash (first 20): {h[:20]}...")
    print(f"Verify correct : {verify_password('MyPass@1', h)}")
    print(f"Verify wrong   : {verify_password('wrongpass', h)}\n")

    samples = ["short", "alllowercase1!", "NOLOWER1!", "NoSpecial1", "Valid@1Pass"]
    for s in samples:
        ok, msg = password_strength(s)
        print(f"  {'✅' if ok else '❌'}  {s!r:20} — {msg}")

    print(f"\nToken     : {generate_token()}")
    print(f"Session ID: {generate_session_id()}\n")

    print("Rate limit test (6 hits, max 5):")
    for i in range(6):
        blocked = is_rate_limited("test", max_attempts=5, window_seconds=60)
        print(f"  Hit {i+1}: {'🔴 BLOCKED' if blocked else '🟢 allowed'}")

    print("\n[security.py] Self-test complete.")
