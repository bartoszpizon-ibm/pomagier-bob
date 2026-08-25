"""
IBM Storage Scale System (ESS 3500 / ESS 6000) parser.

CSV structure: a single e-config file containing multiple subsystem sections,
each preceded by a header line like "IBM ESS 3500 1", "ESS Protocol Node 1", etc.
Prices are accumulated from the OVERALL ORDER section at the end.

Hybrid NVMe+HDD configs: "ESS Capacity Model" sections contain both a Data Server
(5141-FN2, NVMe) and a 4U102 Storage shelf (5147-102, HDD). Both are parsed and
merged into a single configuration.

XLSX structure (ESS Storage Modeller): three sheets —
  Summary     — Raw/Usable/Effective capacity (TB + TiB) + Throughput (GB/s)
                May have two pools: NVMe Pool (cols 1-6) and HDD Pool (cols 8+)
  Parts List  — drive MTM, feature codes, quantities
  Environmental — power (kW), cooling (BTU/h)

Returns a unified dict compatible with Scale generators.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_scale_project(
    csv_source,
    capacity_xlsx_source,
    performance_xlsx_source=None,   # unused for Scale — capacity file contains perf too
) -> dict[str, Any]:
    """
    Parse ESS e-config CSV + ESS Storage Modeller XLSX.
    Returns a unified dict used by Scale generators.
    """
    hw  = _parse_ess_csv(csv_source)
    cap = _parse_ess_xlsx(capacity_xlsx_source)

    # Merge: CSV is authoritative for prices, model code, node roles
    merged = {**cap, **hw}

    # Keep XLSX capacity/perf values (they come from the dedicated modeller)
    for key in (
        "raw_tb", "raw_tib", "usable_tb", "usable_tib",
        "effective_tb", "effective_tib",
        "throughput_read_gbs", "throughput_write_gbs",
        "throughput_read_gibs", "throughput_write_gibs",
        "drives_count", "drive_type",
        "power_kw", "cooling_btu",
        "sm_version", "sm_date",
    ):
        if cap.get(key):
            merged[key] = cap[key]

    # If raw_tb is missing but raw_tib is present, derive TB (1 TiB = 1.099511627776 TB)
    if not merged.get("raw_tb") and merged.get("raw_tib"):
        merged["raw_tb"] = round(merged["raw_tib"] * 1.099511627776, 2)

    # Derive perf fields expected by generators
    merged["perf_throughput_mib"]  = (cap.get("throughput_read_gbs",  0.0) * 1000 / 1.048576)
    merged["perf_throughput_write_mib"] = (cap.get("throughput_write_gbs", 0.0) * 1000 / 1.048576)
    merged["perf_iops_total"]      = 0   # ESS Modeller reports throughput, not IOPS
    merged["perf_latency_ms"]      = 0.0

    return merged


# ---------------------------------------------------------------------------
# CSV parser — multi-system ESS e-config
# ---------------------------------------------------------------------------

def _parse_ess_csv(source) -> dict[str, Any]:
    """Parse ESS e-config CSV. Handles multi-system sections in one file."""
    if hasattr(source, "read"):
        text = source.read()
        if isinstance(text, bytes):
            text = text.decode("utf-8-sig")
        lines = text.splitlines()
    else:
        lines = Path(source).read_text(encoding="utf-8-sig").splitlines()

    reader = csv.reader(lines)
    rows   = list(reader)

    result: dict[str, Any] = {
        # Identification
        "currency":           "EUR",
        "price_file_date":    "",
        "config_id":          "",
        "model_code":         "",         # primary data node MTM  e.g. "5141-FN2"
        # Prices — from OVERALL ORDER block
        "list_price_hw":      0.0,
        "list_price_sw":      0.0,
        "list_price_support": 0.0,
        "list_price_total":   0.0,
        "shipping":           0.0,
        # Node inventory
        "num_data_nodes":     0,
        "num_protocol_nodes": 0,
        "num_mgmt_nodes":     0,
        "num_switches":       0,
        # Drive info (from data node section)
        "drives_count":       0,
        "drives_per_node":    0,
        "drive_type":         "",
        # Data node memory (cache)
        "cache_gb":           0,
        "cache_label":        "",         # e.g. "16 × 64 GB DDR4 = 1024 GB"
        # Network adapters on data node
        "ib_adapters":        0,          # count of IB HCA adapters
        "ib_adapter_desc":    "",         # e.g. "CX-7 VPI 200GbE/NDR200 Crypto Enabled"
        # Network
        "network_type":       "",
        "network_ports":      0,
        # Software
        "filesystem_type":    "IBM Storage Scale (GPFS)",
        "protocol_support":   [],
        "scale_edition":      "",         # e.g. "Data Management Edition"
        # Support
        "support_codes":      [],
        "support_info":       None,
        "encryption":         False,
        # Utility node details
        "utility_nodes": [],              # list of dicts
        # Expert Labs services (6911-401)
        "expert_labs_qty":    0,          # total onsite project units
        "expert_labs_price":  0.0,        # total Expert Labs price
        "expert_labs_desc":   "",         # e.g. "IBM Expert Labs - 1 Onsite Project Unit for IBM Storage"
    }

    # ── Phase 1: collect meta from first section ──────────────────────────────
    for row in rows:
        raw = [c.strip() for c in row]
        first = raw[0] if raw else ""

        m = re.search(r"Currency\s*:\s*(\w+)", first)
        if m:
            result["currency"] = m.group(1)
            break

    # ── Phase 2: split into subsystem sections ────────────────────────────────
    # Each section starts with a line like: "", "", "", "IBM ESS 3500 1"
    # We detect the title by col index 3 (row[3]) containing a system/node name
    _system_name_re = re.compile(
        r"(IBM ESS\s*\d+\s*\d*"
        r"|ESS Protocol Node"
        r"|ESS Management Server"
        r"|ESS Capacity Model\s*\d+.*Data Server"
        r"|ESS Capacity Model\s*\d+.*4U102"
        r"|Switch\s*\d+)",
        re.IGNORECASE,
    )

    sections: list[dict] = []   # [{name, rows}]
    current_name = None
    current_rows: list[list[str]] = []

    for row in rows:
        raw = [c.strip().strip('"') for c in row]
        # Section header: row[3] matches a known system name (and row[0] is empty/filename)
        col3 = raw[3] if len(raw) > 3 else ""
        if _system_name_re.search(col3):
            if current_name:
                sections.append({"name": current_name, "rows": current_rows})
            current_name  = col3
            current_rows  = []
            continue
        if current_name:
            current_rows.append(raw)

    if current_name:
        sections.append({"name": current_name, "rows": current_rows})

    # ── Phase 3a: parse Expert Labs section (6911-401-) ──────────────────────
    # Layout: product rows appear in the same block between the section header
    # (col[3]="6911-401-") and the GRAND TOTALS separator.
    # We scan all rows linearly and pick up SVOS/6911-401 price lines
    # regardless of section boundaries used by the main section splitter.
    for row in rows:
        raw   = [c.strip().strip('"') for c in row]
        first = raw[0] if raw else ""
        if len(raw) < 3:
            continue
        product = raw[0]
        desc    = raw[1] if len(raw) > 1 else ""
        qty_s   = raw[2] if len(raw) > 2 else ""
        price_s = raw[3] if len(raw) > 3 else ""
        qty     = _parse_int(qty_s)
        price   = _parse_price(price_s)
        # SVOS = onsite Expert Labs project unit line item
        if product == "SVOS" and qty:
            result["expert_labs_qty"]  += qty
            result["expert_labs_price"] = price
            if not result["expert_labs_desc"]:
                result["expert_labs_desc"] = desc.strip()
        # Fallback: total price from "6911-401 Price" summary line
        if "6911-401 Price" in desc and price and not result["expert_labs_price"]:
            result["expert_labs_price"] = price

    # ── Phase 3b: parse SYSTEM SUMMARY block — get System Quantity per subsystem
    # Applied AFTER Phase 4 (sections) via _summary_qty_overrides dict so that
    # the section-counter increments don't overwrite the authoritative SUMMARY qty.
    _summary_qty_overrides: dict[str, int] = {}   # "protocol_nodes" → qty
    in_summary = False
    _summary_current_name = None
    for row in rows:
        raw = [c.strip().strip('"') for c in row]
        first = raw[0] if raw else ""
        if "SYSTEM SUMMARY" in first.upper():
            in_summary = True
            continue
        if "OVERALL ORDER" in first.upper():
            break
        if not in_summary:
            continue
        _is_node_name = (
            first
            and (len(raw) == 1 or (len(raw) >= 2 and raw[1] == ""))
            and re.search(
                r"(ESS Protocol Node|ESS Management Server|ESS Capacity Model|Switch\s*\d+|IBM ESS)",
                first, re.IGNORECASE,
            )
        )
        if _is_node_name:
            _summary_current_name = first
        if len(raw) >= 4 and raw[1] == "System Quantity":
            qty = _parse_int(raw[3])
            if qty and _summary_current_name:
                if re.search(r"Protocol Node", _summary_current_name, re.IGNORECASE):
                    _summary_qty_overrides["protocol_nodes"] = qty

    # ── Phase 3c: parse OVERALL ORDER block (always at the end, outside sections)
    in_overall = False
    for row in rows:
        raw = [c.strip().strip('"') for c in row]
        first = raw[0] if raw else ""
        if "OVERALL ORDER" in first.upper():
            in_overall = True
            continue
        if in_overall and len(raw) >= 4:
            desc  = raw[1]
            price = _parse_price(raw[3])
            if "Hardware Price" in desc and price:
                result["list_price_hw"]    = price
            elif "Software OTC" in desc and price:
                result["list_price_sw"]    = price
            elif "System Total" in desc and price:
                result["list_price_total"] = price
            elif "Shipping" in desc and price:
                result["shipping"]         = price

    # ── Phase 4: parse each subsystem section ────────────────────────────────
    for sec in sections:
        name = sec["name"]
        srows = sec["rows"]

        # Classify
        is_data_node     = bool(re.search(r"IBM ESS\s*\d+", name, re.IGNORECASE))
        is_capacity_data = bool(re.search(r"ESS Capacity Model.*Data Server", name, re.IGNORECASE))
        is_hdd_shelf     = bool(re.search(r"ESS Capacity Model.*4U102", name, re.IGNORECASE))
        is_protocol_node = "Protocol" in name
        is_mgmt_node     = "Management" in name
        is_switch        = "Switch" in name

        # Hybrid NVMe+HDD: "Capacity Model Data Server" acts as data node
        if is_capacity_data:
            is_data_node = True

        if is_data_node:
            result["num_data_nodes"] += 1
        elif is_protocol_node:
            result["num_protocol_nodes"] += 1
        elif is_mgmt_node:
            result["num_mgmt_nodes"] += 1
        elif is_switch:
            result["num_switches"] += 1

        section_hw = False
        for raw in srows:
            first = raw[0] if raw else ""

            # Section detector
            if "HARDWARE" in first.upper():
                section_hw = True; continue
            if "SOFTWARE" in first.upper():
                section_hw = False; continue

            if not section_hw or len(raw) < 4:
                continue

            product = raw[0]
            desc    = raw[1]
            qty     = _parse_int(raw[2])

            if not product or product in ("Product",):
                continue

            # ── HDD shelf (4U102) ──────────────────────────────────────────
            if is_hdd_shelf:
                # HDD drives — AJRD or any feature with SAS/HDD desc
                if re.match(r"^[A-Z]{4}$", product):
                    _dm = re.search(r"([\d.]+\s*TB\b)", desc, re.IGNORECASE)
                    if _dm and re.search(r"HDD|SAS|SATA|NL-SAS", desc, re.IGNORECASE):
                        if "hdd_drive_type" not in result:
                            result["hdd_drive_type"]       = desc.strip()
                            result["hdd_drives_per_shelf"] = qty
                        result["hdd_drives_count"] = result.get("hdd_drives_count", 0) + qty

                # Software edition from HDD shelf (5667-DMT / 5765-DMT)
                if "Data Management" in desc:
                    result["scale_edition"] = "Data Management Edition"

                # Support product code
                if re.match(r"^5249-", product):
                    price = _parse_price(raw[3]) if len(raw) > 3 else 0.0
                    if price:
                        result["list_price_support"] = (
                            result.get("list_price_support", 0.0) + price
                        )

            # ── Data node ──────────────────────────────────────────────────
            elif is_data_node:
                # Primary model code: e.g. 5141-FN2
                if re.match(r"^\d{4}-\w+$", product) and not result["model_code"]:
                    result["model_code"] = product
                    result["num_data_nodes"] = max(result["num_data_nodes"], qty)

                # NVMe drives — AJRO, AJRS, etc. or generic NVMe desc
                if re.match(r"^[A-Z]{4}$", product):
                    _dm = re.search(r"([\d.]+\s*TB\b)", desc, re.IGNORECASE)
                    if _dm and ("NVMe" in desc or "SSD" in desc or "PCIe" in desc):
                        if not result["drive_type"]:
                            result["drive_type"]      = desc.strip()
                            result["drives_per_node"] = qty
                        result["drives_count"] += qty

                    # InfiniBand / IB HCA adapters
                    if re.search(r"200GbE.*NDR|NDR.*200|CX-7|InfiniBand", desc, re.IGNORECASE):
                        result["network_type"]   = "InfiniBand NDR 200 Gb/s"
                        result["network_ports"] += qty * 2
                        result["ib_adapters"]   += qty
                        if not result["ib_adapter_desc"]:
                            # Strip feature code prefix from desc if present
                            _ad = desc.strip()
                            result["ib_adapter_desc"] = _ad

                    # Memory DIMMs → cache_gb for data node
                    _mem_m = re.search(r"(\d+)\s*GB\s+DDR", desc, re.IGNORECASE)
                    if _mem_m:
                        _dimm_gb = int(_mem_m.group(1))
                        result["cache_gb"]    += _dimm_gb * qty
                        result["cache_label"]  = f"{qty} × {_dimm_gb} GB DDR4 = {_dimm_gb * qty} GB"

                    # Encryption
                    if "Crypto" in desc:
                        result["encryption"] = True

                # Support codes
                if product.startswith("ALK"):
                    result["support_codes"].append(product)

                # Software edition
                if "Data Management" in desc:
                    result["scale_edition"] = "Data Management Edition"
                elif "Performance" in desc and "Scale" in desc:
                    result["scale_edition"] = result["scale_edition"] or "Performance Edition"

            # ── Utility nodes (Protocol + Management) ─────────────────────
            elif is_protocol_node or is_mgmt_node:
                node_type = "Protocol Node" if is_protocol_node else "Management Server"

                # Collect utility node info once per section
                if re.match(r"^\d{4}-\w+$", product) and qty:
                    # Check if already added this node type
                    existing = next(
                        (u for u in result["utility_nodes"] if u["type"] == node_type),
                        None,
                    )
                    if not existing:
                        result["utility_nodes"].append({
                            "type":    node_type,
                            "mtm":     product,
                            "qty":     qty,
                            "desc":    desc,
                            "network": "",
                            "memory":  "",
                            "cpu":     "",
                        })

                # Enrich the last utility node
                if result["utility_nodes"] and re.match(r"^[A-Z0-9]{4}$", product):
                    u = result["utility_nodes"][-1]
                    if re.search(r"200GbE.*NDR|NDR.*200|InfiniBand", desc, re.IGNORECASE):
                        u["network"] = "InfiniBand NDR 200 Gb/s"
                    m_mem = re.search(r"(\d+)\s*GB\s+DDR", desc, re.IGNORECASE)
                    if m_mem and not u["memory"]:
                        total_mem = int(m_mem.group(1)) * qty
                        u["memory"] = f"{total_mem} GB DDR4"
                    if re.search(r"Processor|CPU|EPYC|Xeon", desc, re.IGNORECASE) and not u["cpu"]:
                        u["cpu"] = desc.strip()

                # Support
                if product.startswith("ALK"):
                    result["support_codes"].append(product)

                # Support product code (5249-A05 = Expert Care Advanced 5Y)
                if re.match(r"^5249-", product):
                    price = _parse_price(raw[3]) if len(raw) > 3 else 0.0
                    if price:
                        result["list_price_support"] = (
                            result.get("list_price_support", 0.0) + price
                        )

    # Deduplicate support codes
    result["support_codes"] = list(dict.fromkeys(result["support_codes"]))

    # Total nodes
    result["num_nodes"] = result["num_data_nodes"]

    # Merge HDD shelf info into primary drive fields
    if result.get("hdd_drives_count", 0) > 0:
        # Calculate raw HDD capacity (TB) from drive count × drive size
        _hdd_raw_tb = 0.0
        _hdd_m = re.search(r"([\d.]+)\s*TB", result.get("hdd_drive_type", ""))
        if _hdd_m:
            _hdd_raw_tb = float(_hdd_m.group(1)) * result["hdd_drives_count"]
        result["hdd_raw_tb"]  = _hdd_raw_tb
        result["hdd_raw_tib"] = round(_hdd_raw_tb / 1.099511627776, 2) if _hdd_raw_tb else 0.0

        if result["drives_count"] == 0:
            # Pure HDD config — promote HDD info to primary drive fields
            result["drive_type"]      = result.get("hdd_drive_type", "")
            result["drives_per_node"] = result.get("hdd_drives_per_shelf", 0)
            result["drives_count"]    = result["hdd_drives_count"]
        else:
            # Hybrid NVMe + HDD: accumulate total drive count
            result["drives_count"] += result["hdd_drives_count"]
        result["has_hdd_shelf"] = True
    else:
        result["has_hdd_shelf"] = False
        result["hdd_raw_tb"]    = 0.0
        result["hdd_raw_tib"]   = 0.0

    # Apply SYSTEM SUMMARY qty overrides (authoritative, overrides section-counter)
    if _summary_qty_overrides.get("protocol_nodes"):
        result["num_protocol_nodes"] = _summary_qty_overrides["protocol_nodes"]

    # Resolve support info
    from app.knowledge.product_db import get_support_info, SUPPORT_CODES
    for code in result["support_codes"]:
        info = get_support_info(code)
        if info:
            result["support_info"] = info
            break
    if not result["support_info"]:
        # ALK5 = Expert Care Advanced 5 Year — default for ESS
        result["support_info"] = SUPPORT_CODES.get("ALK5")

    return result


# ---------------------------------------------------------------------------
# XLSX parser — ESS Storage Modeller (Summary + Parts List + Environmental)
# ---------------------------------------------------------------------------

def _parse_ess_xlsx(source) -> dict[str, Any]:
    """Parse ESS Storage Modeller XLSX."""
    result: dict[str, Any] = {
        "raw_tb":   0.0, "raw_tib":   0.0,
        "usable_tb": 0.0, "usable_tib": 0.0,
        "effective_tb": 0.0, "effective_tib": 0.0,
        "throughput_read_gbs":   0.0,
        "throughput_write_gbs":  0.0,
        "throughput_read_gibs":  0.0,
        "throughput_write_gibs": 0.0,
        "drives_count": 0,
        "drive_type":   "",
        "power_kw":     0.0,
        "cooling_btu":  0.0,
        "raid_type":    "Erasure Code (8+2p)",
        "rebuild_areas": 2,
        "sm_version":   "",
        "sm_date":      "",
    }

    if hasattr(source, "seek"):
        source.seek(0)
    xf = pd.ExcelFile(source)

    # ── Summary sheet ─────────────────────────────────────────────────────────
    # Two possible layouts:
    # A) Single pool (NVMe or HDD):
    #      col[0]=label, col[1]=System value, col[2]=System value (PB/PiB)
    # B) Dual pool (NVMe Pool + HDD Pool):
    #      col[0]=label, col[1]=NVMe System, col[2]=NVMe System PB,
    #      col[3]="NVMe Pool", ..., col[8]=HDD System, col[9]=HDD System PB
    #      col[10]="HDD Pool"
    # When NVMe Pool values are all zero (pure HDD config), fall back to HDD Pool cols.
    if "Summary" in xf.sheet_names:
        df = xf.parse("Summary", header=None)
        _state = None

        _raw_tb_set = _usable_tb_set = _eff_tb_set = False
        _raw_tib_set = _usable_tib_set = _eff_tib_set = False

        # First pass: detect if this is a dual-pool sheet and if NVMe pool is empty
        _col_offset = 1   # default: single-pool, value in col[1]
        _col_offset2 = 2  # second value (TiB/GiB) in col[2]
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            # Detect "HDD Pool" label in column headers row
            if len(vals) > 10 and vals[10] == "HDD Pool":
                # Dual-pool sheet: check if NVMe pool (col 1) has data
                # by scanning for any non-zero TB value in col[1]
                break
        else:
            pass

        # Scan for non-zero values in col[1] to decide which column set to use
        _nvme_has_data = False
        _hdd_col_start = None
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            # Detect column layout by looking for "HDD Pool" / "NVMe Pool" markers
            for ci, v in enumerate(vals):
                if v in ("HDD Pool",):
                    _hdd_col_start = ci
                if v in ("NVMe Pool",):
                    pass
            # Check if col[1] contains any non-zero TB/GiB values
            v1_probe = vals[1] if len(vals) > 1 else ""
            if v1_probe and re.search(r"[1-9]", v1_probe) and ("TB" in v1_probe or "GB/s" in v1_probe):
                _nvme_has_data = True

        # If NVMe pool is empty but HDD pool exists, shift column offsets
        if not _nvme_has_data and _hdd_col_start is not None:
            _col_offset  = _hdd_col_start + 1  # e.g. col[9] for HDD System value
            _col_offset2 = _hdd_col_start + 2

        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            label = vals[0]
            v1    = vals[_col_offset]  if len(vals) > _col_offset  else ""
            v2    = vals[_col_offset2] if len(vals) > _col_offset2 else ""

            # SM version / date
            m = re.search(r"Storage Modeller version:\s*([\d.]+)", label)
            if m:
                result["sm_version"] = m.group(1)
            m = re.search(r"(\d{1,2} \w+ \d{4})", label)
            if m:
                result["sm_date"] = m.group(1)

            # State machine for capacity rows
            if label == "Raw Capacity":
                _state = "raw"; continue
            if label in ("Usable Capacity",):
                _state = "usable"; continue
            if label == "Effective Capacity":
                _state = "eff"; continue
            if label == "Throughput":
                _state = "perf"; continue

            # Parse values based on state
            # Note: "TiB" contains "TB" — test TiB first, then TB (not TiB)
            if _state == "raw":
                if not _raw_tib_set and v1 and "TiB" in v1:
                    result["raw_tib"] = _parse_cap(v1)
                    _raw_tib_set = True
                    _state = None
                elif not _raw_tb_set and v1 and "TB" in v1 and "TiB" not in v1:
                    result["raw_tb"]  = _parse_cap(v1)
                    _raw_tb_set = True

            elif _state == "usable":
                if label == "Data Pool":
                    if not _usable_tb_set and v1 and "TB" in v1 and "TiB" not in v1:
                        result["usable_tb"]  = _parse_cap(v1)
                        _usable_tb_set = True
                    elif not _usable_tib_set and v1 and "TiB" in v1:
                        result["usable_tib"] = _parse_cap(v1)
                        _usable_tib_set = True
                elif not _usable_tib_set and v1 and "TiB" in v1 and _usable_tb_set:
                    result["usable_tib"] = _parse_cap(v1)
                    _usable_tib_set = True

            elif _state == "eff":
                if label == "Data Pool":
                    if not _eff_tb_set and v1 and "TB" in v1 and "TiB" not in v1:
                        result["effective_tb"]  = _parse_cap(v1)
                        _eff_tb_set = True
                    elif not _eff_tib_set and v1 and "TiB" in v1:
                        result["effective_tib"] = _parse_cap(v1)
                        _eff_tib_set = True
                elif not _eff_tib_set and v1 and "TiB" in v1 and _eff_tb_set:
                    result["effective_tib"] = _parse_cap(v1)
                    _eff_tib_set = True

            elif _state == "perf":
                if label == "Read" and v1:
                    if "GB/s" in v1:
                        result["throughput_read_gbs"] = _parse_cap(v1)
                    if "GiB/s" in v2:
                        result["throughput_read_gibs"] = _parse_cap(v2)
                elif label == "Write" and v1:
                    if "GB/s" in v1:
                        result["throughput_write_gbs"] = _parse_cap(v1)
                    if "GiB/s" in v2:
                        result["throughput_write_gibs"] = _parse_cap(v2)

    # ── Parts List sheet ─────────────────────────────────────────────────────
    # Columns: Quantity | MTM | Feature | (blank) | Description
    if "Parts List" in xf.sheet_names:
        df = xf.parse("Parts List", header=None)
        _header_found = False
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            # Skip until header row: "Quantity", "MTM", "Feature", ..., "Description"
            if not _header_found:
                if vals[0] == "Quantity":
                    _header_found = True
                continue

            qty_s = vals[0] if vals else ""
            mtm   = vals[1] if len(vals) > 1 else ""
            feat  = vals[2] if len(vals) > 2 else ""
            desc  = vals[4] if len(vals) > 4 else ""

            qty = _parse_int(qty_s)

            # Drive count and type — feature like AJRO + NVMe desc
            if feat and qty and re.search(r"NVMe|SSD|PCIe", desc, re.IGNORECASE):
                _dm = re.search(r"([\d.]+\s*TB)", desc)
                if _dm:
                    result["drive_type"]  = desc.strip().split("(")[0].strip()
                    result["drives_count"] = max(result["drives_count"], qty)

    # ── Environmental sheet ──────────────────────────────────────────────────
    # Columns: Quantity | MTM/Feature Code | Description | Power (KW) | Cooling (BTU/hr) | ...
    if "Environmental" in xf.sheet_names:
        df = xf.parse("Environmental", header=None)
        for _, row in df.iterrows():
            vals = [str(v).strip() if pd.notna(v) else "" for v in row]
            if len(vals) < 5:
                continue
            desc_e = vals[2] if len(vals) > 2 else ""
            # Look for "Totals:" row
            if "Total" in desc_e:
                try:
                    result["power_kw"]    = float(vals[3]) if vals[3] and vals[3] != "nan" else 0.0
                    result["cooling_btu"] = float(vals[4]) if vals[4] and vals[4] != "nan" else 0.0
                except (ValueError, IndexError):
                    pass

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_price(s: str) -> float:
    s = re.sub(r"[^\d.]", "", str(s).replace(",", ""))
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_int(s: str) -> int:
    m = re.search(r"\d+", str(s).replace(",", ""))
    return int(m.group()) if m else 0


def _parse_cap(s: str) -> float:
    """Parse capacity string like '184.32 TB', '167.64 TiB', '104.40 GB/s'."""
    m = re.search(r"([\d.]+)", str(s).replace(",", ""))
    return float(m.group(1)) if m else 0.0
