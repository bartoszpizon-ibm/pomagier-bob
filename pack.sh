#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  BobFromSales — skrypt pakujący projekt do dystrybucji
#  Użycie: bash pack.sh
#  Tworzy: BobFromSales_vYYYYMMDD.zip  +  BobFromSales_SHARE.zip (kopię)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

VERSION=$(date +%Y%m%d)
OUTPUT="BobFromSales_v${VERSION}.zip"
SHARE="BobFromSales_SHARE.zip"

echo "[INFO] Pakuję projekt do: ${OUTPUT}"

# Usuń poprzednie paczki jeśli istnieją
rm -f "$OUTPUT" "$SHARE"

# Lista plików i folderów do dołączenia
zip -r "$OUTPUT" \
    app.py \
    requirements.txt \
    PRZECZYTAJ.md \
    README.md \
    start.sh \
    start.bat \
    start.ps1 \
    app/ \
    -x "**/__pycache__/*" \
    -x "**/*.pyc" \
    -x "**/*.pyo" \
    -x "**/.DS_Store" \
    -x "app/.DS_Store"

# Kopia do dystrybucji (stała nazwa)
cp "$OUTPUT" "$SHARE"

# Wypisz zawartość
echo ""
echo "[OK] Paczki gotowe:"
echo "     ${OUTPUT}  ($(du -sh "$OUTPUT" | cut -f1))"
echo "     ${SHARE}   (do dystrybucji — stała nazwa)"
echo ""
echo "Zawartość:"
zip -sf "$OUTPUT"
