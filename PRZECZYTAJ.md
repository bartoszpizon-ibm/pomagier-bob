# BobFromSales — Instrukcja uruchomienia

## Jak uruchomić aplikację — 5 kroków

---

### Krok 1 — Zainstaluj Pythona (jednorazowo)

Pobierz Python 3.9 lub nowszy: **https://www.python.org/downloads/**

> ⚠️ **Windows:** podczas instalacji zaznacz opcję **"Add Python to PATH"**

---

### Krok 2 — Wypakuj archiwum

Wypakuj plik `BobFromSales_SHARE.zip` do dowolnego folderu, np. `C:\BobFromSales\` (Windows) lub `~/BobFromSales/` (Mac).

---

### Krok 3 — Uruchom aplikację

**Windows** — dwukliknij plik:
```
start.bat
```

**macOS / Linux** — otwórz Terminal w folderze z aplikacją i wpisz:
```
bash start.sh
```

---

### Krok 4 — Poczekaj na pierwsze uruchomienie (~1–2 min)

Skrypt automatycznie:
- tworzy izolowane środowisko Python (`.venv`)
- pobiera i instaluje wymagane biblioteki

> Każde kolejne uruchomienie jest natychmiastowe (środowisko już istnieje).

---

### Krok 5 — Otwórz w przeglądarce

Aplikacja uruchamia się pod adresem:

## 👉 http://localhost:8501

Przeglądarka otworzy się automatycznie. Jeśli nie — wklej adres ręcznie.

---

## Zatrzymanie aplikacji

| System | Sposób |
|--------|--------|
| Windows | zamknij okno terminala (cmd) |
| macOS / Linux | naciśnij `Ctrl+C` w Terminalu |

---

## Wymagania systemowe

- Python 3.9 lub nowszy
- Windows 10/11 lub macOS 12+ lub Linux
- Połączenie z internetem (tylko przy pierwszym uruchomieniu — do pobrania bibliotek)
- ~300 MB wolnego miejsca na dysku
