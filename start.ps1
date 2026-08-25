# ─────────────────────────────────────────────────────────────────────────────
#  BobFromSales — skrypt uruchamiający (Windows PowerShell)
#  Użycie: .\start.ps1
#
#  Jeśli pojawia się błąd polityki:
#    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# ─────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$VENV_DIR = ".venv"
$APP_FILE = "app.py"
$PORT = 8501

Write-Host ""
Write-Host "  BobFromSales — IBM Storage Sales Project Centre" -ForegroundColor Cyan
Write-Host "  ================================================" -ForegroundColor DarkGray
Write-Host ""

# 1. Sprawdź Pythona
$pythonCmd = $null
foreach ($cmd in @("python", "python3")) {
    try {
        $ver = & $cmd -c "import sys; print(sys.version_info >= (3, 9))" 2>$null
        if ($ver -eq "True") {
            $pythonCmd = $cmd
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "[BŁĄD] Python 3.9+ nie został znaleziony." -ForegroundColor Red
    Write-Host "       Pobierz z: https://www.python.org/downloads/"
    Write-Host "       WAŻNE: Zaznacz 'Add Python to PATH' podczas instalacji!"
    Read-Host "Naciśnij Enter aby zamknąć"
    exit 1
}

$pyVer = & $pythonCmd --version
Write-Host "[OK] $pyVer" -ForegroundColor Green

# 2. Utwórz środowisko wirtualne (jeśli nie istnieje)
if (-not (Test-Path $VENV_DIR)) {
    Write-Host "[INFO] Tworzę środowisko wirtualne..."
    & $pythonCmd -m venv $VENV_DIR
}

# 3. Aktywuj venv
$activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    # Fallback na Scripts/activate dla starszych wersji
    $activateScript = Join-Path $VENV_DIR "Scripts\activate"
}
& $activateScript

# 4. Zainstaluj zależności
Write-Host "[INFO] Sprawdzam / instaluję zależności..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[BŁĄD] Błąd podczas instalacji zależności." -ForegroundColor Red
    Write-Host "       Spróbuj uruchomić PowerShell jako Administrator."
    Read-Host "Naciśnij Enter aby zamknąć"
    exit 1
}
Write-Host "[OK] Zależności zainstalowane." -ForegroundColor Green

# 5. Uruchom Streamlit
Write-Host ""
Write-Host "[START] Uruchamiam aplikację na http://localhost:$PORT" -ForegroundColor Yellow
Write-Host "        Naciśnij Ctrl+C aby zatrzymać."
Write-Host ""

streamlit run $APP_FILE `
    --server.port $PORT `
    --server.headless $false `
    --browser.gatherUsageStats false
