#!/bin/bash
# ============================================================
#   verify_protocols.sh
#   Scyther CLI Authentication & Authorisation Research Platform
#   Runs formal verification on all security protocols
# ============================================================

BASE="$(cd "$(dirname "$0")/.." && pwd)"
PROTO="$BASE/protocols"
RESULT="$BASE/results"
mkdir -p "$RESULT"

# ── Colours ──────────────────────────────────────────────
RED='\033[0;31m';   GREEN='\033[0;32m'
YELLOW='\033[1;33m';CYAN='\033[1;36m'
BLUE='\033[0;34m';  BOLD='\033[1m'; RESET='\033[0m'

PASS=0; FAIL=0

# ── Banner ───────────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║   🔬  Scyther Protocol Verification — Research Platform      ║${RESET}"
echo -e "${BOLD}${CYAN}║       Formal Security Analysis of Auth/Authz Protocols       ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# ── Scyther check ────────────────────────────────────────
if ! command -v scyther-linux &>/dev/null; then
    echo -e "${RED}  ❌ scyther-linux not found in PATH.${RESET}"
    echo -e "${YELLOW}     Install from: https://people.cispa.io/cas.cremers/scyther/${RESET}"
    exit 1
fi

# ── Table printer ────────────────────────────────────────
print_claims_table() {
    local OUTPUT="$1"
    local any_fail=0

    printf "\n"
    printf "  %-26s %-10s %-12s %s\n" "Claim ID" "Nonce" "Property" "Result"
    printf "  %-26s %-10s %-12s %s\n" \
        "──────────────────────────" "──────────" "────────────" "──────────"

    while IFS=$'\t' read -r tag proto_claim claim_id nonce raw_status rest; do
        [[ "$tag" != "claim" ]] && continue

        # Strip ANSI colour codes from status
        status=$(echo "$raw_status" | sed 's/\x1b\[[0-9;]*m//g' | tr -d '[]')

        # Determine property from claim_id suffix
        if   echo "$claim_id" | grep -q "Nisynch"; then prop="Nisynch"
        elif echo "$claim_id" | grep -q "Secret";  then prop="Secret"
        else prop="—"
        fi

        if echo "$status" | grep -qi "Ok"; then
            result="${GREEN}✅ PASS${RESET}"
        else
            result="${RED}❌ FAIL${RESET}"
            any_fail=1
        fi

        printf "  %-26s %-10s %-12s " "$claim_id" "$nonce" "$prop"
        echo -e "$result"

    done <<< "$OUTPUT"

    printf "\n"
    return $any_fail
}

# ── Per-protocol runner ──────────────────────────────────
run_check() {
    local NUM="$1" NAME="$2" FILE="$3" OUT="$4"

    echo ""
    echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${RESET}"
    echo -e "${BOLD}${BLUE}│  [$NUM] $NAME${RESET}"
    echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${RESET}"

    if [[ ! -f "$FILE" ]]; then
        echo -e "  ${RED}❌ Protocol file not found: $FILE${RESET}"
        FAIL=$((FAIL + 1))
        return
    fi

    OUTPUT=$(scyther-linux "$FILE" 2>&1)
    echo "$OUTPUT" > "$OUT"

    if echo "$OUTPUT" | grep -q "error:"; then
        echo -e "  ${RED}❌ Scyther parse error:${RESET}"
        grep "error:" <<< "$OUTPUT" | while read -r l; do
            echo -e "     ${RED}→ $l${RESET}"
        done
        FAIL=$((FAIL + 1))
        return
    fi

    if echo "$OUTPUT" | grep -q "warning:"; then
        echo -e "  ${YELLOW}⚠  Warning (no claims defined):${RESET}"
        grep "warning:" <<< "$OUTPUT" | head -1 | while read -r l; do
            echo -e "     ${YELLOW}→ $l${RESET}"
        done
        FAIL=$((FAIL + 1))
        return
    fi

    print_claims_table "$OUTPUT"
    table_exit=$?

    if echo "$OUTPUT" | grep -qi "^claim.*FAIL\b"; then
        echo -e "  ${RED}  ❌ OVERALL: FAIL${RESET}  — attack trace saved → $OUT"
        FAIL=$((FAIL + 1))
    elif echo "$OUTPUT" | grep -qi "Ok"; then
        echo -e "  ${GREEN}  ✅ OVERALL: PASS${RESET}  — all claims verified secure"
        PASS=$((PASS + 1))
    else
        echo -e "  ${YELLOW}  ⚠  OVERALL: UNKNOWN${RESET} — check $OUT"
        FAIL=$((FAIL + 1))
    fi
}

# ── Run all protocols ────────────────────────────────────
run_check 1 "Needham-Schroeder Protocol  (Public-Key MITM Prevention)" \
    "$PROTO/needham_schroeder.spdl" "$RESULT/ns_result.txt"

run_check 2 "Kerberos Authentication Protocol  (Shared-Key Ticket Auth)" \
    "$PROTO/kerberos_auth.spdl"    "$RESULT/kerberos_result.txt"

run_check 3 "OAuth Token Protocol  (Delegated Authorisation)" \
    "$PROTO/oauth_token.spdl"      "$RESULT/oauth_result.txt"

run_check 4 "Zero Trust Protocol  (Never Trust, Always Verify)" \
    "$PROTO/zero_trust_auth.spdl"  "$RESULT/zero_trust_result.txt"

# ── Summary ──────────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║                   Verification Summary                      ║${RESET}"
echo -e "${BOLD}${CYAN}╠══════════════════════════════════════════════════════════════╣${RESET}"
echo -e "${BOLD}${CYAN}║${RESET}  ✅  Protocols passed   : ${GREEN}${BOLD}$PASS / 4${RESET}"
echo -e "${BOLD}${CYAN}║${RESET}  ❌  Protocols failed   : ${RED}${BOLD}$FAIL / 4${RESET}"
echo -e "${BOLD}${CYAN}║${RESET}  📁  Results directory  : ${YELLOW}results/${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "  ${GREEN}${BOLD}🎉 All 4 protocols passed formal verification!${RESET}"
    echo -e "  ${GREEN}   Secrecy and authentication properties hold.${RESET}"
else
    echo -e "  ${RED}${BOLD}⚠  $FAIL protocol(s) failed — review results/ for attack traces.${RESET}"
fi
echo ""
