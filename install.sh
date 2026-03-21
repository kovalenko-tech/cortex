#!/bin/bash
set -e

REPO="kovalenko-tech/codeprep"
INSTALL_DIR="${HOME}/.codeprep"
BIN_DIR="${HOME}/.local/bin"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}  CodePrep — Project Knowledge Base for Claude Code${NC}"
echo "  https://github.com/${REPO}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}Error: Python 3.11+ is required.${NC}"
  echo "  Install: https://python.org/downloads"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED="3.11"
if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} Python ${PYTHON_VERSION}"
else
  echo -e "${RED}Error: Python 3.11+ required (found ${PYTHON_VERSION}).${NC}"
  exit 1
fi

# Check git
if command -v git &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} git $(git --version | awk '{print $3}')"
else
  echo -e "${RED}Error: git is required.${NC}"
  exit 1
fi

# Download
echo ""
echo -e "  ${BLUE}→${NC} Downloading codeprep..."

mkdir -p "${INSTALL_DIR}"

if command -v curl &>/dev/null; then
  curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/codeprep/cli.py" \
    -o "${INSTALL_DIR}/cli.py"
  curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/codeprep/__init__.py" \
    -o "${INSTALL_DIR}/__init__.py"
elif command -v wget &>/dev/null; then
  wget -qO "${INSTALL_DIR}/cli.py" \
    "https://raw.githubusercontent.com/${REPO}/main/codeprep/cli.py"
  wget -qO "${INSTALL_DIR}/__init__.py" \
    "https://raw.githubusercontent.com/${REPO}/main/codeprep/__init__.py"
else
  echo -e "${RED}Error: curl or wget is required.${NC}"
  exit 1
fi

# Install dependencies
echo -e "  ${BLUE}→${NC} Installing dependencies..."
python3 -m pip install --quiet --upgrade gitpython click rich 2>/dev/null || \
  python3 -m pip install --quiet gitpython click rich

# Create wrapper script
mkdir -p "${BIN_DIR}"
cat > "${BIN_DIR}/codeprep" << WRAPPER
#!/bin/bash
exec python3 "${INSTALL_DIR}/cli.py" "\$@"
WRAPPER
chmod +x "${BIN_DIR}/codeprep"

# Add to PATH if needed
SHELL_RC=""
case "${SHELL}" in
  */zsh)  SHELL_RC="${HOME}/.zshrc" ;;
  */bash) SHELL_RC="${HOME}/.bashrc" ;;
esac

if [[ -n "${SHELL_RC}" ]] && ! grep -q "${BIN_DIR}" "${SHELL_RC}" 2>/dev/null; then
  echo "" >> "${SHELL_RC}"
  echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> "${SHELL_RC}"
fi

export PATH="${BIN_DIR}:${PATH}"

echo ""
echo -e "  ${GREEN}✓${NC} codeprep installed successfully!"
echo ""
echo -e "  ${BOLD}Usage:${NC}"
echo "    codeprep analyze          # analyze current project"
echo "    codeprep context <file>   # get context for a file"
echo "    codeprep security         # security audit only"
echo ""
echo -e "  ${BOLD}Quick start:${NC}"
echo "    cd your-project"
echo "    codeprep analyze"
echo ""
if ! command -v codeprep &>/dev/null; then
  echo -e "  ${BLUE}Note:${NC} Restart your shell or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
fi
