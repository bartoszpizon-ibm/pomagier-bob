#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  BobFromSales — skrypt uruchamiający (macOS / Linux)
#  Użycie: bash start.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

VENV_DIR=".venv"
APP_FILE="app.py"
PORT=8501

# Kolory (wyłącz jeśli terminal nie obsługuje)
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo ""
echo "  ██████╗  ██████╗ ██████╗ "
echo "  ██╔══██╗██╔═══██╗██╔══██╗"
echo "  ██████╔╝██║   ██║██████╔╝"
echo "  ██╔══██╗██║   ██║██╔══██╗"
echo "  ██████╔╝╚██████╔╝██████╔╝"
echo "  ╚═════╝  ╚═════╝ ╚═════╝ "
echo "  BobFromSales — IBM Storage Sales Project Centre"
echo ""

# 1. Sprawdź Pythona
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c 'import sys; print(sys.version_info >= (3, 9))')
        if [ "$VER" = "True" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}[BŁĄD] Python 3.9+ nie został znaleziony.${NC}"
    echo "       Zainstaluj Pythona: https://www.python.org/downloads/"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python: $($PYTHON --version)"

# 2. Utwórz lub użyj istniejącego venv
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Tworzę środowisko wirtualne..."
    $PYTHON -m venv "$VENV_DIR"
fi

# 3. Aktywuj venv i zainstaluj zależności
source "$VENV_DIR/bin/activate"

echo "[INFO] Sprawdzam / instaluję zależności..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo -e "${GREEN}[OK]${NC} Zależności zainstalowane."

# 4. Uruchom Streamlit
echo ""
echo -e "${YELLOW}[START]${NC} Uruchamiam aplikację na http://localhost:${PORT}"
echo "        Naciśnij Ctrl+C aby zatrzymać."
echo ""

streamlit run "$APP_FILE" \
    --server.port "$PORT" \
    --server.headless false \
    --browser.gatherUsageStats false
