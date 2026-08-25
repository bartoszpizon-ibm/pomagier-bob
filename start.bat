@echo off
:: ─────────────────────────────────────────────────────────────────────────────
::  BobFromSales — skrypt uruchamiający (Windows cmd)
::  Użycie: dwukliknij start.bat  lub  uruchom z cmd.exe
:: ─────────────────────────────────────────────────────────────────────────────

title BobFromSales — IBM Storage Sales Project Centre
chcp 65001 > nul 2>&1

echo.
echo   ██████╗  ██████╗ ██████╗
echo   ██╔══██╗██╔═══██╗██╔══██╗
echo   ██████╔╝██║   ██║██████╔╝
echo   ██╔══██╗██║   ██║██╔══██╗
echo   ██████╔╝╚██████╔╝██████╔╝
echo   ╚═════╝  ╚═════╝ ╚═════╝
echo   BobFromSales — IBM Storage Sales Project Centre
echo.

:: 1. Sprawdz Pythona
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [BLAD] Python nie zostal znaleziony.
    echo        Pobierz i zainstaluj Pythona 3.9+ z: https://www.python.org/downloads/
    echo        WAZNE: Zaznacz "Add Python to PATH" podczas instalacji!
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER%

:: 2. Utworz srodowisko wirtualne (jesli nie istnieje)
if not exist ".venv\" (
    echo [INFO] Tworze srodowisko wirtualne...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [BLAD] Nie udalo sie utworzyc srodowiska wirtualnego.
        pause
        exit /b 1
    )
)

:: 3. Aktywuj venv
call .venv\Scripts\activate.bat

:: 4. Zainstaluj zaleznosci
echo [INFO] Sprawdzam / instaluje zaleznosci...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if %errorlevel% neq 0 (
    echo [BLAD] Blad podczas instalacji zaleznosci.
    echo        Sprobuj uruchomic jako Administrator.
    pause
    exit /b 1
)
echo [OK] Zaleznosci zainstalowane.

:: 5. Uruchom Streamlit
echo.
echo [START] Uruchamiam aplikacje na http://localhost:8501
echo         Zamknij to okno aby zatrzymac aplikacje.
echo.

streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false

pause
