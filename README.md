# BobFromSales 🤖

**IBM Storage Sales Project Centre** — Generuj profesjonalne dokumenty sprzedażowe z plików e-config CSV i Storage Modeller XLSX.

---

## 🚀 Szybki start (dla nowych użytkowników)

### Wymagania wstępne

Zanim zaczniesz, upewnij się, że masz zainstalowane:

| Wymaganie | Wersja | Jak sprawdzić |
|---|---|---|
| **Python** | 3.9 lub nowszy | `python --version` lub `python3 --version` |
| **pip** | dowolna | `pip --version` lub `pip3 --version` |

> **Nie masz Pythona?**
> - **Windows**: Pobierz z [python.org/downloads](https://www.python.org/downloads/) — zaznacz opcję **"Add Python to PATH"** podczas instalacji
> - **macOS**: Zainstaluj przez `brew install python3` lub pobierz z [python.org](https://www.python.org/downloads/)
> - **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian) lub `sudo dnf install python3` (Fedora)

---

### Instalacja i uruchomienie

#### 🍎 macOS / 🐧 Linux

Otwórz Terminal w folderze z aplikacją i uruchom:

```bash
bash start.sh
```

Skrypt automatycznie:
1. Sprawdzi wersję Pythona
2. Stworzy izolowane środowisko wirtualne (`venv`)
3. Zainstaluje wszystkie zależności
4. Uruchomi aplikację w przeglądarce

#### 🪟 Windows — PowerShell (zalecane)

Kliknij prawym przyciskiem myszy na folder z aplikacją → **„Otwórz w terminalu"** lub otwórz PowerShell i przejdź do folderu:

```powershell
.\start.ps1
```

Jeśli pojawi się błąd o polityce uruchamiania skryptów:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start.ps1
```

#### 🪟 Windows — Command Prompt (cmd.exe)

Dwukrotnie kliknij plik **`start.bat`** lub w cmd.exe:

```cmd
start.bat
```

---

### Pierwsze uruchomienie (krok po kroku)

Po uruchomieniu skryptu przeglądarka otworzy się automatycznie pod adresem `http://localhost:8501`.

**Przy kolejnych uruchomieniach** — ponownie użyj tego samego skryptu start.

---

## 📋 Jak używać aplikacji

### Krok 1 — Wgraj pliki

| Plik | Skąd go wziąć |
|---|---|
| **e-config CSV** | IBM e-config Cloud → skonfiguruj system → **Export CSV** |
| **Storage Modeller Capacity XLSX** | IBM Storage Modeller → raport pojemności → **Export XLSX** |
| **Storage Modeller Performance XLSX** *(opcjonalny)* | IBM Storage Modeller → raport wydajności → **Export XLSX** |

1. Kliknij **„Browse files"** przy każdym polu
2. Wgraj odpowiednie pliki
3. Kliknij **„▶ Parse Files"**

### Krok 2 — Uzupełnij dane

W sekcji **Project Details** wypełnij:
- **Client name** — nazwa klienta
- **Sales rep** — Twoje imię i nazwisko
- **Deal type** — typ transakcji
- **Discount %** — rabat (domyślnie 60%)
- **Due date** — termin złożenia oferty

### Krok 3 — Wygeneruj dokumenty

Przejdź do odpowiedniej zakładki:

| Zakładka | Co generuje |
|---|---|
| **Executive Summary** | Jednostronicowe podsumowanie dla zarządu (PL/EN) |
| **Technical RFP/RFI** | Odpowiedź na zapytanie techniczne (PL/EN) |
| **Special Bid** | Wniosek o special bid do IBM |
| **Projects** | Zapis i wczytywanie projektów |
| **System Info** | Szczegóły techniczne systemu |

Kliknij przycisk **„Generate … DOCX"** → pobierz plik `.docx`.

---

## 🗂️ Struktura projektu

```
BobFromSales/
├── app.py                          # Główna aplikacja Streamlit (punkt wejścia)
├── requirements.txt                # Lista zależności Pythona
├── start.sh                        # Skrypt uruchamiający (macOS/Linux)
├── start.bat                       # Skrypt uruchamiający (Windows cmd)
├── start.ps1                       # Skrypt uruchamiający (Windows PowerShell)
│
├── app/
│   ├── parsers/
│   │   └── econfig_parser.py       # Parser CSV + XLSX
│   ├── generators/
│   │   ├── exec_summary.py         # Generator Executive Summary DOCX
│   │   ├── rfp_generator.py        # Generator RFP/RFI DOCX
│   │   └── special_bid_generator.py# Generator Special Bid DOCX
│   ├── knowledge/
│   │   └── product_db.py           # Baza danych produktów IBM Storage
│   ├── assets/
│   │   ├── logos/                  # Logo IBM
│   │   └── images/                 # Zdjęcia produktów FlashSystem
│   └── templates/                  # Szablony DOCX (przyszłość)
│
├── projects/                       # Zapisane projekty (generowane automatycznie)
└── INPUT-FILES/                    # Przykładowe pliki wejściowe (do testów)
```

---

## 🔧 Rozwiązywanie problemów

### „python: command not found" / „python3: command not found"
Python nie jest zainstalowany lub nie jest dodany do PATH. Zainstaluj Pythona i dodaj go do PATH.

### „Port 8501 is already in use"
Inny proces używa portu. Uruchom na innym porcie:
```bash
streamlit run app.py --server.port 8502
```

### Błąd przy instalacji zależności (Windows)
Spróbuj uruchomić PowerShell jako **Administrator** lub użyj:
```cmd
pip install --user -r requirements.txt
```

### Aplikacja nie otwiera się w przeglądarce
Otwórz ręcznie: `http://localhost:8501`

### Plik CSV/XLSX nie jest parsowany
Upewnij się, że:
- CSV pochodzi z **IBM e-config Cloud** (nie edytowany ręcznie)
- XLSX pochodzi z **IBM Storage Modeller** i zawiera wymagane arkusze

---

## 🧪 Test smoke

Aby sprawdzić, czy aplikacja działa poprawnie bez UI:

```bash
python3 test_pipeline.py
```

Wymaga plików testowych w katalogu głównym:
- `TEST-FS5600_120TiB.csv`
- `TEST-FS5600_120TiB-summary.xlsx`
- `TEST-FS5600_120TiB-performance.xlsx`

---

## 📦 Funkcjonalności

| Funkcja | Status |
|---|---|
| Parser IBM e-config CSV (BOM, ceny, feature codes, support) | ✅ |
| Parser Storage Modeller capacity XLSX | ✅ |
| Parser Storage Modeller performance XLSX | ✅ |
| Generator **Executive Summary DOCX** (EN/PL) | ✅ |
| Generator **Technical RFP/RFI DOCX** (EN/PL) | ✅ |
| Generator **Special Bid DOCX** | ✅ |
| Suwak rabatu (domyślnie 60%) z ostrzeżeniem Special Bid >65% | ✅ |
| Zapis i wczytywanie projektów | ✅ |
| Streamlit web UI (lokalny) | ✅ |
