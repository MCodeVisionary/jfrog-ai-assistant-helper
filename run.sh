#!/usr/bin/env bash
# =============================================================================
#  JFrog MCP Gateway — Bootstrap (macOS / Linux)
#  Usage:  bash run.sh
#
#  What this script does:
#    1. Detects your OS and architecture
#    2. Installs Python 3.9+ if missing
#    3. Installs / upgrades pip
#    4. Creates an isolated virtual environment (.venv)
#    5. Activates it and runs jfrog_mcp_setup.py
# =============================================================================

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}  ℹ️   $*${RESET}"; }
success() { echo -e "${GREEN}  ✅  $*${RESET}"; }
warn()    { echo -e "${YELLOW}  ⚠️   $*${RESET}"; }
err()     { echo -e "${RED}  ❌  $*${RESET}"; }
doing()   { echo -ne "  ⏳  $* ... "; }
done_ok() { echo -e "${GREEN}done${RESET}"; }

# ── Detect OS and architecture ────────────────────────────────────────────────
OS="$(uname -s)"          # Darwin | Linux
ARCH="$(uname -m)"        # x86_64 | arm64 | aarch64
DISTRO=""
PKG_MGR=""

if [[ "$OS" == "Linux" ]]; then
  if   command -v apt-get &>/dev/null; then PKG_MGR="apt";  DISTRO="debian"
  elif command -v dnf     &>/dev/null; then PKG_MGR="dnf";  DISTRO="fedora"
  elif command -v yum     &>/dev/null; then PKG_MGR="yum";  DISTRO="rhel"
  elif command -v pacman  &>/dev/null; then PKG_MGR="pacman"; DISTRO="arch"
  elif command -v zypper  &>/dev/null; then PKG_MGR="zypper"; DISTRO="suse"
  fi
fi

echo ""
echo -e "${BOLD}${CYAN}"
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║     JFrog MCP Gateway  —  Bootstrap                 ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"
info "OS: $OS  |  Arch: $ARCH  |  Distro: ${DISTRO:-n/a}  |  Package manager: ${PKG_MGR:-none detected}"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 1 — Python 3.9+
# ─────────────────────────────────────────────────────────────────────────────
MIN_MAJOR=3
MIN_MINOR=9
PYTHON_CMD=""

find_python() {
  # Try python3 first, then python, then explicit versioned binaries
  for cmd in python3 python python3.13 python3.12 python3.11 python3.10 python3.9; do
    if command -v "$cmd" &>/dev/null; then
      local ver
      ver="$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
      local major minor
      major="${ver%%.*}"
      minor="${ver##*.}"
      if [[ "$major" -ge "$MIN_MAJOR" && "$minor" -ge "$MIN_MINOR" ]] 2>/dev/null; then
        echo "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

echo -e "${BOLD}[1/4]  Python 3.${MIN_MINOR}+${RESET}"

if PYTHON_CMD="$(find_python)"; then
  success "Python found: $PYTHON_CMD  ($($PYTHON_CMD --version 2>&1))"
else
  warn "Python 3.${MIN_MINOR}+ not found — installing now..."

  if [[ "$OS" == "Darwin" ]]; then
    if command -v brew &>/dev/null; then
      doing "brew install python@3.11"
      brew install python@3.11 &>/dev/null
      done_ok
      # Homebrew may install to a non-PATH location; link it
      brew link --overwrite python@3.11 &>/dev/null || true
    else
      warn "Homebrew not found. Installing Homebrew first..."
      doing "Installing Homebrew"
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      done_ok
      # Add brew to PATH for this session
      if [[ "$ARCH" == "arm64" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
      else
        eval "$(/usr/local/bin/brew shellenv)"
      fi
      doing "brew install python@3.11"
      brew install python@3.11 &>/dev/null
      done_ok
    fi

  elif [[ "$OS" == "Linux" ]]; then
    case "$PKG_MGR" in
      apt)
        doing "apt-get install python3.11 python3.11-venv python3-pip"
        sudo apt-get update -qq
        # Try 3.11, fall back to whatever 3.x is available
        sudo apt-get install -y python3.11 python3.11-venv python3-pip 2>/dev/null || \
        sudo apt-get install -y python3 python3-venv python3-pip
        done_ok
        ;;
      dnf)
        doing "dnf install python3.11 python3-pip"
        sudo dnf install -y python3.11 python3-pip 2>/dev/null || \
        sudo dnf install -y python3 python3-pip
        done_ok
        ;;
      yum)
        doing "yum install python3 python3-pip"
        sudo yum install -y python3 python3-pip
        done_ok
        ;;
      pacman)
        doing "pacman -S python python-pip"
        sudo pacman -Sy --noconfirm python python-pip
        done_ok
        ;;
      zypper)
        doing "zypper install python3 python3-pip"
        sudo zypper install -y python3 python3-pip
        done_ok
        ;;
      *)
        # Fallback: try pyenv
        warn "No recognised package manager found. Trying pyenv..."
        if ! command -v pyenv &>/dev/null; then
          doing "Installing pyenv"
          curl -fsSL https://pyenv.run | bash
          export PYENV_ROOT="$HOME/.pyenv"
          export PATH="$PYENV_ROOT/bin:$PATH"
          eval "$(pyenv init -)"
          done_ok
        fi
        doing "pyenv install 3.11.9"
        pyenv install -s 3.11.9
        pyenv global 3.11.9
        done_ok
        ;;
    esac
  else
    err "Unsupported OS: $OS"
    err "Please install Python 3.${MIN_MINOR}+ manually from https://python.org"
    exit 1
  fi

  # Try to find Python again after install
  if PYTHON_CMD="$(find_python)"; then
    success "Python installed: $PYTHON_CMD  ($($PYTHON_CMD --version 2>&1))"
  else
    # Last resort: try common post-install locations
    for path in /usr/bin/python3.11 /usr/local/bin/python3.11 \
                "$HOME/.pyenv/shims/python3" /opt/homebrew/bin/python3.11; do
      if [[ -x "$path" ]]; then
        PYTHON_CMD="$path"
        success "Python found at $path"
        break
      fi
    done
    if [[ -z "$PYTHON_CMD" ]]; then
      err "Python installation succeeded but the command is still not on PATH."
      err "Please restart your terminal and re-run:  bash run.sh"
      exit 1
    fi
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 2 — pip
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[2/4]  pip${RESET}"

if "$PYTHON_CMD" -m pip --version &>/dev/null; then
  success "pip already available  ($($PYTHON_CMD -m pip --version 2>&1 | head -1))"
else
  warn "pip not found — installing via ensurepip / get-pip.py..."
  if "$PYTHON_CMD" -m ensurepip --upgrade &>/dev/null; then
    success "pip installed via ensurepip"
  else
    doing "Downloading get-pip.py"
    curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    done_ok
    doing "Running get-pip.py"
    "$PYTHON_CMD" /tmp/get-pip.py --quiet
    done_ok
    success "pip installed via get-pip.py"
  fi
fi

# Upgrade pip quietly
doing "Upgrading pip to latest"
"$PYTHON_CMD" -m pip install --upgrade pip --quiet
done_ok

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 3 — Virtual environment
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[3/4]  Virtual environment (.venv)${RESET}"

VENV_DIR="$(dirname "$0")/.venv"

# Check if venv module is available
if ! "$PYTHON_CMD" -m venv --help &>/dev/null; then
  warn "venv module missing — installing python3-venv..."
  if [[ "$PKG_MGR" == "apt" ]]; then
    PY_VER=$("$PYTHON_CMD" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    sudo apt-get install -y "python${PY_VER}-venv" python3-venv &>/dev/null || true
  fi
fi

if [[ -d "$VENV_DIR" ]]; then
  # Validate existing venv matches our Python version requirement
  VENV_PY="$VENV_DIR/bin/python"
  if [[ -x "$VENV_PY" ]]; then
    VENV_VER="$("$VENV_PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")"
    VENV_MAJOR="${VENV_VER%%.*}"
    VENV_MINOR="${VENV_VER##*.}"
    if [[ "$VENV_MAJOR" -ge "$MIN_MAJOR" && "$VENV_MINOR" -ge "$MIN_MINOR" ]] 2>/dev/null; then
      success "Existing .venv is valid  (Python $VENV_VER)"
    else
      warn "Existing .venv is outdated (Python $VENV_VER) — recreating..."
      rm -rf "$VENV_DIR"
      doing "Creating new .venv with $PYTHON_CMD"
      "$PYTHON_CMD" -m venv "$VENV_DIR"
      done_ok
      success ".venv recreated"
    fi
  else
    warn ".venv exists but looks broken — recreating..."
    rm -rf "$VENV_DIR"
    doing "Creating .venv"
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    done_ok
    success ".venv created"
  fi
else
  doing "Creating .venv with $PYTHON_CMD"
  "$PYTHON_CMD" -m venv "$VENV_DIR"
  done_ok
  success ".venv created at $VENV_DIR"
fi

# Activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
info "Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip inside venv
doing "Upgrading pip inside .venv"
python -m pip install --upgrade pip --quiet
done_ok

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 4 — Run the setup script
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[4/4]  Launching JFrog MCP Gateway setup${RESET}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETUP_SCRIPT="$SCRIPT_DIR/jfrog_mcp_setup.py"

if [[ ! -f "$SETUP_SCRIPT" ]]; then
  err "jfrog_mcp_setup.py not found in $SCRIPT_DIR"
  err "Make sure both files are in the same folder."
  exit 1
fi

python "$SETUP_SCRIPT"
