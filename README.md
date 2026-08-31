# BobFromSales 🤖

**IBM Storage Sales Project Centre** — Generate professional sales documents from e-config CSV and Storage Modeller XLSX files.

---

## 🚀 Quick Start

### Prerequisites

Make sure you have the following installed:

| Requirement | Version | How to check |
|---|---|---|
| **Python** | 3.9 or newer | `python --version` or `python3 --version` |
| **pip** | any | `pip --version` or `pip3 --version` |

> **Don't have Python?**
> - **Windows**: Download from [python.org/downloads](https://www.python.org/downloads/) — check **"Add Python to PATH"** during installation
> - **macOS**: Install via `brew install python3` or download from [python.org](https://www.python.org/downloads/)
> - **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian) or `sudo dnf install python3` (Fedora)

---

### Installation & Launch

#### 🍎 macOS / 🐧 Linux

Open Terminal in the application folder and run:

```bash
bash start.sh
```

The script will automatically:
1. Check your Python version
2. Create an isolated virtual environment (`venv`)
3. Install all dependencies
4. Launch the application in your browser

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

### First Run

After running the script, your browser will open automatically at `http://localhost:8501`.

**On subsequent runs** — use the same start script again.

---

## 📋 How to Use

### Step 1 — Upload Files

| File | Where to get it |
|---|---|
| **e-config CSV** | IBM e-config Cloud → configure system → **Export CSV** |
| **Storage Modeller Capacity XLSX** | IBM Storage Modeller → capacity report → **Export XLSX** |
| **Storage Modeller Performance XLSX** *(optional)* | IBM Storage Modeller → performance report → **Export XLSX** |

1. Click **"Browse files"** for each field
2. Upload the appropriate files
3. Click **"▶ Parse Files"**

### Step 2 — Fill in Project Details

In the **Project Details** section, fill in:
- **Client name** — customer name
- **Sales rep** — your name
- **Deal type** — transaction type
- **Discount %** — discount (default 60%)
- **Due date** — offer submission deadline

### Step 3 — Generate Documents

Navigate to the relevant tab:

| Tab | Generates |
|---|---|
| **Executive Summary** | One-page management summary (PL/EN) |
| **Technical RFP/RFI** | Response to technical questionnaire (PL/EN) |
| **Special Bid** | Special bid request for IBM |
| **Projects** | Save and load projects |
| **System Info** | Detailed system specifications |

Click the **"Generate … DOCX"** button → download the `.docx` file.

---

## 🗂️ Project Structure

```
BobFromSales/
├── app.py                          # Main Streamlit application (entry point)
├── requirements.txt                # Python dependencies
├── start.sh                        # Launch script (macOS/Linux)
├── start.bat                       # Launch script (Windows cmd)
├── start.ps1                       # Launch script (Windows PowerShell)
│
├── app/
│   ├── parsers/
│   │   └── econfig_parser.py       # CSV + XLSX parser
│   ├── generators/
│   │   ├── exec_summary.py         # Executive Summary DOCX generator
│   │   ├── rfp_generator.py        # RFP/RFI DOCX generator
│   │   └── special_bid_generator.py# Special Bid DOCX generator
│   ├── knowledge/
│   │   └── product_db.py           # IBM Storage product database
│   ├── assets/
│   │   ├── logos/                  # IBM logos
│   │   └── images/                 # FlashSystem product images
│   └── templates/                  # DOCX templates
│
├── projects/                       # Saved projects (auto-generated)
└── INPUT-FILES/                    # Sample input files (for testing)
```

---

## 🔧 Troubleshooting

### `python: command not found` / `python3: command not found`
Python is not installed or not added to PATH. Install Python and add it to PATH.

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
Make sure that:
- The CSV comes from **IBM e-config Cloud** (not manually edited)
- The XLSX comes from **IBM Storage Modeller** and contains the required sheets

---

## 🧪 Smoke Test

To verify the application works correctly without the UI:

```bash
python3 test_pipeline.py
```

Requires test files in the root directory:
- `TEST-FS5600_120TiB.csv`
- `TEST-FS5600_120TiB-summary.xlsx`
- `TEST-FS5600_120TiB-performance.xlsx`

---

## 📦 Features

| Feature | Status |
|---|---|
| IBM e-config CSV parser (BOM, prices, feature codes, support) | ✅ |
| Storage Modeller capacity XLSX parser | ✅ |
| Storage Modeller performance XLSX parser | ✅ |
| **Executive Summary DOCX** generator (EN/PL) | ✅ |
| **Technical RFP/RFI DOCX** generator (EN/PL) | ✅ |
| **Special Bid DOCX** generator | ✅ |
| Discount slider (default 60%) with Special Bid warning above 65% | ✅ |
| Save and load projects | ✅ |
| Streamlit web UI (local) | ✅ |
