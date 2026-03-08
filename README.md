# 🔐 Scyther CLI Authentication & Authorisation Research Platform

> Formal verification of security protocols using Scyther CLI, integrated with a Python-based CLI authentication system.

**Authors:** Kuldeep Singh & Sahil  
**GitHub:** [github.com/kulde-epsingh25](https://github.com/kulde-epsingh25)  
**Version:** 2.0

---

## 📖 Overview

This project combines a **real-world CLI authentication system** with **formal cryptographic protocol verification** using the [Scyther](https://people.cispa.io/cas.cremers/scyther/) model checker. Four industry-standard authentication and authorisation protocols are modelled in Scyther's SPDL language, verified for secrecy and authentication properties, and presented alongside a working Python auth system.

---

## 📁 Project Structure

```
secure-auth-scyther/
│
├── auth_cli/                  # Python authentication system
│   ├── main.py                # Entry point & main menu
│   ├── auth_system.py         # User registration & login
│   ├── admin_panel.py         # Admin control panel
│   ├── dashboard.py           # Security operations dashboard
│   ├── database.py            # SQLite DB init & helpers
│   └── security.py            # Crypto utilities & rate limiting
│
├── protocols/                 # Scyther SPDL protocol models
│   ├── needham_schroeder.spdl
│   ├── kerberos_auth.spdl
│   ├── oauth_token.spdl
│   └── zero_trust_auth.spdl
│
├── scripts/                   # Shell scripts
│   ├── verify_protocols.sh    # Run Scyther verification
│   ├── generate_graphs.sh     # Generate DOT + PNG attack graphs
│   └── view_graphs.sh         # Interactive graph browser
│
├── results/                   # Scyther output (auto-generated)
├── attack_graphs/             # DOT and PNG graph files
├── database/                  # SQLite database (auto-generated)
├── logs/                      # Application logs
└── docs/
    └── project_report.md      # Full research report
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install Scyther
sudo apt install scyther     # or download from:
# https://people.cispa.io/cas.cremers/scyther/

# Install Graphviz (for PNG graph rendering)
sudo apt install graphviz

# Install xdot (for interactive graph viewing)
sudo apt install xdot

# Python 3.8+ (standard library only — no pip install needed)
python3 --version
```

### Run the Platform

```bash
cd ~/secure-auth-scyther
python3 auth_cli/main.py
```

### Run Verification Only

```bash
cd ~/secure-auth-scyther
./scripts/verify_protocols.sh
```

### Generate Attack Graphs

```bash
./scripts/generate_graphs.sh
```

### View Graphs Interactively

```bash
./scripts/view_graphs.sh
```

---

## 🔬 Protocols Verified

### 1. Needham-Schroeder (Public Key) — Fixed Lowe Variant

The classic Needham-Schroeder public-key protocol is vulnerable to a man-in-the-middle attack discovered by Lowe (1996). This project implements the **Lowe fix**, which adds B's identity to message 2, preventing impersonation.

| Message | Content |
|---------|---------|
| A → B | `{A, Na}pk(B)` |
| B → A | `{Na, Nb, B}pk(A)` ← Lowe fix |
| A → B | `{Nb}pk(B)` |

**Claims verified:** Secret(Na), Secret(Nb), Nisynch ✅

---

### 2. Kerberos Authentication Protocol

Models the core Kerberos ticket-granting exchange using a shared symmetric key between client and server. The nonce is encrypted in all messages to prevent eavesdropping.

| Message | Content |
|---------|---------|
| C → S | `{Nc}k(C,S)` |
| S → C | `{Nc, S}k(C,S)` |

**Claims verified:** Secret(Nc), Nisynch ✅

---

### 3. OAuth Token Protocol

Models the OAuth 2.0 nonce-based token exchange using a shared key, binding the server identity in the response to prevent token substitution attacks.

| Message | Content |
|---------|---------|
| Client → Server | `{Nc}k(Client,Server)` |
| Server → Client | `{Nc, Server}k(Client,Server)` |

**Claims verified:** Secret(Nc), Nisynch ✅

---

### 4. Zero Trust Protocol

Models the Zero Trust principle of "never trust, always verify" — every request is authenticated with an encrypted nonce and server identity binding.

| Message | Content |
|---------|---------|
| U → S | `{Nu}k(U,S)` |
| S → U | `{Nu, S}k(U,S)` |

**Claims verified:** Secret(Nu), Nisynch ✅

---

## 🛡 Security Properties

| Property | Description |
|----------|-------------|
| **Secrecy** | The nonce value cannot be learned by an attacker |
| **Nisynch** | Non-injective synchronisation — both roles agree on the message sequence (authentication) |

---

## 🖥 Authentication System Features

| Feature | Details |
|---------|---------|
| **Password strength** | Min 8 chars, upper/lower, digit, special char |
| **Hashing** | SHA-256 with constant-time comparison (HMAC) |
| **Account lockout** | Locked after 5 failed attempts |
| **Rate limiting** | Per-user in-process rate limiting (5 attempts / 5 min) |
| **Admin approval** | All new users require admin approval |
| **Audit logging** | All auth events written to SQLite |
| **Blacklisting** | Admin can permanently blacklist users |
| **Input sanitisation** | Username regex validation, max-length enforcement |

---

## 🔑 Default Admin Credentials

```
Password: Admin@Scyther1
```

> ⚠ Change this in `auth_cli/admin_panel.py` → `ADMIN_HASH` before production use.

---

## 📊 Verification Results

All 4 protocols pass all Scyther claims:

```
[1] Needham-Schroeder    ✅ PASS  — 6/6 claims
[2] Kerberos             ✅ PASS  — 4/4 claims
[3] OAuth                ✅ PASS  — 4/4 claims
[4] Zero Trust           ✅ PASS  — 4/4 claims
```

---

## 📚 References

- Needham, R., Schroeder, M. (1978). *Using encryption for authentication in large networks*
- Lowe, G. (1996). *Breaking and fixing the Needham-Schroeder public-key protocol*
- Cremers, C. (2008). *The Scyther Tool: Verification, Falsification, and Analysis of Security Protocols*
- Neuman, C. et al. (2005). *The Kerberos Network Authentication Service (V5)* — RFC 4120
- Hardt, D. (2012). *The OAuth 2.0 Authorization Framework* — RFC 6749
- NIST SP 800-207 (2020). *Zero Trust Architecture*
