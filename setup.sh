#!/usr/bin/env bash
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

info()    { echo -e "${BOLD}$*${RESET}"; }
success() { echo -e "${GREEN}✓ $*${RESET}"; }
warn()    { echo -e "${YELLOW}! $*${RESET}"; }
die()     { echo -e "${RED}✗ $*${RESET}" >&2; exit 1; }

echo
info "Pomodoro Timer — setup"
echo "────────────────────────────────────"

# ── 1. OS check ──────────────────────────────────────────────────────────────
if [[ "$(uname -s)" != "Linux" ]]; then
  die "This app targets Linux (Ubuntu). Detected: $(uname -s)"
fi

# ── 2. System packages ───────────────────────────────────────────────────────
info "Checking system dependencies..."

MISSING_PKGS=()
dpkg -l libxcb-cursor0 &>/dev/null || MISSING_PKGS+=(libxcb-cursor0)

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
  warn "Missing packages: ${MISSING_PKGS[*]}"
  info "Installing via apt (may prompt for password)..."
  sudo apt-get install -y "${MISSING_PKGS[@]}"
fi
success "System dependencies OK"

# ── 3. uv ────────────────────────────────────────────────────────────────────
info "Checking uv..."

if ! command -v uv &>/dev/null; then
  warn "uv not found — installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Add to current session PATH
  export PATH="$HOME/.local/bin:$PATH"
fi

UV_VERSION=$(uv --version 2>&1)
success "uv: $UV_VERSION"

# ── 4. Python + dependencies ─────────────────────────────────────────────────
info "Installing Python 3.14 and PyQt6..."
uv sync
success "Dependencies installed"

# ── 5. Launcher ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$HOME/.local/bin/pomodoro"

mkdir -p "$HOME/.local/bin"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
cd "$SCRIPT_DIR"
exec uv run python main.py "\$@"
EOF
chmod +x "$LAUNCHER"
success "Launcher created at $LAUNCHER"

# ── 6. Done ──────────────────────────────────────────────────────────────────
echo
echo -e "${GREEN}${BOLD}All done!${RESET}"
echo
echo "  Run the app:   pomodoro"
echo "  Or directly:   uv run python main.py"
echo

# Warn if launcher dir isn't on PATH
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$HOME/.local/bin"; then
  warn "$HOME/.local/bin is not in your PATH."
  warn "Add this to your ~/.bashrc or ~/.zshrc:"
  echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo
fi
