#!/bin/bash

# ============================================================
#   Scyther Attack Graph Generator
#   Generates DOT + PNG visual attack graphs per protocol
# ============================================================

PROTO=protocols
GRAPH=attack_graphs
mkdir -p "$GRAPH"

PASS=0
FAIL=0

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# Check graphviz
HAS_DOT=false
command -v dot &>/dev/null && HAS_DOT=true

banner() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${CYAN}║       🔐 Scyther Attack Graph Generator          ║${RESET}"
    echo -e "${BOLD}${CYAN}║       Security Protocol Visualisation Tool       ║${RESET}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
    echo ""
    if $HAS_DOT; then
        echo -e "  ${GREEN}✔ Graphviz detected — PNG graphs will be rendered${RESET}"
    else
        echo -e "  ${YELLOW}⚠ Graphviz not found — install with: sudo apt install graphviz${RESET}"
    fi
    echo ""
}

section() {
    echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────┐${RESET}"
    echo -e "${BOLD}${BLUE}│  $1${RESET}"
    echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────┘${RESET}"
}

generate_graph() {
    local NUM="$1"
    local NAME="$2"
    local FILE="$3"
    local OUTBASE="$4"
    local PNG_FILE="$GRAPH/$OUTBASE.png"

    echo ""
    section "[$NUM] $NAME"

    if [ ! -f "$FILE" ]; then
        echo -e "  ${RED}❌ ERROR: Protocol file not found → $FILE${RESET}"
        FAIL=$((FAIL + 1))
        return
    fi

    echo -e "  ${CYAN}⟳ Running Scyther analysis...${RESET}"

    # Clean up any pre-existing scyther dot files
    rm -f *.dot

    # Run scyther — it writes .dot files itself into the current directory
    OUTPUT=$(scyther-linux --dot-output "$FILE" 2>&1)

    # Check for errors
    if echo "$OUTPUT" | grep -q "error:"; then
        echo -e "  ${RED}❌ Scyther Error:${RESET}"
        echo "$OUTPUT" | grep "error:" | while read -r line; do
            echo -e "     ${RED}→ $line${RESET}"
        done
        FAIL=$((FAIL + 1))
        return
    fi

    # Find dot files scyther actually wrote
    DOTFILES=(*.dot)

    if [ ! -e "${DOTFILES[0]}" ]; then
        echo -e "  ${GREEN}✅ STATUS: SECURE — No attack graph generated (no attacks found)${RESET}"
        PASS=$((PASS + 1))
        return
    fi

    # Move and merge all dot files scyther produced into graph dir
    COMBINED_DOT="$GRAPH/$OUTBASE.dot"
    cat *.dot > "$COMBINED_DOT"
    mv *.dot "$GRAPH/"
    echo -e "  ${GREEN}✔ DOT file(s) saved → $GRAPH/${RESET}"

    # Render PNG from the combined dot file
    if $HAS_DOT; then
        if dot -Tpng "$COMBINED_DOT" -o "$PNG_FILE" 2>/dev/null; then
            SIZE=$(du -sh "$PNG_FILE" | cut -f1)
            echo -e "  ${GREEN}✔ PNG rendered      → $PNG_FILE ($SIZE)${RESET}"
        else
            # Try each individual dot file if combined fails
            echo -e "  ${YELLOW}  Combined render failed — trying individual files...${RESET}"
            for dotfile in "$GRAPH"/${OUTBASE}*.dot; do
                pngout="${dotfile%.dot}.png"
                if dot -Tpng "$dotfile" -o "$pngout" 2>/dev/null; then
                    SIZE=$(du -sh "$pngout" | cut -f1)
                    echo -e "  ${GREEN}✔ PNG rendered      → $pngout ($SIZE)${RESET}"
                fi
            done
        fi
    fi

    # Determine attack vs secure
    if echo "$OUTPUT" | grep -qi "attack\|FAIL"; then
        ATTACK_COUNT=$(ls "$GRAPH"/${OUTBASE}*.dot 2>/dev/null | wc -l)
        echo -e "  ${RED}⚠  ATTACK FOUND — $ATTACK_COUNT attack trace(s) in graph${RESET}"
        FAIL=$((FAIL + 1))
    else
        echo -e "  ${GREEN}✅ STATUS: SECURE — All claims hold${RESET}"
        PASS=$((PASS + 1))
    fi
}

# ── Main ──────────────────────────────────────────────────

banner

cd ~/secure-auth-scyther

generate_graph 1 "Needham-Schroeder Protocol" "$PROTO/needham_schroeder.spdl" "ns_attack"
generate_graph 2 "Kerberos Protocol"           "$PROTO/kerberos_auth.spdl"     "kerberos_attack"
generate_graph 3 "OAuth Protocol"              "$PROTO/oauth_token.spdl"       "oauth_attack"
generate_graph 4 "Zero Trust Protocol"         "$PROTO/zero_trust_auth.spdl"   "zero_trust_attack"

# ── Summary ───────────────────────────────────────────────

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║               📊 Generation Summary              ║${RESET}"
echo -e "${BOLD}${CYAN}╠══════════════════════════════════════════════════╣${RESET}"
echo -e "${BOLD}${CYAN}║${RESET}  ✅ Secure (no attacks)  : ${GREEN}$PASS${RESET}"
echo -e "${BOLD}${CYAN}║${RESET}  ❌ Attacks found        : ${RED}$FAIL${RESET}"
echo -e "${BOLD}${CYAN}║${RESET}  📁 Output directory     : ${YELLOW}$GRAPH/${RESET}"
if $HAS_DOT; then
echo -e "${BOLD}${CYAN}║${RESET}  🖼  PNG graphs rendered  : ${GREEN}Yes${RESET}"
else
echo -e "${BOLD}${CYAN}║${RESET}  🖼  PNG graphs rendered  : ${YELLOW}No (install graphviz)${RESET}"
fi
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}🎉 All protocols are secure — no attack graphs produced!${RESET}"
else
    echo -e "  ${RED}${BOLD}⚠  $FAIL protocol(s) have attack traces — review graphs in $GRAPH/${RESET}"
    $HAS_DOT && echo -e "  ${YELLOW}   Open the .png files to visualise the attack paths.${RESET}"
fi
echo ""
