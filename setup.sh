#!/bin/bash
# ============================================================
#   setup.sh — Pre-installation Setup Script
#   Scyther CLI Authentication & Authorisation Research Platform
#
#   Installs and configures all required tools on Kali / Debian
#   / Ubuntu Linux WITHOUT modifying any core project files.
#
#   Tools installed:
#     • scyther-linux  — formal security-protocol verifier
#     • graphviz (dot) — attack-graph PNG renderer
#     • xdot           — interactive DOT graph viewer
#     • python3        — runtime for the auth CLI
#
#   Usage:
#     chmod +x setup.sh
#     sudo ./setup.sh          # recommended (needs root for apt / /usr/local/bin)
#     ./setup.sh               # runs without sudo where possible
# ============================================================

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { echo -e "${CYAN}  [INFO]${RESET}  $*"; }
ok()      { echo -e "${GREEN}  [ OK ]${RESET}  $*"; }
warn()    { echo -e "${YELLOW}  [WARN]${RESET}  $*"; }
err()     { echo -e "${RED}  [ERR ]${RESET}  $*"; }
section() {
    echo ""
    echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${RESET}"
    echo -e "${BOLD}${BLUE}│  $1${RESET}"
    echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${RESET}"
}

# ── Determine sudo prefix ─────────────────────────────────────────────────────
if [[ $EUID -eq 0 ]]; then
    SUDO=""
else
    if command -v sudo &>/dev/null; then
        SUDO="sudo"
    else
        warn "Not running as root and 'sudo' is not available."
        warn "Some steps may fail. Run with: sudo ./setup.sh"
        SUDO=""
    fi
fi

# ── Locate project root (directory containing this script) ───────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Banner ────────────────────────────────────────────────────────────────────
clear
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║     🔐  Scyther Research Platform — Setup Script            ║${RESET}"
echo -e "${BOLD}${CYAN}║         Pre-installation & Configuration Utility            ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
info "Project root  : $PROJECT_DIR"
info "Running as    : $(whoami)"
info "Date / time   : $(date)"
echo ""

# ── 1. OS / Distribution check ───────────────────────────────────────────────
section "Step 1 — Operating System Detection"

OS_ID=""
if [[ -f /etc/os-release ]]; then
    # shellcheck source=/dev/null
    . /etc/os-release
    OS_ID="${ID:-unknown}"
    OS_NAME="${PRETTY_NAME:-unknown}"
fi

case "$OS_ID" in
    kali|debian|ubuntu|linuxmint|pop|raspbian)
        ok "Detected Debian-based system: $OS_NAME"
        PKG_MANAGER="apt-get"
        ;;
    *)
        warn "OS '$OS_ID' is not explicitly supported."
        warn "This script is designed for Kali / Debian / Ubuntu."
        warn "Continuing anyway — you may need to install packages manually."
        PKG_MANAGER="apt-get"
        ;;
esac

# ── 2. Update package lists ───────────────────────────────────────────────────
section "Step 2 — Update Package Lists"

if command -v "$PKG_MANAGER" &>/dev/null; then
    info "Running: $SUDO $PKG_MANAGER update -y"
    $SUDO $PKG_MANAGER update -y 2>&1 | tail -5
    ok "Package lists updated."
else
    warn "Package manager '$PKG_MANAGER' not found. Skipping update."
fi

# ── 3. Install Python 3 ───────────────────────────────────────────────────────
section "Step 3 — Python 3"

PYTHON_OK=false
for PY in python3 python3.11 python3.10 python3.9 python3.8; do
    if command -v "$PY" &>/dev/null; then
        PY_VER=$("$PY" -c "import sys; print('{}.{}'.format(*sys.version_info[:2]))")
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 8 ]]; then
            ok "Found: $PY  (version $PY_VER) — meets Python 3.8+ requirement"
            PYTHON_OK=true
            PYTHON_BIN="$PY"
            break
        fi
    fi
done

if ! $PYTHON_OK; then
    info "Python 3.8+ not found — attempting to install python3..."
    $SUDO $PKG_MANAGER install -y python3 python3-venv python3-pip 2>&1 | tail -5
    if command -v python3 &>/dev/null; then
        PY_VER=$(python3 -c "import sys; print('{}.{}'.format(*sys.version_info[:2]))")
        ok "Installed python3 $PY_VER"
        PYTHON_BIN="python3"
        PYTHON_OK=true
    else
        err "Could not install python3. Please install it manually."
    fi
fi

# ── 4. Install Graphviz ───────────────────────────────────────────────────────
section "Step 4 — Graphviz (dot command)"

if command -v dot &>/dev/null; then
    DOT_VER=$(dot -V 2>&1 | head -1)
    ok "Graphviz already installed: $DOT_VER"
else
    info "Installing graphviz..."
    $SUDO $PKG_MANAGER install -y graphviz 2>&1 | tail -5
    if command -v dot &>/dev/null; then
        DOT_VER=$(dot -V 2>&1 | head -1)
        ok "Graphviz installed: $DOT_VER"
    else
        err "Graphviz (dot) could not be installed."
        warn "Attack graph PNG rendering will be unavailable."
        warn "Install manually: sudo apt-get install graphviz"
    fi
fi

# ── 5. Install xdot ──────────────────────────────────────────────────────────
section "Step 5 — xdot (interactive graph viewer)"

if command -v xdot &>/dev/null; then
    ok "xdot already installed: $(command -v xdot)"
else
    info "Installing xdot..."
    $SUDO $PKG_MANAGER install -y xdot 2>&1 | tail -5
    if command -v xdot &>/dev/null; then
        ok "xdot installed."
    else
        warn "xdot could not be installed."
        warn "Interactive graph viewing will be unavailable."
        warn "Install manually: sudo apt-get install xdot"
    fi
fi

# ── 6. Install Scyther ───────────────────────────────────────────────────────
section "Step 6 — Scyther Protocol Verifier"

SCYTHER_OK=false
SCYTHER_INSTALL_DIR="/usr/local/bin"

# Helper: test that the binary actually runs (with a 5-second timeout)
_test_scyther() {
    local bin="$1"
    local output
    output=$(timeout 5s "$bin" --help 2>&1) && return 0
    echo "$output" | grep -qi "scyther\|usage\|option" && return 0
    return 1
}

# 6a. Check if scyther-linux already exists in PATH
if command -v scyther-linux &>/dev/null; then
    ok "scyther-linux already in PATH: $(command -v scyther-linux)"
    SCYTHER_OK=true

# 6b. Check if 'scyther' is installed (apt package may use this name)
elif command -v scyther &>/dev/null; then
    ok "'scyther' command found: $(command -v scyther)"
    info "Creating 'scyther-linux' symlink → scyther ..."
    SCYTHER_REAL=$(command -v scyther)
    $SUDO ln -sf "$SCYTHER_REAL" "$SCYTHER_INSTALL_DIR/scyther-linux"
    if command -v scyther-linux &>/dev/null; then
        ok "Symlink created: $SCYTHER_INSTALL_DIR/scyther-linux → $SCYTHER_REAL"
        SCYTHER_OK=true
    else
        warn "Symlink creation failed — try: sudo ln -sf $(command -v scyther) /usr/local/bin/scyther-linux"
    fi

else
    # 6c. Try apt-get install scyther
    info "Trying: $SUDO $PKG_MANAGER install -y scyther ..."
    if $SUDO $PKG_MANAGER install -y scyther 2>&1 | tail -5; then
        if command -v scyther &>/dev/null; then
            ok "Scyther installed via apt."
            SCYTHER_REAL=$(command -v scyther)
            info "Creating 'scyther-linux' symlink..."
            $SUDO ln -sf "$SCYTHER_REAL" "$SCYTHER_INSTALL_DIR/scyther-linux"
            ok "Symlink created: $SCYTHER_INSTALL_DIR/scyther-linux → $SCYTHER_REAL"
            SCYTHER_OK=true
        elif command -v scyther-linux &>/dev/null; then
            ok "scyther-linux installed via apt."
            SCYTHER_OK=true
        fi
    fi

    # 6d. If apt failed, download the precompiled binary
    if ! $SCYTHER_OK; then
        info "Scyther not available via apt — attempting binary download..."

        ARCH=$(uname -m)
        case "$ARCH" in
            x86_64)      SCYTHER_URL="https://people.cispa.io/cas.cremers/scyther/scyther-linux" ;;
            aarch64|*)   SCYTHER_URL="" ;;
        esac

        if [[ -z "$SCYTHER_URL" ]]; then
            warn "No precompiled Scyther binary for architecture: $ARCH"
            warn "Download manually from: https://people.cispa.io/cas.cremers/scyther/"
            warn "Place the binary at $SCYTHER_INSTALL_DIR/scyther-linux and run:"
            warn "  sudo chmod +x $SCYTHER_INSTALL_DIR/scyther-linux"
        else
            # Install curl/wget if needed
            DOWNLOADER=""
            if command -v wget &>/dev/null; then
                DOWNLOADER="wget"
            elif command -v curl &>/dev/null; then
                DOWNLOADER="curl"
            else
                info "Installing wget for downloading Scyther..."
                $SUDO $PKG_MANAGER install -y wget 2>&1 | tail -3
                command -v wget &>/dev/null && DOWNLOADER="wget"
            fi

            if [[ -n "$DOWNLOADER" ]]; then
                SCYTHER_BIN="$SCYTHER_INSTALL_DIR/scyther-linux"
                info "Downloading Scyther binary from $SCYTHER_URL ..."
                if [[ "$DOWNLOADER" == "wget" ]]; then
                    $SUDO wget --show-progress -O "$SCYTHER_BIN" "$SCYTHER_URL" && DOWNLOAD_OK=true || DOWNLOAD_OK=false
                else
                    $SUDO curl -fsSL -o "$SCYTHER_BIN" "$SCYTHER_URL" && DOWNLOAD_OK=true || DOWNLOAD_OK=false
                fi

                if $DOWNLOAD_OK && [[ -f "$SCYTHER_BIN" ]]; then
                    $SUDO chmod +x "$SCYTHER_BIN"
                    ok "Scyther binary downloaded and made executable: $SCYTHER_BIN"
                    # Verify it actually runs
                    if _test_scyther "$SCYTHER_BIN"; then
                        ok "Scyther binary verified — it runs correctly."
                        SCYTHER_OK=true
                    else
                        warn "Downloaded binary does not appear to execute correctly."
                        warn "It may need 32-bit libraries. Try:"
                        warn "  sudo dpkg --add-architecture i386"
                        warn "  sudo apt-get update"
                        warn "  sudo apt-get install libc6:i386 libstdc++6:i386"
                    fi
                else
                    err "Download failed."
                    warn "Download Scyther manually from:"
                    warn "  https://people.cispa.io/cas.cremers/scyther/"
                    warn "Then run:"
                    warn "  sudo mv scyther-linux /usr/local/bin/"
                    warn "  sudo chmod +x /usr/local/bin/scyther-linux"
                fi
            else
                err "No download tool (wget/curl) available."
                warn "Install wget:  sudo apt-get install wget"
                warn "Then re-run this setup script."
            fi
        fi
    fi
fi

# Final recheck: honour any pre-existing installation or one done outside
# the detection blocks above (e.g. a manually placed binary).
if ! $SCYTHER_OK && command -v scyther-linux &>/dev/null; then
    ok "scyther-linux is available: $(command -v scyther-linux)"
    SCYTHER_OK=true
fi

if ! $SCYTHER_OK; then
    warn "Scyther installation incomplete."
    warn "Protocol verification scripts will not work until scyther-linux is in your PATH."
fi

# ── 7. Create required project directories ───────────────────────────────────
section "Step 7 — Project Directories"

DIRS=(
    "$PROJECT_DIR/database"
    "$PROJECT_DIR/logs"
    "$PROJECT_DIR/results"
    "$PROJECT_DIR/attack_graphs"
)

for DIR in "${DIRS[@]}"; do
    if [[ -d "$DIR" ]]; then
        ok "Exists:  $DIR"
    else
        mkdir -p "$DIR"
        ok "Created: $DIR"
    fi
done

# ── 8. Make scripts executable ────────────────────────────────────────────────
section "Step 8 — Script Permissions"

SCRIPTS=(
    "$PROJECT_DIR/scripts/verify_protocols.sh"
    "$PROJECT_DIR/scripts/generate_graphs.sh"
    "$PROJECT_DIR/scripts/view_graphs.sh"
)

for SCRIPT in "${SCRIPTS[@]}"; do
    if [[ -f "$SCRIPT" ]]; then
        chmod +x "$SCRIPT"
        ok "chmod +x: $SCRIPT"
    else
        warn "Not found:  $SCRIPT"
    fi
done

# ── 9. Verify tools ───────────────────────────────────────────────────────────
section "Step 9 — Final Verification"

echo ""
echo -e "  ${BOLD}Tool            Status            Location${RESET}"
echo -e "  ${BLUE}──────────────  ────────────────  ─────────────────────────────────${RESET}"

# Python
if ${PYTHON_OK:-false} && command -v "${PYTHON_BIN:-python3}" &>/dev/null; then
    PY_LOC=$(command -v "${PYTHON_BIN:-python3}")
    PY_VER=$("${PYTHON_BIN:-python3}" -c "import sys; print('{}.{}'.format(*sys.version_info[:2]))")
    printf "  %-14s  ${GREEN}%-16s${RESET}  %s\n" "python3" "✅  v$PY_VER" "$PY_LOC"
else
    printf "  %-14s  ${RED}%-16s${RESET}  %s\n" "python3" "❌  NOT FOUND" "install: sudo apt-get install python3"
fi

# Scyther
if command -v scyther-linux &>/dev/null; then
    SCYTHER_LOC=$(command -v scyther-linux)
    printf "  %-14s  ${GREEN}%-16s${RESET}  %s\n" "scyther-linux" "✅  found" "$SCYTHER_LOC"
else
    printf "  %-14s  ${RED}%-16s${RESET}  %s\n" "scyther-linux" "❌  NOT FOUND" "see Step 6 notes above"
fi

# Graphviz
if command -v dot &>/dev/null; then
    DOT_LOC=$(command -v dot)
    printf "  %-14s  ${GREEN}%-16s${RESET}  %s\n" "graphviz (dot)" "✅  found" "$DOT_LOC"
else
    printf "  %-14s  ${YELLOW}%-16s${RESET}  %s\n" "graphviz (dot)" "⚠   not found" "sudo apt-get install graphviz"
fi

# xdot
if command -v xdot &>/dev/null; then
    XDOT_LOC=$(command -v xdot)
    printf "  %-14s  ${GREEN}%-16s${RESET}  %s\n" "xdot" "✅  found" "$XDOT_LOC"
else
    printf "  %-14s  ${YELLOW}%-16s${RESET}  %s\n" "xdot" "⚠   not found" "sudo apt-get install xdot"
fi

echo ""

# ── 10. Final summary & next steps ───────────────────────────────────────────
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║                   Setup Complete                            ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

if $SCYTHER_OK; then
    echo -e "  ${GREEN}${BOLD}✅  All core tools are installed and ready.${RESET}"
else
    echo -e "  ${YELLOW}${BOLD}⚠   Setup finished with warnings — check Step 6 above.${RESET}"
fi

echo ""
echo -e "${BOLD}  Next Steps:${RESET}"
echo -e "  ${CYAN}1.${RESET}  Run the auth CLI:         ${BOLD}python3 auth_cli/main.py${RESET}"
echo -e "  ${CYAN}2.${RESET}  Verify all protocols:     ${BOLD}./scripts/verify_protocols.sh${RESET}"
echo -e "  ${CYAN}3.${RESET}  Generate attack graphs:   ${BOLD}./scripts/generate_graphs.sh${RESET}"
echo -e "  ${CYAN}4.${RESET}  View graphs interactively:${BOLD}./scripts/view_graphs.sh${RESET}"
echo -e "  ${CYAN}5.${RESET}  Run attack simulations:   ${BOLD}python3 simulate_attacks.py${RESET}"
echo -e "  ${CYAN}6.${RESET}  Run the full demo:        ${BOLD}python3 demo.py${RESET}"
echo ""
echo -e "  ${BLUE}Default admin password: ${BOLD}Admin@Scyther1${RESET}"
echo ""
