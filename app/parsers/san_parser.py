"""
SAN Switch parser — reads IBM e-config CSV exports for b-type (Brocade OEM) switches.

A single CSV file may contain:
 - Only SAN switches (one or more)
 - A FlashSystem + SAN switch combination (multi-system CSV)

The parser splits the CSV into per-system sections and extracts SAN switch
entries. Returns a list of switch dicts; FlashSystem sections are ignored
(handled by econfig_parser.py).
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from app.knowledge.product_db import (
    SAN_SWITCH_DB,
    SAN_PORT_UPGRADES,
    SAN_BASE_BUNDLES,
    SANNAV_PRODUCTS,
    get_san_switch_info,
    is_san_switch_mtm,
    SUPPORT_CODES,
)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_san_csv(source) -> list[dict[str, Any]]:
    """
    Parse an e-config CSV export and return a list of SAN switch config dicts.

    Each dict represents ONE physical switch unit and contains:
        model_code        str   — e.g. "8969-R64"
        switch_name       str   — e.g. "IBM Storage Networking SAN64B-7"
        switch_short      str   — e.g. "SAN64B-7"
        exhaust           str   — "front-port" | "rear-port" | ""
        max_ports         int   — total port capacity of the chassis
        port_speed_gbps   int   — max port speed
        active_ports      int   — licensed/activated ports (bundle + upgrades)
        form_factor       str   — "1U" | "7U" | "14U"
        qty               int   — number of identical switches (from copy sections)
        features          list  — [{code, description, qty, list_price}]
        list_price_hw     float
        list_price_sw     float
        list_price_support float
        list_price_total  float
        shipping          float
        currency          str
        price_file_date   str
        config_id         str
        support_info      dict | None
        sannav_licenses   list  — [{product, description, years}]
        optics_qty        int   — number of SFP/QSFP optics
    """
    lines = _read_lines(source)
    sections = _split_sections(lines)
    switches: list[dict[str, Any]] = []

    for sec_lines in sections:
        sw = _parse_section(sec_lines)
        if sw:
            switches.append(sw)
        elif switches and _is_copy_section(sec_lines):
            # "copy N" section — same hardware as previous SAN switch; increment qty
            switches[-1]["qty"] += 1

    return switches


def _is_copy_section(lines: list[str]) -> bool:
    """Return True if this section is a copy of the previous one (": copy N" header)."""
    for line in lines[:4]:
        if re.search(r':\s*copy\s*\d+', line, re.IGNORECASE):
            return True
    return False


def has_san_switches(source) -> bool:
    """Return True if the CSV contains at least one SAN switch section."""
    lines = _read_lines(source)
    for line in lines:
        # Quick scan for 8969-xxx MTM in the header area of any section
        m = re.search(r'"(8969-[A-Z0-9]+)"', line)
        if m:
            return True
    return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_lines(source) -> list[str]:
    if hasattr(source, "read"):
        text = source.read()
        if isinstance(text, bytes):
            text = text.decode("utf-8-sig")
        source.seek(0)  # rewind so caller can re-read
        return text.splitlines()
    path = Path(source)
    return path.read_text(encoding="utf-8-sig").splitlines()


def _split_sections(lines: list[str]) -> list[list[str]]:
    """
    Split CSV into per-system sections.
    Each section starts with an 'Output File Name:' header line.
    The first occurrence may or may not have a preceding header — handle both.
    """
    sections: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if re.search(r"Output File Name:", line, re.IGNORECASE):
            if current:
                sections.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append(current)

    # If no "Output File Name" markers found, treat whole file as one section
    if not sections:
        sections = [lines]

    return sections


def _parse_section(lines: list[str]) -> dict[str, Any] | None:
    """
    Parse a single system section. Returns a dict if it's a SAN switch,
    or None if it's a FlashSystem/other product.
    """
    reader = csv.reader(lines)
    rows = list(reader)

    # --- Detect model code from header rows (row 1 typically: ["", "", "", "8969-R64-"]) ---
    model_code = ""
    for row in rows[:8]:
        raw = [c.strip() for c in row]
        if not raw:
            continue
        # MTM appears in any cell of the first few rows
        for cell in raw:
            m = re.match(r"^(8969-[A-Z0-9]+)", cell)
            if m:
                model_code = m.group(1).rstrip("-")
                break
        if model_code:
            break

    if not model_code or not is_san_switch_mtm(model_code):
        return None

    sw_info = get_san_switch_info(model_code)

    result: dict[str, Any] = {
        "model_code": model_code,
        "switch_name": sw_info.get("name", f"IBM SAN Switch {model_code}"),
        "switch_short": sw_info.get("short", model_code),
        "brocade_model": sw_info.get("brocade_model", ""),
        "exhaust": sw_info.get("exhaust", ""),
        "max_ports": sw_info.get("max_ports", 0),
        "port_speed_gbps": sw_info.get("port_speed_gbps", 32),
        "form_factor": sw_info.get("form_factor", "1U"),
        "active_ports": sw_info.get("base_ports", 0),
        "qty": 1,
        "features": [],
        "list_price_hw": 0.0,
        "list_price_sw": 0.0,
        "list_price_support": 0.0,
        "list_price_total": 0.0,
        "shipping": 0.0,
        "currency": "EUR",
        "price_file_date": "",
        "config_id": "",
        "support_info": None,
        "support_codes": [],
        "sannav_licenses": [],
        "optics_qty": 0,
        "lw_optics_qty": 0,   # long-wave SFP (2628, 2629, 2630 — LWL ≥10 km)
        "sw_optics_qty": 0,   # short-wave SFP (5810, 5811, 5812 — OM3 cable + SR SFP)
    }

    section = None

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
            elif "Shipping" in desc or "S&H" in desc.upper():
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

            # Support product for SAN: 8999-xxx, 9474-xxx, 8883-xxx
            if re.match(r"^(8999|9474|8883)-", product) and section == "hardware":
                result["list_price_support"] = price
                # Detect support level from description
                _detect_support_from_desc(result, desc)
                continue

            # Feature codes (4-char) or numeric feature codes (4-digit)
            if re.match(r"^[A-Z0-9]{4}$", product) or re.match(r"^\d{4}$", product):
                feat = {"code": product, "description": desc, "qty": qty, "list_price": price}
                result["features"].append(feat)

                # Support ALK/ALC feature codes
                if product.startswith("ALK") or product.startswith("ALC"):
                    result["support_codes"].append(product)
                    _detect_support_from_code(result, product)

                # Base bundle → sets initial active_ports
                if product in SAN_BASE_BUNDLES:
                    result["active_ports"] = SAN_BASE_BUNDLES[product]

                # Port upgrade → adds ports
                if product in SAN_PORT_UPGRADES:
                    result["active_ports"] += SAN_PORT_UPGRADES[product] * qty

                # Optics — distinguish LW (long-wave, 10 km+) from SW (short-wave/OM3)
                # LW: 2628 = SFP+,LWL,32G,10KM (8-pack); 2629/2630 = similar LW variants
                # SW: 5810 = OM3 LC/LC 10m cable; 5811/5812 = other OM3 cables
                if re.match(r"^(2628|2629|2630)", product):
                    # LW SFPs are sold in 8-packs (qty=1 pack = 8 SFPs)
                    # detect pack size from description "8-PK" or similar
                    _pk = re.search(r"(\d+)-?PK", desc, re.IGNORECASE)
                    _pack_size = int(_pk.group(1)) if _pk else 1
                    result["lw_optics_qty"] += qty * _pack_size
                    result["optics_qty"] += qty * _pack_size
                elif re.match(r"^(5810|5811|5812)", product):
                    result["sw_optics_qty"] += qty
                    result["optics_qty"] += qty

            # SANnav software product
            if re.match(r"^\d{4}-\w+$", product) and product in SANNAV_PRODUCTS:
                _years = _extract_years(desc)
                result["sannav_licenses"].append({
                    "product": product,
                    "description": SANNAV_PRODUCTS[product],
                    "full_description": desc,
                    "years": _years,
                    "list_price": price,
                })

    # Cap active_ports at max_ports
    if result["max_ports"]:
        result["active_ports"] = min(result["active_ports"], result["max_ports"])

    # Resolve support info from ALK/ALC codes
    if not result["support_info"]:
        from app.knowledge.product_db import get_support_info
        for code in result["support_codes"]:
            info = get_support_info(code)
            if info:
                result["support_info"] = info
                break

    return result


def _detect_support_from_desc(result: dict, desc: str) -> None:
    """Try to populate support_info from a free-text support product description."""
    _5y = "5 year" in desc.lower() or "5-year" in desc.lower()
    _3y = "3 year" in desc.lower() or "3-year" in desc.lower()
    _1y = "1 year" in desc.lower() or "1-year" in desc.lower()
    _24h = "24hr" in desc.lower() or "24h " in desc.lower() or "committed fix" in desc.lower()
    _adv = "advanced" in desc.lower() or "expert care" in desc.lower()
    _prm = "premium" in desc.lower()
    if _prm and _5y:
        result["support_info"] = SUPPORT_CODES.get("ALKG")
    elif _prm and _3y:
        result["support_info"] = SUPPORT_CODES.get("ALKF")
    elif (_adv or _24h) and _5y:
        result["support_info"] = SUPPORT_CODES.get("ALCN")
    elif (_adv or _24h) and _3y:
        result["support_info"] = SUPPORT_CODES.get("ALKH")
    elif _adv and _1y:
        result["support_info"] = SUPPORT_CODES.get("ALKC")


def _detect_support_from_code(result: dict, code: str) -> None:
    info = SUPPORT_CODES.get(code)
    if info and not result["support_info"]:
        result["support_info"] = info


def _extract_years(desc: str) -> int:
    m = re.search(r"(\d+)\s*[- ]?[Yy]ear", desc)
    return int(m.group(1)) if m else 0


def _parse_price(s: str) -> float:
    s = s.strip().replace(",", "")
    if not s or s in ("N/C", "N/O", "N/A", "W/D"):
        return 0.0
    s = re.sub(r"[^\d.]", "", s)
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_int(s: str) -> int:
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        return 0
