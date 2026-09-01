# Ace of Sales ♠ `v0.9.0-beta`

**IBM Storage Sales Project Centre** — Generate professional sales documents from IBM e-config CSV and Storage Modeller XLSX exports in seconds.

> **Beta release** — core features are stable and production-ready. Some product lines and language options are still in active development.

---

## ✨ What It Does

| Document | Description |
|---|---|
| 📋 **Executive Summary** | One-page management summary with IBM branding, product photo, full tech spec and pricing |
| 📝 **Technical RFP / RFI** | Requirements table pre-filled with your exact config values (capacity, RAID, ports, cache, support SLA) |
| 💼 **Special Bid Questionnaire** | Pre-filled HW Special Bid pricing request (Sections A/B/C) with auto-generated deal narrative |
| ✍️ **Bid Justification** | Ready-to-paste Business Justification text for IBM pricers |

All documents are generated as `.docx` — ready to send or edit in Microsoft Word.

---

## 🌐 Supported Languages

| Language | Executive Summary | RFP / RFI | Special Bid |
|---|---|---|---|
| 🇬🇧 **English** | ✅ | ✅ | ✅ |
| 🇵🇱 **Polish** | ✅ | ✅ | ✅ (EN template, PL narrative) |

Language is selected per-document via a toggle in the Generate panel.

---

## 🗄️ Supported Product Lines

| Product Line | Status |
|---|---|
| ⚡ **IBM FlashSystem** (FS5000 · FS5600 · FS7600 · FS9600 · FSc200) | ✅ Live |
| 🔗 **IBM SAN b-type switches** (SAN24B-7 · SAN64B-7 · SAN256B-7) | ✅ Live |
| 🗂️ **IBM Storage Scale** (ESS 3500 · ESS 6000) | ✅ Live |
| ☁️ Storage Fusion | 🔜 Coming soon |
| 🖥️ IBM Power Server | 🔜 Coming soon |

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | How to check |
|---|---|---|
| **Python** | 3.9 or newer | `python --version` or `python3 --version` |
| **pip** | any | `pip --version` or `pip3 --version` |

> **Don't have Python?**
> - **Windows**: Download from [python.org/downloads](https://www.python.org/downloads/) — check **"Add Python to PATH"** during installation
> - **macOS**: `brew install python3` or download from [python.org](https://www.python.org/downloads/)
> - **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian) or `sudo dnf install python3` (Fedora)

---

### Installation & Launch

#### 🍎 macOS / 🐧 Linux

Open Terminal in the application folder:

```bash
bash start.sh
```

The script will automatically:
1. Check your Python version
2. Create an isolated virtual environment (`venv`)
3. Install all dependencies
4. Launch the application in your browser at `http://localhost:8501`

#### 🪟 Windows — PowerShell (recommended)

Right-click the application folder → **"Open in Terminal"**, or open PowerShell and navigate to the folder:

```powershell
.\start.ps1
```

If you get a script execution policy error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start.ps1
```

#### 🪟 Windows — Command Prompt (cmd.exe)

Double-click **`start.bat`** or run in cmd.exe:

```cmd
start.bat
```

---

## 📋 How to Use

### Step 1 — Select Product Line & Upload Files

Choose your product line (FlashSystem, Storage Scale, or SAN), then upload:

| File | Required | Where to get it |
|---|---|---|
| **e-config CSV** | ✅ Always | IBM e-config Cloud → configure system → **Export CSV** |
| **StorM Capacity XLSX** | ⚡ FlashSystem / Scale | IBM Storage Modeller → capacity report → **Export XLSX** |
| **StorM Performance XLSX** | Optional | IBM Storage Modeller → performance report → **Export XLSX** |

> **CSV-only mode**: If you upload only the e-config CSV (no XLSX), the app runs in *CSV-only mode* — capacity is estimated from drive configuration. Sufficient for **Special Bid** generation; Exec Summary and RFP benefit from the full XLSX data.

Click **"Parse Files →"** to process.

### Step 2 — Fill in Project Details

| Field | Description |
|---|---|
| **Client name** | End-user / customer name |
| **Sales representative** | Your name (IBM rep) |
| **Deal type** | Workload scenario — auto-fills narrative texts |
| **Requested MEP** | Target end-user price; Discount % updates automatically |
| **Due date** | Bid / RFP submission deadline |

### Step 3 — Generate Documents

Navigate to the relevant tab:

| Tab | Generates |
|---|---|
| **Executive Summary** | One-page management summary (EN / PL) |
| **RFP / RFI** | Technical requirements response (EN / PL) |
| **Special Bid** | IBM HW Special Bid Questionnaire (Sections A/B/C) |
| **Projects** | Save and load projects |

Click **"Generate … →"** → download the `.docx` file.

### Bid Justification page

Navigate to **Bid Justification** in the top nav bar to generate a ready-to-paste Business Justification text for IBM pricers — no config upload required.

---

## 🗂️ Project Structure

```
AceOfSales/
├── app.py                              # Main Streamlit application (entry point)
├── requirements.txt                    # Python dependencies
├── start.sh                            # Launch script (macOS/Linux)
├── start.bat                           # Launch script (Windows cmd)
├── start.ps1                           # Launch script (Windows PowerShell)
│
├── app/
│   ├── parsers/
│   │   ├── econfig_parser.py           # FlashSystem e-config CSV + XLSX parser
│   │   ├── scale_parser.py             # Storage Scale CSV + XLSX parser
│   │   ├── san_parser.py               # SAN b-type switch CSV parser
│   │   └── bid_parser.py               # Special Bid DOCX pre-fill parser
│   ├── generators/
│   │   ├── exec_summary.py             # FlashSystem Executive Summary DOCX
│   │   ├── rfp_generator.py            # FlashSystem RFP/RFI DOCX
│   │   ├── special_bid_generator.py    # FlashSystem Special Bid DOCX
│   │   ├── san_rfp_generator.py        # SAN RFP / Specification DOCX
│   │   ├── scale_exec_summary.py       # Storage Scale Executive Summary DOCX
│   │   ├── scale_rfp_generator.py      # Storage Scale RFP DOCX
│   │   ├── scale_special_bid_generator.py  # Storage Scale Special Bid DOCX
│   │   └── bid_justification.py        # Bid Justification text generator
│   ├── knowledge/
│   │   └── product_db.py               # IBM Storage product database (models, docs URLs)
│   ├── assets/
│   │   ├── logos/                      # IBM logos (PNG)
│   │   └── images/                     # FlashSystem / Scale product images
│   └── templates/                      # DOCX base templates
│
└── projects/                           # Saved projects (auto-generated, git-ignored)
```

---

## 🔧 Troubleshooting

### `python: command not found` / `python3: command not found`
Python is not installed or not added to PATH. Install Python 3.9+ and add it to PATH.

### `Port 8501 is already in use`
Another process is using the port. Run on a different port:
```bash
streamlit run app.py --server.port 8502
```

### Dependency installation error (Windows)
Try running PowerShell as **Administrator** or use:
```cmd
pip install --user -r requirements.txt
```

### App doesn't open in browser
Open manually: `http://localhost:8501`

### CSV/XLSX file not parsed
- The CSV must come from **IBM e-config Cloud** (not manually edited)
- The XLSX must come from **IBM Storage Modeller** and contain the required sheets

---

## 🧪 Smoke Test

To verify the pipeline works correctly without the UI:

```bash
python3 test_pipeline.py
```

---

## 📦 Features

| Feature | Status |
|---|---|
| IBM e-config CSV parser (BOM, prices, feature codes, support) | ✅ |
| Storage Modeller Capacity XLSX parser | ✅ |
| Storage Modeller Performance XLSX parser | ✅ |
| SAN b-type switch CSV parser | ✅ |
| Storage Scale ESS CSV + XLSX parser | ✅ |
| **Executive Summary DOCX** — FlashSystem · Scale · SAN (EN/PL) | ✅ |
| **Technical RFP / RFI DOCX** — FlashSystem · Scale · SAN (EN/PL) | ✅ |
| **Special Bid DOCX** — FlashSystem · Scale · SAN | ✅ |
| **Bid Justification** text generator | ✅ |
| CSV-only mode (no XLSX required for Special Bid) | ✅ |
| Auto-generated deal narratives (8 deal types, multiple variants) | ✅ |
| Discount / MEP calculator with Special Bid warning | ✅ |
| Save and load projects (JSON) | ✅ |
| IBM.com design system UI (IBM Plex Sans, Carbon palette) | ✅ |
| Storage Fusion support | 🔜 |
| IBM Power Server support | 🔜 |

---

## 📄 License

Internal IBM sales tooling. Not for external distribution.
