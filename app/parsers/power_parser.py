"""
Power e-config CSV parser for IBM Power11 servers (ECMPWR format).
Returns a project dict compatible with the Power generators.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Memory module capacities by feature code
# ---------------------------------------------------------------------------
_MEM_GB: dict[str, int] = {
    "EM4H": 512,   # 512 GB DDIMM (Power L1124)
    "EM5S": 512,   # 512 GB DDIMM (Power E1150)
    "EM5T": 1024,  # 1024 GB DDIMM (Power E1180)
}

# NVMe drives by feature code
_NVME_FEATURE: dict[str, str] = {
    "EC7W": "800 GB Enterprise NVMe U.2",
    "EC7Q": "800 GB Mainstream NVMe U.2",
    "ES5A": "800 GB Enterprise NVMe U.2",
}

# Processor feature codes → (cores_per_chip, ghz_min, ghz_max, description)
_PROC_FEATURE: dict[str, tuple[int, float, float, str]] = {
    "EP4C": (16, 3.4, 4.2, "Power11 EP4C 16-core 3.4–4.2 GHz"),
    "EPEX": (16, 3.5, 4.2, "Power11 EPEX 16-core 3.5–4.2 GHz"),
    "EDQ9": (48, 3.9, 4.4, "Power11 EDQ9 48-core 3.9–4.4 GHz"),
}

# Activated-cores feature codes
_ACT_FEATURE: set[str] = {
    "ERFF",  # L1124 — all 32 cores activated
    "ELEW",  # E1150 — Linux activations (54)
    "EPUT",  # E1150 — AIX activations (10)
    "ELCK",  # E1180 — Linux activations (48)
}

# FC adapter feature codes → ports per card
_FC_FEATURE: dict[str, int] = {
    "EN1A": 2,  # PCIe3 32Gb 2-port FC
    "EN1B": 2,  # PCIe3 LP 32Gb 2-port FC
}

# RoCE adapter feature codes
_ROCE_FEATURE: set[str] = {"EC72", "EC71"}

# Expert Care service codes
_SUPPORT_CODES_POWER: dict[str, dict] = {
    "EXF5": {
        "name": "Expert Care Advanced 5Y 24h Committed Fix",
        "level": "Advanced",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "24h on-site committed fix",
        "description": "24×7 support with 24-hour on-site committed hardware fix-time SLA.",
    },
    "EXPE": {
        "name": "Expert Care Premium 5Y 24h Committed Fix",
        "level": "Premium",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "24h on-site committed fix",
        "description": "24×7 premium support with 24-hour on-site committed hardware fix-time SLA.",
    },
}

# ServicePac product codes that carry Expert Care level
_SERVICEPAC_EXPERT: dict[str, dict] = {
    "9821-AF5": {
        "name": "Expert Care Advanced 5Y (Power L1124)",
        "level": "Advanced",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "24h on-site committed fix",
        "description": "Expert Care Advanced 5-year 24h Committed Fix for Power L1124.",
    },
    "9369-PF5": {
        "name": "Expert Care Premium 5Y (Power E1150)",
        "level": "Premium",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "24h on-site committed fix",
        "description": "Expert Care Premium 5-year 24h Committed Fix for Power E1150.",
    },
    "9367-PF5": {
        "name": "Expert Care Premium 5Y (Power E1180)",
        "level": "Premium",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "24h on-site committed fix",
        "description": "Expert Care Premium 5-year 24h Committed Fix for Power E1180.",
    },
}

# Model names by MTM
_MODEL_NAMES: dict[str, str] = {
    "9856-42H": "IBM Power L1124",
    "9043-MRU": "IBM Power E1150",
    "9080-HEU": "IBM Power E1180",
}


def _parse_price(s: str) -> float:
    if not s:
        return 0.0
    cleaned = re.sub(r"[^\d.,]", "", str(s)).replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_int(s: str) -> int:
    if not s:
        return 0
    try:
        return int(re.sub(r"[^\d]", "", str(s)) or "0")
    except ValueError:
        return 0


def parse_power_project(csv_source) -> dict[str, Any]:
    """
    Parse an IBM Power e-config CSV export (ECMPWR format).
    Returns a project dict for use with Power generators.
    """
    if hasattr(csv_source, "read"):
        text = csv_source.read()
        if isinstance(text, bytes):
            text = text.decode("utf-8-sig")
        lines = text.splitlines()
    else:
        path = Path(csv_source)
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    reader = csv.reader(lines)
    rows = list(reader)

    result: dict[str, Any] = {
        # identity
        "product_type":   "power",
        "_product_type":  "power",
        "model_code":     "",
        "model_name":     "",
        "currency":       "PLN",
        "date":           "",
        "config_id":      "",
        "price_file_date": "",
        # processor
        "processors":           0,   # physical processor sockets
        "processor_desc":       "",
        "processor_ghz_min":    0.0,
        "processor_ghz_max":    0.0,
        "physical_cores":       0,
        "total_cores_activated": 0,
        # memory
        "memory_gb":        0,
        "memory_tb":        0.0,
        "memory_type":      "DDR5",
        "memory_freq_mhz":  4000,
        "memory_mirroring": False,
        # storage
        "nvme_count":   0,
        "nvme_desc":    "",
        # connectivity
        "fc_ports":       0,
        "roce_adapters":  0,
        "roce_speed_gbps": 25,
        # power supply
        "power_supply_count": 0,
        # OS
        "os_primary":   "Linux",
        "os_secondary": "",
        "os_aix":       False,
        "os_linux":     True,
        # SAP / software
        "sap_hana":  False,
        "powervm":   False,
        "powerha":   False,
        "powersc":   False,
        "powervc":   False,
        "hmc_virtual": False,
        # expert labs
        "expert_labs":       False,
        "expert_labs_price": 0.0,
        "expert_labs_qty":   0,
        # support
        "support_info": None,
        # pricing
        "list_price_hw":       0.0,
        "list_price_sw":       0.0,
        "list_price_services": 0.0,
        "list_price_support":  0.0,
        "shipping":            0.0,
        # raw feature list
        "features": [],
    }

    section = None  # "hardware" | "software" | "totals"
    _sw_codes: list[str] = []   # software product codes seen
    _support_feature_code: str = ""

    for row in rows:
        if not row:
            continue
        raw = [c.strip() for c in row]
        first = raw[0] if raw else ""

        # ── meta lines ─────────────────────────────────────────────────────
        m = re.search(r"Currency\s*:\s*(\w+)", first)
        if m:
            result["currency"] = m.group(1)

        m = re.search(r"Date\s*:\s*(\d{2}/\d{2}/\d{4})", first)
        if m and not result["date"]:
            result["date"] = m.group(1)

        m = re.search(r"Hardware Price File.*?(\d{2}/\d{2}/\d{4})", first)
        if m:
            result["price_file_date"] = m.group(1)

        m = re.search(r"Configuration ID[:\s]+(\S+)", first)
        if m:
            result["config_id"] = m.group(1)

        m = re.search(r"Output File Name[:\s]+(\S+)", first)
        if m and not result["config_id"]:
            result["config_id"] = m.group(1)

        # ── model name from header (e.g. "Server 1:IBM Power L1124") ──────
        m = re.search(r"Server\s+\d+:\s*(IBM Power [A-Z]\d+)", first, re.IGNORECASE)
        if m and not result["model_name"]:
            result["model_name"] = m.group(1).strip()

        # OS detection
        if "Primary OS - Linux" in first or "Primary OS : Linux" in first:
            result["os_primary"] = "Linux"
            result["os_linux"] = True
        if "AIX Partition" in first or "AIX" in first and "Secondary" in first:
            result["os_secondary"] = "AIX"
            result["os_aix"] = True

        # ── section markers ────────────────────────────────────────────────
        _fu = first.upper()
        if "HARDWARE" in _fu and not section:
            section = "hardware"
            continue
        if "SOFTWARE" in _fu and section == "hardware":
            section = "software"
            continue
        if "GRAND TOTALS" in _fu:
            section = "totals"
            continue
        if "SERVICES" in _fu and section == "hardware":
            section = "services"
            continue

        # ── grand totals ────────────────────────────────────────────────────
        if section == "totals":
            desc = raw[1] if len(raw) > 1 else ""
            price_str = raw[3] if len(raw) > 3 else (raw[2] if len(raw) > 2 else "")
            price = _parse_price(price_str)
            if "Hardware Price" in desc or "HW Price" in desc:
                result["list_price_hw"] = price
            elif "Software OTC" in desc or "SW Price" in desc:
                result["list_price_sw"] = price
            elif "Services Price" in desc:
                result["list_price_services"] = price
            elif "Shipping" in desc or "S&H" in desc:
                result["shipping"] = price
            continue

        # ── hardware / software rows ────────────────────────────────────────
        if section in ("hardware", "software", "services") and len(raw) >= 3:
            product = raw[0]
            desc    = raw[1] if len(raw) > 1 else ""
            qty_str = raw[2] if len(raw) > 2 else ""
            price_str = raw[3] if len(raw) > 3 else ""

            if not product or product in ("Product", "Feature"):
                continue

            qty   = _parse_int(qty_str)
            price = _parse_price(price_str)

            # ── Base model MTM (e.g. 9856-42H, 9043-MRU, 9080-HEU) ────────
            if re.match(r"^\d{4}-\w+$", product) and not result["model_code"]:
                if re.match(r"^(9856|9043|9080)-", product):
                    result["model_code"] = product
                    if product in _MODEL_NAMES and not result["model_name"]:
                        result["model_name"] = _MODEL_NAMES[product]

            # ── ServicePac support products (9821-xxx, 9369-xxx, 9367-xxx) ─
            if re.match(r"^(9821|9369|9367)-", product) and section == "hardware":
                _sp = _SERVICEPAC_EXPERT.get(product)
                if _sp and not result["support_info"]:
                    result["support_info"] = _sp
                continue

            # ── Expert Labs (6911-301) ─────────────────────────────────────
            if product == "6911-301":
                result["expert_labs"] = True
                result["expert_labs_price"] = price
                result["expert_labs_qty"]   = qty or 1
                continue

            # ── 4-char feature codes ────────────────────────────────────────
            if re.match(r"^[A-Z0-9]{4}$", product):
                feat = {"code": product, "description": desc, "qty": qty, "list_price": price}
                result["features"].append(feat)

                # Processors (physical sockets)
                if product in _PROC_FEATURE:
                    cores_per, ghz_min, ghz_max, pdesc = _PROC_FEATURE[product]
                    result["processors"] += qty
                    result["physical_cores"] += qty * cores_per
                    if not result["processor_desc"]:
                        result["processor_desc"] = pdesc
                    result["processor_ghz_min"] = ghz_min
                    result["processor_ghz_max"] = ghz_max

                # Activated cores
                if product in _ACT_FEATURE:
                    result["total_cores_activated"] += qty

                # Memory DIMMs
                for mem_code, mem_gb in _MEM_GB.items():
                    if product == mem_code:
                        result["memory_gb"] += qty * mem_gb

                # Active Memory Mirroring
                if product == "EM71":
                    result["memory_mirroring"] = True

                # NVMe drives
                if product in _NVME_FEATURE:
                    result["nvme_count"] += qty
                    if not result["nvme_desc"]:
                        result["nvme_desc"] = _NVME_FEATURE[product]

                # FC ports
                if product in _FC_FEATURE:
                    result["fc_ports"] += qty * _FC_FEATURE[product]

                # RoCE adapters
                if product in _ROCE_FEATURE:
                    result["roce_adapters"] += qty

                # Power supply
                if product in ("EB3S", "EB39"):
                    result["power_supply_count"] += qty

                # Expert Care feature codes
                if product in _SUPPORT_CODES_POWER:
                    _support_feature_code = product
                    if not result["support_info"]:
                        result["support_info"] = _SUPPORT_CODES_POWER[product]

                # SAP HANA tracking feature
                if product == "EHKV":
                    result["sap_hana"] = True

                # PowerVM
                if product in ("EPVT", "EPVW", "ELCV"):
                    result["powervm"] = True

            # ── Software product codes (5-char + dashes) ───────────────────
            if re.match(r"^\d{4}-\w+$", product) and section == "software":
                _sw_codes.append(product)
                if product == "5765-H39":
                    result["powerha"] = True
                if product in ("5765-VE4", "5765-VL4", "5765-VM1"):
                    result["powervm"] = True
                if product == "5765-SC2":
                    result["powersc"] = True
                if product == "5765-VC2":
                    result["powervc"] = True
                if product == "5765-HMU":
                    result["hmc_virtual"] = True

    # ── Post-parse derivations ─────────────────────────────────────────────
    result["memory_tb"] = round(result["memory_gb"] / 1000, 2)

    # If physical_cores known but activated not set — assume all activated
    if result["physical_cores"] and not result["total_cores_activated"]:
        result["total_cores_activated"] = result["physical_cores"]

    # OS flags
    if result["os_aix"]:
        result["os_linux"] = True   # mixed AIX+Linux configs always have Linux too

    # SAP HANA auto-detect from software if EHKV not present
    if not result["sap_hana"]:
        for sw in _sw_codes:
            if "5639-SAP" in sw or "SLES for SAP" in sw:
                result["sap_hana"] = True
                break

    # Support fallback: scan for EXF5/EXPE in features
    if not result["support_info"]:
        from app.knowledge.product_db import SUPPORT_CODES
        for feat in result["features"]:
            code = feat["code"]
            if code in _SUPPORT_CODES_POWER:
                result["support_info"] = _SUPPORT_CODES_POWER[code]
                break
        if not result["support_info"]:
            # Generic Power Expert Care fallback
            result["support_info"] = _SUPPORT_CODES_POWER.get("EXF5", {
                "name": "IBM Power Expert Care",
                "level": "Advanced",
                "years": 5,
                "coverage": "24×7",
                "fix_time": True,
                "fix_time_hours": "24h committed fix",
                "description": "24×7 support with committed hardware fix-time SLA.",
            })

    return result
