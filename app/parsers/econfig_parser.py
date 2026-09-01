"""
Parser Core — reads e-config CSV + Storage Modeller capacity XLSX + performance XLSX.
Returns a unified dict used by all generators.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def parse_project(
    csv_source,
    capacity_xlsx_source,
    performance_xlsx_source=None,
) -> dict[str, Any]:
    """
    Parse all input files and return a unified project data dict.

    Args:
        csv_source: path string, Path, or file-like object (e-config CSV).
        capacity_xlsx_source: path/file-like (Storage Modeller capacity XLSX).
        performance_xlsx_source: path/file-like (Storage Modeller performance XLSX), optional.

    Returns:
        dict with keys: hardware, pricing, capacity, performance, support, environment.
    """
    hw = _parse_econfig_csv(csv_source)
    cap = _parse_capacity_xlsx(capacity_xlsx_source)
    perf = _parse_performance_xlsx(performance_xlsx_source) if performance_xlsx_source else {}

    merged = {**hw, **cap, **perf}
    # _extra_cache_gb from CSV is not reliable — Storage Modeller XLSX already
    # reports final System Memory (base + any upgrades). Remove the CSV-derived
    # extra to avoid double-counting.
    merged.pop("_extra_cache_gb", None)

    # Drive data: CSV (e-config) is the authoritative source for drive type/count
    # because the XLSX (Storage Modeller) may be from a different model configuration.
    # Always use CSV values when available; fall back to XLSX only if CSV has nothing.
    for _field, _default in (("drive_type", ""), ("drive_feature", ""), ("drives_count", 0)):
        csv_val = hw.get(_field, _default)
        if csv_val and csv_val != _default:   # CSV has a real value — use it
            merged[_field] = csv_val
        # else: keep whatever XLSX (cap) contributed via the **cap spread above

    # Hybrid flags: OR of CSV and XLSX detections — either source can flag it
    merged["is_hybrid"] = hw.get("is_hybrid", False) or cap.get("is_hybrid", False)

    # HDD tier — prefer XLSX Details sheet values (more precise per-tier numbers)
    # over CSV-derived approximations; CSV fills in drive_type/feature/count if missing
    for _hf in ("hdd_raw_tb", "hdd_raw_tib", "hdd_usable_tb", "hdd_usable_tib",
                "hdd_drives_count", "nvme_raw_tb", "nvme_raw_tib",
                "nvme_usable_tb", "nvme_usable_tib", "nvme_drives_count"):
        xlsx_val = cap.get(_hf, 0)
        if xlsx_val:
            merged[_hf] = xlsx_val
    # HDD drive type/feature: prefer CSV (parsed from actual line items)
    for _hf in ("hdd_drive_type", "hdd_drive_feature"):
        csv_val = hw.get(_hf, "")
        if csv_val:
            merged[_hf] = csv_val
        elif not merged.get(_hf):
            merged[_hf] = cap.get(_hf, "")
    # HDD enclosure info from CSV only
    for _hf in ("hdd_enclosure", "hdd_enclosure_qty", "hdd_drives_count", "has_sas_attach"):
        csv_val = hw.get(_hf)
        if csv_val:
            merged[_hf] = csv_val

    # NVMe FCM drive count from XLSX when CSV only sees the NVMe partition of drives
    if merged.get("is_hybrid") and cap.get("nvme_drives_count"):
        merged["drives_count"] = cap["nvme_drives_count"]

    # Rack units — for hybrid configs the XLSX may only report the controller RU.
    # Recompute from known per-component RU values when we have enclosure info from CSV.
    # Known rack heights: FS5600 (5127-*) = 1 RU, FS5000 HD LFF expansion (4662-92G) = 5 RU
    _ENC_RU = {
        "4662-92G": 5,
        "4662-92F": 5,
    }
    _MODEL_RU = {
        "5127": 1,   # FS5600 control enclosure
        "5078": 2,   # FS7600 control enclosure
        "5015": 2,   # FS9600 control enclosure
    }
    if merged.get("is_hybrid"):
        _model_prefix = (merged.get("model_code") or "")[:4]
        _ctrl_ru      = _MODEL_RU.get(_model_prefix, merged.get("rack_units", 1))
        _hdd_enc_mtm  = merged.get("hdd_enclosure", "")
        _hdd_enc_qty  = merged.get("hdd_enclosure_qty", 1)
        _enc_ru       = _ENC_RU.get(_hdd_enc_mtm, 0)
        if _enc_ru:
            merged["rack_units"] = _ctrl_ru + _enc_ru * _hdd_enc_qty

    return merged


def parse_project_csv_only(csv_source) -> dict[str, Any]:
    """
    Parse only the e-config CSV (no Storage Modeller XLSX required).
    Estimates raw/usable capacity from drive feature codes.
    Missing performance data is filled with zeros.

    Returns the same dict shape as parse_project() so all generators work unchanged.
    Used when XLSX files are not available — sufficient for Special Bid generation.
    """
    hw = _parse_econfig_csv(csv_source)

    # --- For models with integrated drives (e.g. FSC200 5202-C25), fill from model_info ---
    if not hw.get("drives_count") or not hw.get("drive_type"):
        from app.knowledge.product_db import get_model_info as _gmi
        _mi = _gmi(hw.get("model_code", ""))
        if _mi.get("drives_count") and not hw.get("drives_count"):
            hw["drives_count"] = _mi["drives_count"]
        if _mi.get("drive_type") and not hw.get("drive_type"):
            hw["drive_type"] = _mi["drive_type"]

    # --- Estimate raw capacity from drive type string ---
    # drive_type examples: "6.6 TB FlashCore Module 5", "26.4 TB FlashCore Module 5"
    raw_tib = 0.0
    drive_tb_each = 0.0
    if hw.get("drive_type") and hw.get("drives_count"):
        m = re.match(r"([\d.]+)\s*TB", hw["drive_type"], re.IGNORECASE)
        if m:
            drive_tb_each = float(m.group(1))
            raw_tb = drive_tb_each * hw["drives_count"]
            raw_tib = raw_tb / 1.099511627776  # TB → TiB

    # --- Estimate usable: DRAID6 overhead is roughly 2 drives + 1 rebuild area ---
    # Conservative estimate: usable ≈ raw × 0.75 (accounts for DRAID6 + overhead)
    usable_tib = round(raw_tib * 0.75, 1) if raw_tib else 0.0
    raw_tib    = round(raw_tib,         1)

    # --- Base cache per model family (from e-config model code) ---
    # FS5600/5200:  5127-xxx → 256 GB
    # FS7600/7300:  5075-xxx → 768 GB
    # FS9600/9500:  5078-xxx → 512 GB
    # FS5045/5015:  4680-xxx → 64 GB base (upgradeable via ALGA +32 GB, ALGB +64 GB)
    _model = hw.get("model_code", "")
    if re.match(r"5078-|5077-", _model):    # FS9600 / FS9500
        cache_gb = 512
    elif re.match(r"5075-|5074-", _model):  # FS7600 / FS7300
        cache_gb = 768
    elif re.match(r"5127-|5126-", _model):  # FS5600 / FS5200
        cache_gb = 256
    elif re.match(r"5202-|5147-|5076-", _model):  # FSC200
        cache_gb = 256
    elif re.match(r"4680-", _model):        # FS5045 / FS5015
        cache_gb = 64
    else:
        cache_gb = 256
    # Add any cache upgrade features parsed from CSV
    cache_gb += hw.pop("_extra_cache_gb", 0)

    # --- I/O group count per model family ---
    # FS5045/FS5015 (4680-xxx): 1 I/O group (single controller pair)
    # All other FlashSystem models: 2 I/O groups
    if re.match(r"4680-", _model):
        _io_groups = 1
    else:
        _io_groups = 2

    merged = {
        # capacity (estimated)
        "raw_tb":    round(raw_tib * 1.099511627776, 1),
        "raw_tib":   raw_tib,
        "usable_tb": round(usable_tib * 1.099511627776, 1),
        "usable_tib": usable_tib,
        "effective_tb":  0.0,
        "effective_tib": 0.0,
        "recommended_max_tib": 0.0,
        "compression_pct": 0.0,
        "dedup_pct":        0.0,
        # config defaults
        "cache_gb":      cache_gb,
        "raid_type":     "DRAID6",
        "io_groups":     _io_groups,
        "enclosures":    1,
        "pools":         1,
        "arrays":        1,
        "rack_units":    2,
        "power_kw_typical": 0.0,
        "power_kva_typical": 0.0,
        "power_kw_max":  0.0,
        "power_kva_max": 0.0,
        "cooling_btu":   0.0,
        "sm_version":    "",
        "sm_date":       "",
        # performance — unknown without modeller
        "perf_iops_total":          0,
        "perf_iops_max_sub1ms":     0,
        "perf_latency_ms":          0.0,
        "perf_latency_at_max_sub1ms": 0.0,
        "perf_bandwidth_sub1ms":    0.0,
        "perf_throughput_mib":      0.0,
        "perf_throughput_write_mib": 0.0,
        # flag so UI can show a notice
        "_csv_only": True,
    }
    merged.update(hw)  # CSV values override defaults (prices, model, features, etc.)
    # restore capacity estimates (CSV has no capacity data)
    merged["raw_tib"]    = raw_tib
    merged["usable_tib"] = usable_tib
    merged["cache_gb"]   = cache_gb
    return merged


# ---------------------------------------------------------------------------
# e-config CSV parser
# ---------------------------------------------------------------------------

def _parse_econfig_csv(source) -> dict[str, Any]:
    """Parse IBM e-config CSV export."""
    if hasattr(source, "read"):
        text = source.read()
        if isinstance(text, bytes):
            text = text.decode("utf-8-sig")
        lines = text.splitlines()
    else:
        path = Path(source)
        lines = path.read_text(encoding="utf-8-sig").splitlines()

    reader = csv.reader(lines)
    rows = list(reader)

    result: dict[str, Any] = {
        "currency": "EUR",
        "price_file_date": "",
        "country_code": "",
        "config_id": "",
        "model_code": "",
        "features": [],           # list of {code, description, qty, price}
        "list_price_hw": 0.0,
        "list_price_sw": 0.0,
        "list_price_support": 0.0,
        "list_price_total": 0.0,
        "shipping": 0.0,
        "support_codes": [],
        "support_info": None,
        "fc_ports": 0,
        "encryption": False,
        "cable_qty": 0,
        "drive_type": "",
        "drive_feature": "",
        "drives_count": 0,
        # Hybrid NVMe + HDD tier (e.g. FS5600H with 4662-92G expansion)
        "is_hybrid": False,
        "hdd_drive_type": "",      # e.g. "20TB 7.2K 3.5 Inch NL HDD"
        "hdd_drive_feature": "",   # e.g. "AL4E"
        "hdd_drives_count": 0,
        "hdd_enclosure": "",       # expansion MTM e.g. "4662-92G"
        "hdd_enclosure_qty": 0,
        "has_sas_attach": False,   # ALBQ = SAS expansion attach card
    }

    section = None  # "hardware" | "software"

    for row in rows:
        if not row:
            continue

        raw = [c.strip() for c in row]
        first = raw[0] if raw else ""

        # --- meta ---
        m = re.search(r"Currency\s*:\s*(\w+)", first)
        if m:
            result["currency"] = m.group(1)

        m = re.search(r"Hardware Price File.*?(\d{2}/\d{2}/\d{4})", first)
        if m:
            result["price_file_date"] = m.group(1)

        # Country code — "LV EUR Euros Commercial" → "LV"
        # or "for pricing country/region code LT"
        if "Hardware Price File" in first or "Software Price File" in first:
            _mc = re.search(r":\s+([A-Z]{2})\s+[A-Z]{3}", first)
            if _mc and not result.get("country_code"):
                result["country_code"] = _mc.group(1)
        _mc2 = re.search(r"country/region code\s+([A-Z]{2})\b", first, re.IGNORECASE)
        if _mc2 and not result.get("country_code"):
            result["country_code"] = _mc2.group(1).upper()

        m = re.search(r"Configuration ID:\s*(\S+)", first)
        if m:
            result["config_id"] = m.group(1)

        # --- sections ---
        if "HARDWARE" in first.upper():
            section = "hardware"
            continue
        if "SOFTWARE" in first.upper():
            section = "software"
            continue
        if "GRAND TOTALS" in first.upper():
            section = "totals"
            continue

        # --- grand totals ---
        if section == "totals":
            desc = raw[1] if len(raw) > 1 else ""
            price_str = raw[3] if len(raw) > 3 else ""
            price = _parse_price(price_str)
            if "Hardware Price" in desc:
                result["list_price_hw"] = price
            elif "Software OTC" in desc:
                result["list_price_sw"] = price
            elif "System Total" in desc:
                result["list_price_total"] = price
            elif "Shipping" in desc:
                result["shipping"] = price
            continue

        # --- product/feature rows ---
        if section in ("hardware", "software") and len(raw) >= 4:
            product = raw[0]
            desc = raw[1]
            qty_str = raw[2]
            price_str = raw[3]

            if not product and not desc:
                continue
            if product in ("Product", ""):
                continue

            qty = _parse_int(qty_str)
            price = _parse_price(price_str)

            # Base model: first numeric product code (e.g. 5127-A20, 5078-A40)
            # Must be in HARDWARE section; skip known non-model prefixes
            if re.match(r"^\d{4}-\w+$", product) and not result["model_code"] and section == "hardware":
                # Exclude known support/software product prefixes AND SAN switches (8969-xxx)
                if not re.match(r"^(5132|5076|5079|5080|5081|5203|5608|5775|8969|8999|9474|8883)-", product):
                    result["model_code"] = product

            # Support product — various prefixes depending on model family:
            # 5132-xxx (FS5x00), 5076-xxx (FS7600), 5079-xxx (FS9600), 5080-xxx, 5081-xxx
            # 5203-xxx (FSC200 Expert Care), 4690-xxx (FS5045/FS5015 Expert Care)
            # 8999-xxx / 9474-xxx / 8883-xxx = SAN b-type Expert Care
            if re.match(r"^(5132|5076|5079|5080|5081|5203|4690|8999|9474|8883)-", product) and section == "hardware":
                result["list_price_support"] = price
                continue

            # Feature codes (4 chars uppercase or alphanumeric)
            if re.match(r"^[A-Z0-9]{4}$", product):
                feature = {"code": product, "description": desc, "qty": qty, "list_price": price}
                result["features"].append(feature)

                # Support feature codes — ALK* and ALC* (e.g. ALCN = Advanced 24hr)
                if product.startswith("ALK") or product.startswith("ALC"):
                    result["support_codes"].append(product)

                # FC adapter → count ports
                # ALB9 / AHBL = 32Gb 4-port pair → 4 ports × qty
                # ALBB        = 32Gb 2-port pair → 2 ports × qty
                # ALB7        = 16Gb 4-port pair → 4 ports × qty
                # ALBG        = 16Gb FC 4-port pair (FS5045/FS5015) → 4 ports × qty
                if product in ("ALB9", "AHBL", "ALB7", "ALBG"):
                    result["fc_ports"] += qty * 4
                elif product == "ADBE":   # C200: 32 Gb FC 4-port pair (2 cards × 4 ports)
                    result["fc_ports"] += qty * 8
                elif product == "ALBB":
                    result["fc_ports"] += qty * 2

                # Cache upgrade — description may be in GB or TB
                # e.g. "768 GB cache upgrade" (ALGG) or "1.5 TB cache upgrade" (ALGH)
                if product.startswith("ALG") and "cache" in desc.lower():
                    try:
                        _gb_m  = re.search(r"([\d.]+)\s*GB", desc, re.IGNORECASE)
                        _tb_m  = re.search(r"([\d.]+)\s*TB", desc, re.IGNORECASE)
                        if _tb_m:
                            gb = int(float(_tb_m.group(1)) * 1024)
                        elif _gb_m:
                            gb = int(float(_gb_m.group(1)))
                        else:
                            gb = 0
                        if gb:
                            result.setdefault("_extra_cache_gb", 0)
                            result["_extra_cache_gb"] += gb * qty
                    except Exception:
                        pass

                # Encryption — ACEG (standard), ACEF (C200 Encryption Enablement)
                if product in ("ACEG", "ACEF"):
                    result["encryption"] = True

                # Cables
                if product in ("ACSR", "ACSS"):
                    result["cable_qty"] += qty

                # Drive type & count — NVMe FCM drives AND SAS Flash Drives (FS5045/FS5015)
                # e.g. "6.6 TB FlashCore Module 5" / "15.36TB 12 Gb SAS 2.5 Inch Flash Drive"
                # Note: [\w\s.] includes dots (for "2.5 Inch" in SAS drive descriptions)
                _dm = re.search(
                    r"([\d.]+\s*TB\s+Flash\w+\s+Module\s+\d+|[\d.]+\s*TB[\w\s.]*?Flash\s+Drive)",
                    desc, re.IGNORECASE
                )
                if _dm and not result.get("drive_type"):
                    result["drive_type"] = _dm.group(1).strip()
                    result["drive_feature"] = product
                    result["drives_count"] = qty

                # HDD drives — NL-SAS / SAS / NL HDD feature codes (e.g. AL4E, AL4G…)
                # Description pattern: "20TB 7,200 rpm 12 Gb SAS NL 3.5 Inch HDD"
                _hm = re.search(r"([\d.]+\s*TB\b.*?\bNL\s*HDD\b|[\d.]+\s*TB\b.*?\bSAS\b.*?\bHDD\b|[\d.]+\s*TB\b.*?\bNL-SAS\b)", desc, re.IGNORECASE)
                if _hm:
                    result["is_hybrid"] = True
                    result["hdd_drive_feature"] = product
                    result["hdd_drives_count"] += qty
                    if not result["hdd_drive_type"]:
                        # Compact the description to "20TB NL-SAS HDD" form
                        _cap_m = re.search(r"([\d.]+\s*TB)", desc)
                        _rpm_m = re.search(r"(\d[,\d]*\s*rpm)", desc, re.IGNORECASE)
                        _cap = _cap_m.group(1).strip() if _cap_m else ""
                        _rpm = _rpm_m.group(1).replace(",", "").strip() if _rpm_m else ""
                        result["hdd_drive_type"] = f"{_cap} {_rpm + ' ' if _rpm else ''}NL-SAS HDD".strip()

                # SAS expansion attach card
                if product == "ALBQ":
                    result["has_sas_attach"] = True

    # Mark hybrid if AHZE (Hybrid Flash Indicator) was present
    for f in result["features"]:
        if f["code"] == "AHZE":
            result["is_hybrid"] = True
            break

    # For hybrid: expansion enclosure MTM from product rows:
    #   4662-* = FS5600/FS5200 LFF HDD expansion (4663-* is its support — skip)
    #   4680-12H / 4680-12L = FS5045/FS5015 LFF expansion (4690-* is support — already skipped above)
    for row in rows:
        raw = [c.strip() for c in row]
        if not raw:
            continue
        product = raw[0] if raw else ""
        desc    = raw[1] if len(raw) > 1 else ""
        qty_str = raw[2] if len(raw) > 2 else ""
        if re.match(r"^4662-", product) or re.match(r"^4680-1", product):
            result["hdd_enclosure"]     = product
            result["hdd_enclosure_qty"] = _parse_int(qty_str) or 1
            result["is_hybrid"]         = True

    # --- resolve support info ---
    from app.knowledge.product_db import get_support_info
    for code in result["support_codes"]:
        info = get_support_info(code)
        if info:
            result["support_info"] = info
            break

    # If no support info found from individual features, scan all support product rows
    # (5132-xxx FS5x00, 5076-xxx FS7600, 5079-xxx FS9600, 5080/5081-xxx others, 4690-xxx FS5045/5015)
    if not result["support_info"]:
        from app.knowledge.product_db import SUPPORT_CODES
        for row in rows:
            raw = [c.strip() for c in row]
            if raw and re.match(r"^(5132|5076|5079|5080|5081|5203|4690)-", raw[0]):
                desc = raw[1] if len(raw) > 1 else ""
                _has_24hr  = "24hr" in desc or "24 hr" in desc or "Committed Fix" in desc
                _has_4h    = "4 hour" in desc or "4hr" in desc or "same.day" in desc.lower()
                _5y = "5 Year" in desc or "5 year" in desc
                _3y = "3 Year" in desc or "3 year" in desc
                _1y = "1 Year" in desc or "1 year" in desc
                if "Premium" in desc and _5y:
                    result["support_info"] = SUPPORT_CODES["ALKG"]
                elif "Premium" in desc and _3y:
                    result["support_info"] = SUPPORT_CODES["ALKF"]
                elif "Premium" in desc and _1y:
                    result["support_info"] = SUPPORT_CODES["ALKD"]
                elif ("Advanced" in desc or _has_24hr or _has_4h) and _5y:
                    result["support_info"] = SUPPORT_CODES["ALCN"]   # Advanced 24hr 5Y
                elif ("Advanced" in desc or _has_24hr) and _3y:
                    result["support_info"] = SUPPORT_CODES["ALKH"]
                elif ("Advanced" in desc or _has_24hr) and _1y:
                    result["support_info"] = SUPPORT_CODES["ALKC"]
                elif "Basic" in desc and _5y:
                    result["support_info"] = SUPPORT_CODES["ALK3"]
                elif "Expert Care" in desc or "Storage Expert" in desc:
                    # generic fallback — at least mark as Advanced 5Y
                    result["support_info"] = SUPPORT_CODES["ALCN"]
                if result["support_info"]:
                    break

    return result


# ---------------------------------------------------------------------------
# Capacity XLSX parser
# ---------------------------------------------------------------------------

def _parse_capacity_xlsx(source) -> dict[str, Any]:
    """Parse Storage Modeller capacity XLSX."""
    result: dict[str, Any] = {
        "raw_gb": 0.0, "raw_tb": 0.0, "raw_gib": 0.0, "raw_tib": 0.0,
        "usable_gb": 0.0, "usable_tb": 0.0, "usable_gib": 0.0, "usable_tib": 0.0,
        "effective_gb": 0.0, "effective_tb": 0.0, "effective_gib": 0.0, "effective_tib": 0.0,
        # Hybrid tiers — populated from Details sheet when present
        "is_hybrid": False,
        "nvme_raw_tb": 0.0,    "nvme_raw_tib": 0.0,
        "nvme_usable_tb": 0.0, "nvme_usable_tib": 0.0,
        "nvme_drives_count": 0,
        "hdd_raw_tb": 0.0,     "hdd_raw_tib": 0.0,
        "hdd_usable_tb": 0.0,  "hdd_usable_tib": 0.0,
        "hdd_drives_count": 0,
        "hdd_drive_type": "",
        "hdd_drive_feature": "",
        "compression_pct": 0.0,
        "dedup_pct": 0.0,
        "recommended_max_tib": 0.0,
        "drives_count": 0,
        "drive_type": "",
        "drive_feature": "",
        "enclosures": 1,
        "io_groups": 1,
        "pools": 1,
        "arrays": 1,
        "cache_gb": 256,
        "model_version": "",
        "raid_type": "DRAID6",
        "raid_drives": 0,
        "rebuild_areas": 1,
        "extent_size_mib": 0,
        "pool_type": "Regular",
        "fc_adapters_slots": [],
        "eth_onboard": True,
        "product_version": "",
        "rack_units": 1,
        "power_kw_typical": 0.0,
        "power_kva_typical": 0.0,
        "power_kw_max": 0.0,
        "power_kva_max": 0.0,
        "cooling_btu": 0.0,
        "sm_version": "",
        "sm_date": "",
    }

    if hasattr(source, "seek"):
        source.seek(0)
    xf = pd.ExcelFile(source)

    # --- Summary sheet ---
    if "Summary" in xf.sheet_names:
        df = xf.parse("Summary", header=None)
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            label = vals[0]
            v1 = vals[1] if len(vals) > 1 else ""
            v2 = vals[2] if len(vals) > 2 else ""

            if "Number of drives" in label:
                result["drives_count"] = _parse_int(v1)
            elif "Number of I/O groups" in label:
                result["io_groups"] = _parse_int(v1)
            elif "Number of pools" in label:
                result["pools"] = _parse_int(v1)
            elif "Number of arrays" in label:
                result["arrays"] = _parse_int(v1)
            elif "Number of enclosures" in label:
                result["enclosures"] = _parse_int(v1)
            elif "Raw capacity" in label and "GB" in v1:
                result["raw_gb"] = _parse_capacity_val(v1)
                result["raw_tb"] = _parse_capacity_val(v2)
            elif v1 and "GiB" in v1 and result["raw_gib"] == 0.0 and not label:
                result["raw_gib"] = _parse_capacity_val(v1)
                result["raw_tib"] = _parse_capacity_val(v2)
            elif "Usable capacity" in label and "GB" in v1:
                result["usable_gb"] = _parse_capacity_val(v1)
                result["usable_tb"] = _parse_capacity_val(v2)
            elif v1 and "GiB" in v1 and result["usable_gib"] == 0.0 and not label and result["usable_gb"] > 0:
                result["usable_gib"] = _parse_capacity_val(v1)
                result["usable_tib"] = _parse_capacity_val(v2)
            elif "Effective capacity" in label and "GB" in v1:
                result["effective_gb"] = _parse_capacity_val(v1)
                result["effective_tb"] = _parse_capacity_val(v2)
            elif v1 and "GiB" in v1 and result["effective_gib"] == 0.0 and not label and result["effective_gb"] > 0:
                result["effective_gib"] = _parse_capacity_val(v1)
                result["effective_tib"] = _parse_capacity_val(v2)

            # SM version/date
            m = re.search(r"Storage Modeller version:\s*([\d.]+)", label)
            if m:
                result["sm_version"] = m.group(1)
            m = re.search(r"(\d{1,2} \w+ \d{4})", label)
            if m:
                result["sm_date"] = m.group(1)

    # --- Details sheet ---
    # Layout (header): Description | Arrays | Drives | Raw(TB) | Raw(TiB) | Usable(TB) | Usable(TiB) | Eff(TB) | Eff(TiB)
    # Key rows: "TOTAL" | "NVMe" | "Nearline HDD" | "Pool overheads" | "Pool #N"
    if "Details" in xf.sheet_names:
        df = xf.parse("Details", header=None)
        _dh: dict[str, int] = {}   # header key → column index
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            if not vals:
                continue

            # Detect header row by presence of "Raw capacity (TB)"
            joined_row = " ".join(vals)
            if vals[0] == "Description" and "Raw capacity (TB)" in joined_row:
                _dh = {v.lower(): i for i, v in enumerate(vals) if v}
                continue

            if "Recommended usage" in joined_row:
                for v in vals:
                    m = re.search(r"(\d+)\s*TiB", v)
                    if m:
                        result["recommended_max_tib"] = float(m.group(1))
                        break
            for v in vals:
                m = re.search(r"extent size (\d+) MiB", v)
                if m:
                    result["extent_size_mib"] = int(m.group(1))
            for v in vals:
                if "Regular Pool" in v:
                    result["pool_type"] = "Regular"

            # Per-tier row — use detected header positions or fixed fallback
            _ri = _dh if _dh else {
                "description": 0, "drives": 2,
                "raw capacity (tb)": 3, "raw capacity (tib)": 4,
                "usable capacity (tb)": 5, "usable capacity (tib)": 6,
            }

            def _col(key: str) -> str:
                idx = _ri.get(key, -1)
                return vals[idx] if 0 <= idx < len(vals) else ""

            desc_val = vals[_ri.get("description", 0)] if vals else ""

            if desc_val == "NVMe":
                result["is_hybrid"] = True
                result["nvme_raw_tb"]     = _parse_capacity_val(_col("raw capacity (tb)"))
                result["nvme_raw_tib"]    = _parse_capacity_val(_col("raw capacity (tib)"))
                result["nvme_usable_tb"]  = _parse_capacity_val(_col("usable capacity (tb)"))
                result["nvme_usable_tib"] = _parse_capacity_val(_col("usable capacity (tib)"))
                _nd = _parse_int(_col("drives"))
                if _nd:
                    result["nvme_drives_count"] = _nd
            elif re.search(r"Nearline HDD|NL HDD|HDD", desc_val, re.IGNORECASE) and desc_val not in ("TOTAL",):
                result["is_hybrid"] = True
                result["hdd_raw_tb"]     = _parse_capacity_val(_col("raw capacity (tb)"))
                result["hdd_raw_tib"]    = _parse_capacity_val(_col("raw capacity (tib)"))
                result["hdd_usable_tb"]  = _parse_capacity_val(_col("usable capacity (tb)"))
                result["hdd_usable_tib"] = _parse_capacity_val(_col("usable capacity (tib)"))
                _hd = _parse_int(_col("drives"))
                if _hd:
                    result["hdd_drives_count"] = _hd

    # --- Protection sheet ---
    if "Protection" in xf.sheet_names:
        df = xf.parse("Protection", header=None)
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            for v in vals:
                if "Distributed RAID" in v or "DRAID" in v:
                    result["raid_type"] = "DRAID6"
            if len(vals) >= 4:
                n = _parse_int(vals[2])
                if n > 0:
                    result["raid_drives"] = n
                rb = _parse_int(vals[3])
                if rb > 0:
                    result["rebuild_areas"] = rb

    # --- Parts List sheet ---
    if "Parts List" in xf.sheet_names:
        df = xf.parse("Parts List", header=None)
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            joined = " ".join(vals)
            # NVMe FCM drive type — "ADSL 26.4TB FlashCore Module 5" or "26.4TB FlashCore Module 5 (ADSL)"
            m = re.search(r"(\w{4})\s+([\d.]+\s*TB\s+Flash\w+\s+Module\s+\d+)", joined, re.IGNORECASE)
            if m:
                result["drive_feature"] = m.group(1)
                result["drive_type"] = m.group(2).strip()
            else:
                m = re.search(r"([\d.]+\s*TB\s+Flash\w+\s+Module\s+\d+)\s*\((\w+)\)", joined, re.IGNORECASE)
                if m:
                    result["drive_type"] = m.group(1).strip()
                    result["drive_feature"] = m.group(2)
            # cache
            m = re.search(r"(\d+)\s*GB\s*Base\s*Cache", joined)
            if m:
                result["cache_gb"] = int(m.group(1))
            # Hybrid flag from Parts List notes
            if "hybrid" in joined.lower() and "FlashSystem" in joined:
                result["is_hybrid"] = True
            # HDD drive type from Parts List (feature + description columns)
            # Row: qty | MTM | feature_code | description
            if len(vals) >= 4:
                _feat = vals[2].strip()
                _desc = vals[3].strip()
                _hm = re.search(r"([\d.]+\s*TB\b.*?\bNL\s*HDD\b|[\d.]+\s*TB\b.*?\bSAS\b.*?\bHDD\b)", _desc, re.IGNORECASE)
                if _hm and _feat and not result["hdd_drive_feature"]:
                    result["hdd_drive_feature"] = _feat
                    _cap_m2 = re.search(r"([\d.]+\s*TB)", _desc)
                    _rpm_m2 = re.search(r"(\d[\d.]*[kK]\s*rpm|\d[,\d]*\s*rpm)", _desc, re.IGNORECASE)
                    _cap2   = _cap_m2.group(1).strip() if _cap_m2 else ""
                    _rpm2   = _rpm_m2.group(1).replace(",", "").strip() if _rpm_m2 else ""
                    result["hdd_drive_type"] = result["hdd_drive_type"] or f"{_cap2} {_rpm2 + ' ' if _rpm2 else ''}NL-SAS HDD".strip()
                    result["is_hybrid"] = True

    # --- Configuration sheet ---
    if "Configuration" in xf.sheet_names:
        df = xf.parse("Configuration", header=None)
        _pool_header_cols: list[str] = []
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            if len(vals) >= 2:
                label = vals[0]
                val = vals[1]
                if "Product Version" in label:
                    result["product_version"] = val
                elif "System Memory" in label:
                    result["cache_gb"] = _parse_int(val)
            # Detect pool header row: contains "Compression" and "Deduplication" columns
            joined = " ".join(vals)
            if "Compression" in joined and "Deduplication" in joined:
                _pool_header_cols = [v.lower() for v in vals]
            elif _pool_header_cols and vals[0].startswith("Pool"):
                # Data row matching the pool header
                try:
                    ci = next(i for i, h in enumerate(_pool_header_cols) if "compression" in h)
                    di = next(i for i, h in enumerate(_pool_header_cols) if "deduplication" in h)
                    if ci < len(vals) and vals[ci]:
                        result["compression_pct"] = float(vals[ci])
                    if di < len(vals) and vals[di]:
                        result["dedup_pct"] = float(vals[di])
                except (StopIteration, ValueError):
                    pass
                _pool_header_cols = []  # only read first pool

    # --- Operating Environment sheet ---
    if "Operating Environment" in xf.sheet_names:
        df = xf.parse("Operating Environment", header=None)
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            joined = " ".join(vals)
            # parse specific rows
            for v in vals:
                m = re.search(r"([\d.]+)\s*kW$", v)
                if m and result["power_kw_typical"] == 0.0:
                    result["power_kw_typical"] = float(m.group(1))
                elif m and result["power_kw_typical"] > 0.0 and result["power_kw_max"] == 0.0:
                    result["power_kw_max"] = float(m.group(1))

                m = re.search(r"([\d.]+)\s*kVA", v)
                if m and result["power_kva_typical"] == 0.0:
                    result["power_kva_typical"] = float(m.group(1))
                elif m and result["power_kva_typical"] > 0.0 and result["power_kva_max"] == 0.0:
                    result["power_kva_max"] = float(m.group(1))

                m = re.search(r"([\d.]+)\s*KW", v)
                if m:
                    result["power_kw_max"] = float(m.group(1))

                m = re.search(r"([\d,]+\.?\d*)\s*BTU", v)
                if m:
                    result["cooling_btu"] = float(m.group(1).replace(",", ""))

                m = re.search(r"Rack Units[^\d]*([\d]+)", joined)
                if m:
                    result["rack_units"] = int(m.group(1))

    return result


# ---------------------------------------------------------------------------
# Performance XLSX parser
# ---------------------------------------------------------------------------

def _parse_performance_xlsx(source) -> dict[str, Any]:
    """Parse Storage Modeller performance XLSX."""
    result: dict[str, Any] = {
        "perf_iops_total": 0,
        "perf_iops_read": 0,
        "perf_iops_write": 0,
        "perf_read_pct": 0.0,
        "perf_transfer_size_kib": 16,
        "perf_throughput_mib": 0.0,
        "perf_latency_ms": 0.0,
        "perf_cache_hit_pct": 0.0,
        "perf_workload_name": "",
        # Key metric: max IOPS the system can sustain below 1 ms latency
        "perf_iops_max_sub1ms": 0,
        "perf_latency_at_max_sub1ms": 0.0,
        # Bandwidth (MiB/s) at max sub-1ms IOPS point
        "perf_bandwidth_sub1ms": 0.0,
    }

    try:
        if hasattr(source, "seek"):
            source.seek(0)
        xf = pd.ExcelFile(source)
    except Exception:
        return result

    # --- Workload Details ---
    if "Workload Details" in xf.sheet_names:
        df = xf.parse("Workload Details", header=None)
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            if len(vals) < 2:
                continue
            label = vals[0]
            val = vals[1]

            if "Total I/O Rate" in label and "Sequential" not in label:
                result["perf_iops_total"] = int(float(val)) if _is_number(val) else 0
            elif "Read I/O Rate" in label and "Sequential" not in label:
                result["perf_iops_read"] = int(float(val)) if _is_number(val) else 0
            elif "Write I/O Rate" in label and "Sequential" not in label:
                result["perf_iops_write"] = int(float(val)) if _is_number(val) else 0
            elif "Read I/O Percentage" in label and "Sequential" not in label:
                result["perf_read_pct"] = float(val) if _is_number(val) else 0.0
            elif "Read Transfer Size" in label and "Sequential" not in label:
                result["perf_transfer_size_kib"] = int(float(val)) if _is_number(val) else 16
            elif "Total Data Rate" in label and "Sequential" not in label:
                result["perf_throughput_mib"] = float(val) if _is_number(val) else 0.0
            elif "Total Cache Read Hits" in label:
                # "Total Cache Read Hits (%)" — primary cache hit metric
                result["perf_cache_hit_pct"] = float(val) if _is_number(val) else 0.0
            elif "Cache Random Read Hits" in label and result["perf_cache_hit_pct"] == 0.0:
                # Fallback to random-only metric if total not yet set
                result["perf_cache_hit_pct"] = float(val) if _is_number(val) else 0.0

    # --- Response Times ---
    if "Response Times" in xf.sheet_names:
        df = xf.parse("Response Times", header=None)
        target_iops = result["perf_iops_total"]
        best_diff = float("inf")
        best_latency = 0.0
        max_iops_sub1ms = 0
        latency_at_max_sub1ms = 0.0

        bandwidth_at_max_sub1ms = 0.0

        for _, row in df.iterrows():
            vals = list(row)
            # Each data row has a numeric triplet: IOPS, Data Rate (MiB/s), Latency (ms)
            nums = [v for v in vals if isinstance(v, (int, float)) and pd.notna(v)]
            if len(nums) >= 3:
                iops_val      = nums[0]
                bandwidth_val = nums[1]   # Data Rate (MiB/s)
                latency_val   = nums[2]

                # Latency at the configured workload IOPS
                diff = abs(iops_val - target_iops)
                if diff < best_diff:
                    best_diff    = diff
                    best_latency = latency_val

                # Max IOPS while staying below 1 ms latency
                if latency_val < 1.0 and iops_val > max_iops_sub1ms:
                    max_iops_sub1ms       = int(round(iops_val))
                    latency_at_max_sub1ms = round(latency_val, 3)
                    bandwidth_at_max_sub1ms = round(bandwidth_val, 1)

        if best_latency > 0:
            result["perf_latency_ms"] = round(best_latency, 3)
        if max_iops_sub1ms > 0:
            result["perf_iops_max_sub1ms"]       = max_iops_sub1ms
            result["perf_latency_at_max_sub1ms"] = latency_at_max_sub1ms
            result["perf_bandwidth_sub1ms"]      = bandwidth_at_max_sub1ms

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_price(s: str) -> float:
    s = s.strip().replace(",", "").replace("$", "").replace("€", "")
    if s in ("N/C", "N/A", "N/O", "W/D", "=========", ""):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_int(s: str) -> int:
    s = s.strip().replace(",", "")
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def _parse_capacity_val(s: str) -> float:
    """Extract numeric value from strings like '237,494.51 GB' or '216.00 TiB'."""
    s = re.sub(r"[^\d.]", "", s.replace(",", ""))
    try:
        return float(s)
    except ValueError:
        return 0.0


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False
