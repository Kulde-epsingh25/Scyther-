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
SCYTHER_BIN="$SCYTHER_INSTALL_DIR/scyther-linux"

# Timeout (seconds) used when testing a candidate Scyther binary.
SCYTHER_TEST_TIMEOUT=5

# ── Helper: test that a Scyther binary actually runs ─────────────────────────
_test_scyther() {
    local bin="$1"
    local output rc
    output=$(timeout "${SCYTHER_TEST_TIMEOUT}s" "$bin" --help 2>&1)
    rc=$?
    [[ $rc -eq 124 ]] && return 1   # timed out — binary hung
    [[ $rc -eq 0   ]] && return 0   # exited cleanly
    echo "$output" | grep -qi "scyther\|usage\|option" && return 0
    return 1
}

# ── Helper: ensure wget or curl is available; set $DOWNLOADER ─────────────────
_ensure_downloader() {
    if command -v wget &>/dev/null; then
        DOWNLOADER="wget"
    elif command -v curl &>/dev/null; then
        DOWNLOADER="curl"
    else
        info "No download tool found — installing wget..."
        $SUDO $PKG_MANAGER install -y wget 2>&1 | tail -3
        if command -v wget &>/dev/null; then
            DOWNLOADER="wget"
        else
            DOWNLOADER=""
        fi
    fi
}

# ── Helper: fetch a single URL to a destination file ─────────────────────────
# Usage: _fetch <url> <dest>   Returns 0 on success, 1 on failure.
# On failure, prints the captured error output so the user can diagnose it.
_fetch() {
    local url="$1" dest="$2" errtmp
    errtmp=$(mktemp)
    local rc=0
    if [[ "$DOWNLOADER" == "wget" ]]; then
        $SUDO wget --show-progress -O "$dest" "$url" 2>"$errtmp" || rc=$?
    else
        $SUDO curl -fL --progress-bar -o "$dest" "$url" 2>"$errtmp" || rc=$?
    fi
    if [[ $rc -ne 0 ]] && [[ -s "$errtmp" ]]; then
        warn "    $(tail -3 "$errtmp")"
    fi
    rm -f "$errtmp"
    return $rc
}

# ── Helper: install binary after a successful download ────────────────────────
_install_scyther_bin() {
    local src="$1"
    $SUDO chmod +x "$src"
    ok "Binary made executable: $src"
    if _test_scyther "$src"; then
        ok "Scyther binary verified — it runs correctly."
        SCYTHER_OK=true
    else
        warn "Binary present but does not execute cleanly."
        warn "It may require 32-bit compatibility libraries:"
        warn "  sudo dpkg --add-architecture i386"
        warn "  sudo apt-get update && sudo apt-get install libc6:i386 libstdc++6:i386"
    fi
}

# ────────────────────────────────────────────────────────────────────────────
# 6a. scyther-linux already in PATH
# ────────────────────────────────────────────────────────────────────────────
if command -v scyther-linux &>/dev/null; then
    ok "scyther-linux already in PATH: $(command -v scyther-linux)"
    SCYTHER_OK=true

# ────────────────────────────────────────────────────────────────────────────
# 6b. 'scyther' installed (apt may use this name) — create symlink
# ────────────────────────────────────────────────────────────────────────────
elif command -v scyther &>/dev/null; then
    ok "'scyther' command found: $(command -v scyther)"
    info "Creating 'scyther-linux' symlink → scyther ..."
    SCYTHER_REAL=$(command -v scyther)
    $SUDO ln -sf "$SCYTHER_REAL" "$SCYTHER_INSTALL_DIR/scyther-linux"
    if command -v scyther-linux &>/dev/null; then
        ok "Symlink created: $SCYTHER_INSTALL_DIR/scyther-linux → $SCYTHER_REAL"
        SCYTHER_OK=true
    else
        warn "Symlink creation failed."
        warn "Try manually: sudo ln -sf $SCYTHER_REAL /usr/local/bin/scyther-linux"
    fi

else
    # ──────────────────────────────────────────────────────────────────────
    # 6c. Try apt-get install scyther
    # ──────────────────────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────────────────────
    # 6d. Download precompiled binary — multiple fallback sources
    # ──────────────────────────────────────────────────────────────────────
    if ! $SCYTHER_OK; then
        ARCH=$(uname -m)
        info "Scyther not available via apt — attempting binary download (arch: $ARCH)..."

        # Ordered list of download sources: "Label|URL"
        # Each entry is tried in turn; the first successful download wins.
        case "$ARCH" in
            x86_64)
                SCYTHER_SOURCES=(
                    "Official CISPA site|https://people.cispa.io/cas.cremers/scyther/scyther-linux"
                    "GitHub Releases — cascremers/scyther (latest)|https://github.com/cascremers/scyther/releases/latest/download/scyther-linux"
                    "GitHub Releases — cascremers/scyther v1.1.3|https://github.com/cascremers/scyther/releases/download/v1.1.3/scyther-linux"
                    "GitHub raw binary (master branch)|https://raw.githubusercontent.com/cascremers/scyther/master/binaries/scyther-linux"
                )
                ;;
            *)
                SCYTHER_SOURCES=()
                warn "No precompiled Scyther binary for architecture: $ARCH"
                warn "Will attempt build from source (Method 6e) below."
                ;;
        esac

        if [[ ${#SCYTHER_SOURCES[@]} -gt 0 ]]; then
            _ensure_downloader
        fi

        if [[ -n "${DOWNLOADER:-}" && ${#SCYTHER_SOURCES[@]} -gt 0 ]]; then
            TMPBIN=$(mktemp)
            SOURCE_NUM=0
            for SOURCE_ENTRY in "${SCYTHER_SOURCES[@]}"; do
                SOURCE_NUM=$((SOURCE_NUM + 1))
                SOURCE_LABEL="${SOURCE_ENTRY%%|*}"
                SOURCE_URL="${SOURCE_ENTRY##*|}"

                echo ""
                info "  [${SOURCE_NUM}/${#SCYTHER_SOURCES[@]}] Trying: $SOURCE_LABEL"
                info "        URL: $SOURCE_URL"

                if _fetch "$SOURCE_URL" "$TMPBIN" && [[ -s "$TMPBIN" ]]; then
                    $SUDO cp "$TMPBIN" "$SCYTHER_BIN"
                    rm -f "$TMPBIN"
                    ok "Downloaded from: $SOURCE_LABEL"
                    _install_scyther_bin "$SCYTHER_BIN"
                    $SCYTHER_OK && break
                else
                    warn "  ✗ Failed: $SOURCE_LABEL"
                    rm -f "$TMPBIN"
                    TMPBIN=$(mktemp)
                fi
            done
            rm -f "$TMPBIN"
        elif [[ ${#SCYTHER_SOURCES[@]} -gt 0 ]]; then
            err "No download tool (wget/curl) available."
            warn "Install wget:  sudo apt-get install wget"
            warn "Then re-run this setup script."
        fi
    fi

    # ──────────────────────────────────────────────────────────────────────
    # 6e. Build from source (last resort)
    # ──────────────────────────────────────────────────────────────────────
    if ! $SCYTHER_OK; then
        echo ""
        info "All binary download sources failed — attempting build from source..."
        info "Repository: https://github.com/cascremers/scyther"

        BUILD_OK=false

        # Ensure build tools are present
        BUILD_DEPS=(git cmake gcc make libssl-dev libgmp-dev flex bison)
        info "Installing build dependencies: ${BUILD_DEPS[*]} ..."
        if $SUDO $PKG_MANAGER install -y "${BUILD_DEPS[@]}" 2>&1 | tail -5; then
            ok "Build dependencies installed."
            BUILD_DEPS_OK=true
        else
            warn "Could not install all build dependencies."
            BUILD_DEPS_OK=false
        fi

        if $BUILD_DEPS_OK; then
            SCYTHER_SRC_DIR=$(mktemp -d)
            info "Cloning Scyther source to $SCYTHER_SRC_DIR ..."

            # Try GitHub first, then fall back to the official Git repo
            SCYTHER_REPO_SOURCES=(
                "GitHub (cascremers/scyther)|https://github.com/cascremers/scyther.git"
                "Official Scyther Git|https://people.cispa.io/cas.cremers/scyther.git"
            )

            for REPO_ENTRY in "${SCYTHER_REPO_SOURCES[@]}"; do
                REPO_LABEL="${REPO_ENTRY%%|*}"
                REPO_URL="${REPO_ENTRY##*|}"
                info "  Cloning from: $REPO_LABEL ($REPO_URL)"
                if git clone --depth 1 "$REPO_URL" "$SCYTHER_SRC_DIR/scyther" 2>&1 | tail -3; then
                    ok "Clone successful: $REPO_LABEL"
                    CLONE_OK=true
                    break
                else
                    warn "  ✗ Clone failed: $REPO_LABEL"
                    CLONE_OK=false
                    rm -rf "$SCYTHER_SRC_DIR/scyther"
                fi
            done

            if ${CLONE_OK:-false}; then
                info "Building Scyther..."
                BUILD_DIR="$SCYTHER_SRC_DIR/scyther/src"
                BUILD_LOG=$(mktemp)
                if [[ -d "$BUILD_DIR" ]] && \
                   (cd "$BUILD_DIR" && cmake -D TARGETOS=Unix . 2>&1 | tee -a "$BUILD_LOG" | tail -5) && \
                   (cd "$BUILD_DIR" && make --jobs "$(nproc)" 2>&1 | tee -a "$BUILD_LOG" | tail -5); then

                    # The Scyther build outputs the binary directly in src/
                    BUILT_BIN="$BUILD_DIR/scyther-linux"
                    if [[ -f "$BUILT_BIN" ]]; then
                        $SUDO cp "$BUILT_BIN" "$SCYTHER_BIN"
                        ok "Built binary installed to: $SCYTHER_BIN"
                        _install_scyther_bin "$SCYTHER_BIN"
                        BUILD_OK=true
                    else
                        # Fallback: search for exact expected names in src/ and verify
                        BUILT_BIN=$(find "$BUILD_DIR" -maxdepth 2 -type f \
                                    -name "scyther-linux" -executable | head -1)
                        if [[ -n "$BUILT_BIN" ]] && _test_scyther "$BUILT_BIN"; then
                            $SUDO cp "$BUILT_BIN" "$SCYTHER_BIN"
                            ok "Built binary installed to: $SCYTHER_BIN"
                            _install_scyther_bin "$SCYTHER_BIN"
                            BUILD_OK=true
                        else
                            warn "Build completed but could not locate a working output binary."
                            warn "Full build log saved to: $BUILD_LOG"
                        fi
                    fi
                else
                    warn "cmake/make build failed."
                    warn "Full build log saved to: $BUILD_LOG"
                    warn "Last 20 lines:"
                    tail -20 "$BUILD_LOG" | while IFS= read -r line; do
                        warn "  $line"
                    done
                fi
                # Clean up build log unless it contains useful error information
                $SCYTHER_OK && rm -f "$BUILD_LOG"
            fi

            rm -rf "$SCYTHER_SRC_DIR"
        fi

        if ! $BUILD_OK && ! $SCYTHER_OK; then
            err "All Scyther installation methods failed."
            warn "Manual installation steps:"
            warn "  Option A — Download binary:"
            warn "    wget https://people.cispa.io/cas.cremers/scyther/scyther-linux"
            warn "    sudo mv scyther-linux /usr/local/bin/"
            warn "    sudo chmod +x /usr/local/bin/scyther-linux"
            warn ""
            warn "  Option B — Build from source:"
            warn "    sudo apt-get install git cmake gcc libssl-dev libgmp-dev flex bison"
            warn "    git clone https://github.com/cascremers/scyther.git"
            warn "    cd scyther/src && cmake . && make"
            warn "    sudo cp scyther /usr/local/bin/scyther-linux"
        fi
    fi
fi

# ── Final recheck ─────────────────────────────────────────────────────────────
# Honour any pre-existing installation or a manually placed binary.
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
