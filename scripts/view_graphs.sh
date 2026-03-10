#!/bin/bash

# ============================================================
#   Scyther Attack Graph Viewer
#   Browse, render and view protocol attack graphs
# ============================================================

GRAPH=attack_graphs

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

cd ~/secure-auth-scyther

# ── Dependency checks ─────────────────────────────────────

HAS_DOT=false;    command -v dot      &>/dev/null && HAS_DOT=true
HAS_EOG=false;    command -v eog      &>/dev/null && HAS_EOG=true
HAS_DISPLAY=false;[ -n "$DISPLAY" ]               && HAS_DISPLAY=true
HAS_XDOT=false;   command -v xdot     &>/dev/null && HAS_XDOT=true
HAS_FEH=false;    command -v feh      &>/dev/null && HAS_FEH=true

banner() {
    clear
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${CYAN}║         🔍 Scyther Attack Graph Viewer               ║${RESET}"
    echo -e "${BOLD}${CYAN}║         Interactive Protocol Graph Browser           ║${RESET}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════╝${RESET}"
    echo ""
}

check_tools() {
    echo -e "${BOLD}  Available Tools:${RESET}"
    $HAS_DOT     && echo -e "  ${GREEN}✔ graphviz (dot)${RESET} — DOT → PNG rendering" \
                 || echo -e "  ${RED}✘ graphviz missing${RESET}  → sudo apt install graphviz"
    $HAS_XDOT    && echo -e "  ${GREEN}✔ xdot${RESET}           — Interactive DOT viewer" \
                 || echo -e "  ${YELLOW}○ xdot not found${RESET}    → sudo apt install xdot"
    $HAS_EOG     && echo -e "  ${GREEN}✔ eog${RESET}            — GNOME image viewer" \
                 || true
    $HAS_FEH     && echo -e "  ${GREEN}✔ feh${RESET}            — Lightweight image viewer" \
                 || true
    $HAS_DISPLAY && echo -e "  ${GREEN}✔ Display${RESET}        — GUI available" \
                 || echo -e "  ${YELLOW}○ No DISPLAY${RESET}        — GUI may not work (try: export DISPLAY=:0)"
    echo ""
}

list_graphs() {
    echo -e "${BOLD}${BLUE}  Available Attack Graphs:${RESET}"
    echo -e "${BLUE}  ─────────────────────────────────────────────────────${RESET}"

    local i=1
    DOTFILES=()
    while IFS= read -r -d '' f; do
        DOTFILES+=("$f")
        BASENAME=$(basename "$f" .dot)
        PNG="${f%.dot}.png"
        HAS_PNG=""
        [ -f "$PNG" ] && HAS_PNG="${GREEN}[PNG ✔]${RESET}" || HAS_PNG="${YELLOW}[PNG ✘]${RESET}"

        SIZE=$(wc -l < "$f")
        echo -e "  ${BOLD}[$i]${RESET} ${CYAN}$BASENAME${RESET}  $HAS_PNG  ${BLUE}($SIZE lines)${RESET}"
        i=$((i + 1))
    done < <(find "$GRAPH" -name "*.dot" -print0 | sort -z)

    if [ ${#DOTFILES[@]} -eq 0 ]; then
        echo -e "  ${RED}No .dot files found in $GRAPH/${RESET}"
        echo -e "  ${YELLOW}Run ./scripts/generate_graphs.sh first${RESET}"
        echo ""
        exit 1
    fi
    echo ""
}

render_png() {
    local DOTFILE="$1"
    local PNG="${DOTFILE%.dot}.png"
    if $HAS_DOT; then
        echo -e "  ${CYAN}⟳ Rendering PNG...${RESET}"
        if dot -Tpng "$DOTFILE" -o "$PNG" 2>/dev/null; then
            echo -e "  ${GREEN}✔ Rendered → $PNG${RESET}"
            echo "$PNG"
        else
            echo -e "  ${RED}✘ Render failed${RESET}"
            echo ""
        fi
    else
        echo -e "  ${RED}✘ graphviz not installed — cannot render PNG${RESET}"
        echo ""
    fi
}

open_image() {
    local PNG="$1"
    if ! $HAS_DISPLAY; then
        echo -e "  ${YELLOW}⚠ No GUI display found.${RESET}"
        echo -e "  ${YELLOW}  If using SSH, run: ssh -X user@host${RESET}"
        echo -e "  ${YELLOW}  Or copy the file and open locally:${RESET}"
        echo -e "  ${CYAN}  scp kali@<ip>:~/secure-auth-scyther/$PNG .${RESET}"
        return
    fi

    if $HAS_XDOT && [[ "$1" == *.dot ]]; then
        echo -e "  ${CYAN}⟳ Opening in xdot (interactive)...${RESET}"
        xdot "$1" &
    elif $HAS_EOG; then
        echo -e "  ${CYAN}⟳ Opening in Eye of GNOME...${RESET}"
        eog "$PNG" &
    elif $HAS_FEH; then
        echo -e "  ${CYAN}⟳ Opening in feh...${RESET}"
        feh "$PNG" &
    else
        echo -e "  ${YELLOW}⚠ No image viewer found. Install one:${RESET}"
        echo -e "  ${CYAN}  sudo apt install eog     # GNOME viewer${RESET}"
        echo -e "  ${CYAN}  sudo apt install feh     # Lightweight${RESET}"
        echo -e "  ${CYAN}  sudo apt install xdot    # Interactive DOT viewer${RESET}"
    fi
}

print_dot_summary() {
    local DOTFILE="$1"
    echo ""
    echo -e "${BOLD}  DOT File Summary:${RESET}"
    echo -e "${BLUE}  ─────────────────────────────────────────────────────${RESET}"
    NODES=$(grep -c "^[[:space:]]*[a-zA-Z0-9_]* \[" "$DOTFILE" 2>/dev/null || echo 0)
    EDGES=$(grep -c "\->" "$DOTFILE" 2>/dev/null || echo 0)
    GRAPHS=$(grep -c "^digraph\|^graph" "$DOTFILE" 2>/dev/null || echo 0)
    echo -e "  ${CYAN}Graphs/Subgraphs : ${BOLD}$GRAPHS${RESET}"
    echo -e "  ${CYAN}Nodes            : ${BOLD}$NODES${RESET}"
    echo -e "  ${CYAN}Edges/Arrows     : ${BOLD}$EDGES${RESET}"
    echo ""
}

view_menu() {
    local DOTFILE="$1"
    local BASENAME=$(basename "$DOTFILE" .dot)
    local PNG="${DOTFILE%.dot}.png"

    while true; do
        echo ""
        echo -e "${BOLD}${CYAN}  ┌─ $BASENAME ─────────────────────────────────┐${RESET}"
        echo -e "${BOLD}${CYAN}  │  What would you like to do?                  │${RESET}"
        echo -e "${BOLD}${CYAN}  ├───────────────────────────────────────────────┤${RESET}"
        echo -e "${BOLD}${CYAN}  │${RESET}  ${BOLD}[1]${RESET} 🖼  Render & Open as PNG                  ${BOLD}${CYAN}│${RESET}"
        echo -e "${BOLD}${CYAN}  │${RESET}  ${BOLD}[2]${RESET} 🔍 Open in xdot (interactive graph)        ${BOLD}${CYAN}│${RESET}"
        echo -e "${BOLD}${CYAN}  │${RESET}  ${BOLD}[3]${RESET} 📋 Print DOT source to terminal            ${BOLD}${CYAN}│${RESET}"
        echo -e "${BOLD}${CYAN}  │${RESET}  ${BOLD}[4]${RESET} 📊 Show graph summary (nodes/edges)        ${BOLD}${CYAN}│${RESET}"
        echo -e "${BOLD}${CYAN}  │${RESET}  ${BOLD}[5]${RESET} 📤 Show SCP copy command                   ${BOLD}${CYAN}│${RESET}"
        echo -e "${BOLD}${CYAN}  │${RESET}  ${BOLD}[b]${RESET} ← Back to graph list                       ${BOLD}${CYAN}│${RESET}"
        echo -e "${BOLD}${CYAN}  └───────────────────────────────────────────────┘${RESET}"
        echo -n "  Choice: "
        read -r ACTION

        case "$ACTION" in
            1)
                [ ! -f "$PNG" ] && PNG=$(render_png "$DOTFILE")
                [ -f "$PNG" ] && open_image "$PNG" || echo -e "  ${RED}✘ PNG not available${RESET}"
                ;;
            2)
                if $HAS_XDOT; then
                    echo -e "  ${CYAN}⟳ Opening xdot...${RESET}"
                    xdot "$DOTFILE" &
                else
                    echo -e "  ${RED}✘ xdot not installed → sudo apt install xdot${RESET}"
                fi
                ;;
            3)
                echo ""
                echo -e "${BLUE}── DOT Source: $BASENAME ──────────────────────${RESET}"
                cat "$DOTFILE"
                echo -e "${BLUE}───────────────────────────────────────────────${RESET}"
                ;;
            4)
                print_dot_summary "$DOTFILE"
                ;;
            5)
                IP=$(hostname -I | awk '{print $1}')
                echo ""
                echo -e "  ${CYAN}Copy DOT file:${RESET}"
                echo -e "  scp kali@${IP}:~/secure-auth-scyther/$DOTFILE ."
                if [ -f "$PNG" ]; then
                    echo -e "  ${CYAN}Copy PNG file:${RESET}"
                    echo -e "  scp kali@${IP}:~/secure-auth-scyther/$PNG ."
                fi
                ;;
            b|B)
                break
                ;;
            *)
                echo -e "  ${YELLOW}Invalid option${RESET}"
                ;;
        esac
    done
}

# ── Main Loop ─────────────────────────────────────────────

banner
check_tools

while true; do
    list_graphs

    echo -e "${BOLD}  Select a graph to view [1-${#DOTFILES[@]}] or [q] to quit:${RESET}"
    echo -n "  Choice: "
    read -r CHOICE

    if [[ "$CHOICE" == "q" || "$CHOICE" == "Q" ]]; then
        echo ""
        echo -e "  ${GREEN}Bye! 👋${RESET}"
        echo ""
        exit 0
    fi

    if [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "${#DOTFILES[@]}" ]; then
        SELECTED="${DOTFILES[$((CHOICE - 1))]}"
        view_menu "$SELECTED"
    else
        echo -e "  ${RED}Invalid choice${RESET}"
    fi

    banner
    check_tools
done
