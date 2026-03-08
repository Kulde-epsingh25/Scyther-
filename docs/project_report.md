# Formal Verification of Authentication and Authorisation Protocols Using Scyther CLI

**Authors:** Kuldeep Singh, Sahil  
**Tool:** Scyther CLI — Formal Protocol Verifier  
**Date:** 2025  
**Version:** 2.0

---

## Abstract

This report presents a research project that combines a functional Python-based CLI authentication system with the formal verification of four cryptographic security protocols using the Scyther model checker. The protocols — Needham-Schroeder (Lowe fix), Kerberos, OAuth, and Zero Trust — were modelled in Scyther's Security Protocol Description Language (SPDL), verified for secrecy and authentication properties, and analysed for known attack vectors. All four protocols pass all Scyther claims, demonstrating that the implemented designs are resistant to known cryptographic attacks within the Dolev-Yao threat model.

---

## 1. Introduction

Authentication and authorisation are foundational pillars of information security. Despite decades of research, insecure protocol design remains a leading cause of system compromise. Formal methods — mathematical techniques for specifying and verifying system properties — offer a rigorous alternative to testing-based assurance.

Scyther is an automated tool for the verification and falsification of cryptographic protocols. It operates under the Dolev-Yao model, which assumes an all-powerful network attacker who can intercept, replay, forge, and redirect messages. If a protocol's security properties hold under this model, they are considered formally verified.

This project has two components:

1. A Python CLI authentication system implementing real-world security controls
2. Formal Scyther verification of four protocols that model its underlying auth/authz mechanisms

---

## 2. Threat Model

All protocols are verified under the **Dolev-Yao threat model**, which assumes:

- The attacker controls the entire network
- The attacker can read, intercept, block, replay, and forge any message
- The attacker cannot break strong cryptography (encryption/hashing)
- The attacker may run protocol sessions as a legitimate party

This is the strongest practical threat model for network security protocols and is the standard assumption in formal protocol analysis.

---

## 3. Protocols Analysed

### 3.1 Needham-Schroeder Public-Key Protocol (Lowe Fix)

**Background:** The original Needham-Schroeder public-key protocol (1978) was shown by Gavin Lowe in 1996 to be vulnerable to a man-in-the-middle attack. The fix adds B's identity to message 2.

**SPDL Model:**

```
protocol NeedhamSchroeder(A, B)
{
    role A {
        fresh Na: Nonce;
        var   Nb: Nonce;
        send_1(A, B, {A, Na}pk(B));
        recv_2(B, A, {Na, Nb, B}pk(A));    ← B's identity binds the response
        send_3(A, B, {Nb}pk(B));
        claim_A1(A, Secret, Na);
        claim_A2(A, Secret, Nb);
        claim_A3(A, Nisynch);
    }
    role B {
        var   Na: Nonce;
        fresh Nb: Nonce;
        recv_1(A, B, {A, Na}pk(B));
        send_2(B, A, {Na, Nb, B}pk(A));
        recv_3(A, B, {Nb}pk(B));
        claim_B1(B, Secret, Nb);
        claim_B2(B, Secret, Na);
        claim_B3(B, Nisynch);
    }
}
```

**Security Properties Verified:**

| Claim | Role | Property | Result |
|-------|------|----------|--------|
| Secret_A1 | A | Na is secret | ✅ PASS |
| Secret_A2 | A | Nb is secret | ✅ PASS |
| Nisynch_A3 | A | Auth synchronisation | ✅ PASS |
| Secret_B1 | B | Nb is secret | ✅ PASS |
| Secret_B2 | B | Na is secret | ✅ PASS |
| Nisynch_B3 | B | Auth synchronisation | ✅ PASS |

**Analysis:** The original protocol fails B's secrecy claims due to the Lowe attack (attacker C uses A's session to authenticate as A to B). The Lowe fix — including B's identity in message 2 — prevents this and all 6 claims pass.

---

### 3.2 Kerberos Authentication Protocol

**Background:** Kerberos (RFC 4120) is a network authentication protocol developed at MIT. It uses symmetric-key cryptography and a trusted third-party ticket-granting server. This model captures the core nonce-based challenge-response between client and service.

**SPDL Model:**

```
protocol Kerberos(C, S)
{
    role C {
        fresh Nc: Nonce;
        send_1(C, S, {Nc}k(C,S));
        recv_2(S, C, {Nc, S}k(C,S));
        claim_C1(C, Secret, Nc);
        claim_C2(C, Nisynch);
    }
    role S {
        var Nc: Nonce;
        recv_1(C, S, {Nc}k(C,S));
        send_2(S, C, {Nc, S}k(C,S));
        claim_S1(S, Secret, Nc);
        claim_S2(S, Nisynch);
    }
}
```

**Security Properties Verified:**

| Claim | Role | Property | Result |
|-------|------|----------|--------|
| Secret_C1 | C | Nc is secret | ✅ PASS |
| Nisynch_C2 | C | Auth synchronisation | ✅ PASS |
| Secret_S1 | S | Nc is secret | ✅ PASS |
| Nisynch_S2 | S | Auth synchronisation | ✅ PASS |

**Analysis:** Encrypting the nonce in message 1 prevents the eavesdropping attack present when the nonce is sent in plaintext. Binding S's identity in message 2 prevents server impersonation. All 4 claims pass.

---

### 3.3 OAuth Token Protocol

**Background:** OAuth 2.0 (RFC 6749) is the industry-standard protocol for delegated authorisation. This model captures the nonce-based token request/response with server identity binding.

**SPDL Model:**

```
protocol OAuth(Client, Server)
{
    role Client {
        fresh Nc: Nonce;
        send_1(Client, Server, {Nc}k(Client,Server));
        recv_2(Server, Client, {Nc, Server}k(Client,Server));
        claim_C1(Client, Secret, Nc);
        claim_C2(Client, Nisynch);
    }
    role Server {
        var Nc: Nonce;
        recv_1(Client, Server, {Nc}k(Client,Server));
        send_2(Server, Client, {Nc, Server}k(Client,Server));
        claim_S1(Server, Secret, Nc);
        claim_S2(Server, Nisynch);
    }
}
```

**Security Properties Verified:**

| Claim | Role | Property | Result |
|-------|------|----------|--------|
| Secret_C1 | Client | Nc is secret | ✅ PASS |
| Nisynch_C2 | Client | Auth synchronisation | ✅ PASS |
| Secret_S1 | Server | Nc is secret | ✅ PASS |
| Nisynch_S2 | Server | Auth synchronisation | ✅ PASS |

**Analysis:** Token secrecy and server authentication both hold. The server binding prevents a compromised relay from substituting a valid token from a different server session.

---

### 3.4 Zero Trust Authentication Protocol

**Background:** Zero Trust (NIST SP 800-207) is an architectural model based on the principle of "never trust, always verify." Every access request is authenticated regardless of network location. This model implements continuous challenge-response verification.

**SPDL Model:**

```
protocol ZeroTrust(U, S)
{
    role U {
        fresh Nu: Nonce;
        send_1(U, S, {Nu}k(U,S));
        recv_2(S, U, {Nu, S}k(U,S));
        claim_U1(U, Secret, Nu);
        claim_U2(U, Nisynch);
    }
    role S {
        var Nu: Nonce;
        recv_1(U, S, {Nu}k(U,S));
        send_2(S, U, {Nu, S}k(U,S));
        claim_S1(S, Secret, Nu);
        claim_S2(S, Nisynch);
    }
}
```

**Security Properties Verified:**

| Claim | Role | Property | Result |
|-------|------|----------|--------|
| Secret_U1 | U | Nu is secret | ✅ PASS |
| Nisynch_U2 | U | Auth synchronisation | ✅ PASS |
| Secret_S1 | S | Nu is secret | ✅ PASS |
| Nisynch_S2 | S | Auth synchronisation | ✅ PASS |

**Analysis:** The Zero Trust model satisfies both secrecy and mutual authentication. Encrypting the challenge and binding service identity in the response aligns with the Zero Trust principle of explicit verification.

---

## 4. Overall Verification Results

| Protocol | Claims Tested | Passed | Failed | Verdict |
|----------|:---:|:---:|:---:|:---:|
| Needham-Schroeder (Lowe Fix) | 6 | 6 | 0 | ✅ SECURE |
| Kerberos | 4 | 4 | 0 | ✅ SECURE |
| OAuth | 4 | 4 | 0 | ✅ SECURE |
| Zero Trust | 4 | 4 | 0 | ✅ SECURE |
| **TOTAL** | **18** | **18** | **0** | **✅ ALL PASS** |

---

## 5. Authentication System Implementation

The Python CLI system implements the following security controls:

### 5.1 Password Security

- **Hashing:** SHA-256 with constant-time comparison via `hmac.compare_digest` to prevent timing attacks
- **Strength enforcement:** Minimum 8 characters, requires uppercase, lowercase, digit, and special character

### 5.2 Access Control

- **Account lockout:** Accounts are locked after 5 consecutive failed login attempts
- **Rate limiting:** In-process rate limiting (5 attempts per 5-minute window per username)
- **Admin approval:** All newly registered accounts require explicit admin approval
- **Blacklisting:** Admin can permanently block users with a reason

### 5.3 Audit Logging

All security events are written to the SQLite database:

| Event | Trigger |
|-------|---------|
| `REGISTERED` | New user registration |
| `LOGIN_SUCCESS` | Successful login |
| `FAILED_LOGIN` | Incorrect password |
| `ACCOUNT_LOCKED` | 5 failed attempts reached |
| `RATE_LIMITED` | Rate limit exceeded |
| `ADMIN_APPROVED` | Admin approved account |
| `ADMIN_UNLOCKED` | Admin unlocked account |
| `BLACKLISTED` | Admin blacklisted user |

### 5.4 Input Validation

- Username restricted to `[a-zA-Z0-9_.\-]`, 3–30 characters
- All inputs stripped and length-bounded before DB operations
- Parameterised SQL queries throughout (no string interpolation)

---

## 6. Bugs Fixed

| File | Bug | Fix Applied |
|------|-----|-------------|
| `main.py` | `elif choice == "6"` extra leading space — IndentationError | Corrected to match other `elif` blocks |
| `main.py` | Option 6 called `os.system("cat results/*")` raw | Replaced with formatted reader with ANSI stripping |
| `auth_system.py` | `log_event()` called with mixed tab+space indent (3 locations) | Standardised to 12-space indentation |
| `auth_system.py` | Bare `except:` silently swallowed all errors | Changed to `except sqlite3.IntegrityError` |
| `auth_system.py` | Connection not closed on early `return` paths | Added `conn.close()` before every exit path |
| `auth_system.py` | Failed attempts counter not reset on success | Added `UPDATE users SET failed_attempts=0` on success |
| `admin_panel.py` | `ADMIN_PASSWORD = "admin123"` stored in plaintext | Replaced with SHA-256 hashed credential |
| `admin_panel.py` | `view_users()` printed raw tuples | Replaced with formatted bordered table |
| `admin_panel.py` | `blacklist` INSERT with no conflict handling | Changed to `INSERT OR REPLACE` |
| `database.py` | File was empty | Implemented full schema: users, login_logs, blacklist |
| `security.py` | File was empty | Implemented hashing, rate limiting, token gen, sanitisation |

---

## 7. Conclusion

This project demonstrates that formal verification is a practical and valuable tool for security protocol design. All four protocols — representing different authentication paradigms — pass their Scyther claims when correctly designed. The key lessons are:

- **Plaintext nonces are never secret.** Any nonce transmitted unencrypted can be observed and replayed.
- **Server identity must be bound in responses.** Without this, an attacker can relay responses between sessions.
- **Lowe's fix to Needham-Schroeder is essential.** The unfixed protocol fails B's secrecy and authentication claims.
- **Formal verification catches design flaws testing cannot.** Scyther explores all possible attacker strategies, not just known ones.

---

## 8. References

1. Needham, R. M., & Schroeder, M. D. (1978). Using encryption for authentication in large networks of computers. *Communications of the ACM*, 21(12), 993–999.
2. Lowe, G. (1996). Breaking and fixing the Needham-Schroeder public-key protocol using FDR. *TACAS 1996*, LNCS 1055, 147–166.
3. Cremers, C. J. F. (2008). The Scyther tool: Verification, falsification, and analysis of security protocols. *CAV 2008*, LNCS 5123.
4. Neuman, C., Yu, T., Hartman, S., & Raeburn, K. (2005). *The Kerberos Network Authentication Service (V5)*. RFC 4120. IETF.
5. Hardt, D. (2012). *The OAuth 2.0 Authorization Framework*. RFC 6749. IETF.
6. Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). *Zero Trust Architecture*. NIST SP 800-207.
7. Dolev, D., & Yao, A. (1983). On the security of public key protocols. *IEEE Transactions on Information Theory*, 29(2), 198–208.
