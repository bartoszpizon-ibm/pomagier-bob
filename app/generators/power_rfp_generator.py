"""
RFP / RFI Generator for IBM Power11 servers (L1124 / E1150 / E1180).
Produces a DOCX technical requirements table for Power server procurement.
Vendor-neutral wording throughout — no IBM product names in requirement cells.
"""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

from ..knowledge.product_db import get_model_info

IBM_BLUE  = RGBColor(0x00, 0x62, 0xFF)
IBM_DARK  = RGBColor(0x16, 0x16, 0x16)
IBM_GRAY  = RGBColor(0x52, 0x52, 0x52)
IBM_LG    = RGBColor(0xF4, 0xF4, 0xF4)
IBM_WHITE = RGBColor(0xFF, 0xFF, 0xFF)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGOS_DIR  = ASSETS_DIR / "logos"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_power_rfp(
    project: dict[str, Any],
    client_name: str = "",
    seller_name: str = "",
    lang: str = "en",
    num_systems: int = 1,
) -> bytes:
    """Generate Power11 RFP requirements DOCX and return as bytes."""
    doc = Document()
    _set_page_margins(doc)
    _set_default_font(doc)

    model_code = project.get("model_code", "")
    model_info = get_model_info(model_code)

    _add_header_block(doc, project, model_info, client_name, seller_name, lang)
    _add_intro_paragraph(doc, project, model_info, client_name, lang, num_systems=num_systems)
    _add_requirements_table(doc, project, model_info, lang)
    _add_footer_note(doc, lang)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Document sections
# ---------------------------------------------------------------------------

def _add_header_block(doc, project, model_info, client_name, seller_name, lang):
    from app.generators.rfp_generator import _add_hrule, _para_space
    from app.generators.exec_summary import _add_logo_header

    _add_logo_header(doc)

    _is_pl = (lang == "pl")
    title = ("Specyfikacja Wymagań Technicznych — Serwer IBM Power"
             if _is_pl else
             "Technical Requirements Specification — IBM Power Server")
    sub   = ("Dokument RFP / RFI · IBM Power11"
             if _is_pl else
             "RFP / RFI Document · IBM Power11")

    p = doc.add_paragraph()
    _para_space(p, before=24, after=4)
    run = p.add_run(title)
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = IBM_DARK

    sp = doc.add_paragraph()
    _para_space(sp, before=0, after=4)
    srun = sp.add_run(sub)
    srun.font.size = Pt(11)
    srun.font.color.rgb = IBM_BLUE

    _add_hrule(doc)

    meta_label = "Przygotowane dla" if _is_pl else "Prepared for"
    meta_by    = "Przygotowane przez" if _is_pl else "Prepared by"
    meta_date  = "Data" if _is_pl else "Date"

    mp = doc.add_paragraph()
    _para_space(mp, before=8, after=0)
    mp.add_run(f"{meta_label}: {client_name or '—'}  |  "
               f"{meta_by}: {seller_name or '—'}  |  "
               f"{meta_date}: {date.today().strftime('%d.%m.%Y' if _is_pl else '%B %d, %Y')}"
               ).font.size = Pt(9)


def _add_intro_paragraph(doc, project, model_info, client_name, lang, num_systems=1):
    from app.generators.rfp_generator import _para_space

    _is_pl = (lang == "pl")
    model_name = model_info.get("name", project.get("model_name", "IBM Power Server"))
    cores      = project.get("total_cores_activated", project.get("physical_cores", 0))
    mem_tb     = project.get("memory_tb", 0.0)
    client_str = f"dla {client_name} " if (_is_pl and client_name) else (
                 f"for {client_name} " if client_name else "")

    if _is_pl:
        body = (
            f"Niniejszy dokument określa minimalne wymagania techniczne {client_str}"
            f"dla serwera klasy enterprise IBM Power11. "
            f"Konfiguracja referencyjna: {model_name}, {cores} aktywowanych rdzeni, "
            f"{mem_tb:.1f} TB pamięci DDR5. "
            f"Oferty niespełniające minimalnych wymagań zostaną odrzucone."
        )
        if num_systems > 1:
            body += f" Łącznie wymaganych systemów: {num_systems}."
    else:
        body = (
            f"This document defines the minimum technical requirements {client_str}"
            f"for an enterprise-class IBM Power11 server. "
            f"Reference configuration: {model_name}, {cores} activated cores, "
            f"{mem_tb:.1f} TB DDR5 memory. "
            f"Bids not meeting the minimum requirements will be disqualified."
        )
        if num_systems > 1:
            body += f" Total systems required: {num_systems}."

    p = doc.add_paragraph(body)
    _para_space(p, before=12, after=12)
    for run in p.runs:
        run.font.size = Pt(10)
        run.font.color.rgb = IBM_DARK


def _add_requirements_table(doc, project, model_info, lang):
    from app.generators.rfp_generator import _para_space

    _is_pl = (lang == "pl")

    cores      = project.get("total_cores_activated", project.get("physical_cores", 0))
    phys_cores = project.get("physical_cores", cores)
    proc_desc  = project.get("processor_desc", "Power11")
    ghz_min    = project.get("processor_ghz_min", 0.0)
    ghz_max    = project.get("processor_ghz_max", 0.0)
    mem_tb     = project.get("memory_tb", 0.0)
    mem_gb     = project.get("memory_gb", 0)
    mem_type   = project.get("memory_type", "DDR5")
    mem_freq   = project.get("memory_freq_mhz", 4000)
    nvme_count = project.get("nvme_count", 0)
    nvme_desc  = project.get("nvme_desc", "NVMe U.2")
    fc_ports   = project.get("fc_ports", 0)
    roce_n     = project.get("roce_adapters", 0)
    roce_spd   = project.get("roce_speed_gbps", 25)
    os_p       = project.get("os_primary", "Linux")
    os_s       = project.get("os_secondary", "")
    sap        = project.get("sap_hana", False)
    pvm        = project.get("powervm", False)
    pha        = project.get("powerha", False)
    psc        = project.get("powersc", False)
    hmc        = project.get("hmc_virtual", False)
    sup_info   = project.get("support_info") or {}
    sup_name   = sup_info.get("name", "Expert Care")
    sup_years  = sup_info.get("years", 5)
    sup_fix    = "Yes" if sup_info.get("fix_time") else "No"
    labs       = project.get("expert_labs", False)

    if _is_pl:
        headers = ["#", "Wymaganie", "Opis / Minimalna wartość", "Spełnione (T/N)", "Uwagi"]
        rows = [
            ("1",  "Model serwera",
             f"Enterprise IBM Power11 — referencyjna konfiguracja: {model_info.get('name', 'IBM Power')}",
             "", ""),
            ("2",  "Architektura procesorów",
             f"Procesor IBM Power11 RISC. Min. {cores} aktywowanych rdzeni"
             + (f" z {phys_cores} fizycznych rdzeni" if phys_cores != cores else ""),
             "", ""),
            ("3",  "Taktowanie procesora",
             f"Min. {ghz_min:.1f} GHz bazowe, boost do {ghz_max:.1f} GHz" if ghz_min else "Power11",
             "", ""),
            ("4",  "Pojemność pamięci RAM",
             f"Min. {mem_tb:.0f} TB ({mem_gb:,} GB) pamięci operacyjnej",
             "", ""),
            ("5",  "Typ i prędkość pamięci",
             f"{mem_type} {mem_freq} MHz — pamięć DDIMM",
             "", ""),
            ("6",  "Wewnętrzna pamięć NVMe",
             f"Min. {nvme_count} × {nvme_desc}" if nvme_count else "Wewnętrzne napędy NVMe",
             "", ""),
            ("7",  "Łączność sieciowa (RoCE)",
             f"Min. {roce_n} × {roce_spd} GbE RoCE (dual-port)" if roce_n else f"{roce_spd} GbE RoCE",
             "", ""),
            ("8",  "Łączność Fibre Channel",
             f"Min. {fc_ports} portów FC 32 Gb/s" if fc_ports else "Porty FC 32 Gb/s",
             "", ""),
            ("9",  "Wsparcie systemu operacyjnego",
             (f"Linux ({os_p})" + (f" + {os_s}" if os_s else "")),
             "", ""),
            ("10", "Certyfikacja SAP HANA",
             "Wymagana certyfikacja SAP HANA TDI (Tailored Data Centre Integration)" if sap else "Opcjonalnie",
             "", ""),
            ("11", "Platforma wirtualizacji",
             "IBM PowerVM — wymagana obsługa LPAR, live partition mobility" if pvm else "Wirtualizacja na poziomie systemu operacyjnego",
             "", ""),
            ("12", "Oprogramowanie HA",
             "IBM PowerHA SystemMirror lub równoważne — klastrowanie active/standby" if pha else "Opcjonalne HA",
             "", ""),
            ("13", "Oprogramowanie bezpieczeństwa",
             "IBM PowerSC lub równoważne (hardening, STIG, audyt)" if psc else "Opcjonalne",
             "", ""),
            ("14", "Konsola zarządzania (HMC)",
             "IBM HMC Virtual Appliance lub fizyczna HMC" if hmc else "Narzędzie zarządzania serwerem",
             "", ""),
            ("15", "Poziom wsparcia",
             f"{sup_name}" if sup_name != "Expert Care" else "Min. 24×7 z fix-time SLA",
             "", ""),
            ("16", "Okres wsparcia",
             f"Min. {sup_years} lat" if sup_years else "Min. 3 lata",
             "", ""),
            ("17", "Usługi wdrożeniowe",
             "IBM Expert Labs lub certyfikowany partner — instalacja i konfiguracja on-site" if labs else "Usługi wdrożeniowe wycenione oddzielnie",
             "", ""),
        ]
    else:
        headers = ["#", "Requirement", "Description / Minimum Value", "Met (Y/N)", "Comments"]
        rows = [
            ("1",  "Server model",
             f"Enterprise IBM Power11 — reference configuration: {model_info.get('name', 'IBM Power')}",
             "", ""),
            ("2",  "Processor architecture",
             f"IBM Power11 RISC processor. Min. {cores} activated cores"
             + (f" from {phys_cores} total physical cores" if phys_cores != cores else ""),
             "", ""),
            ("3",  "Processor frequency",
             f"Min. {ghz_min:.1f} GHz base, boost to {ghz_max:.1f} GHz" if ghz_min else "Power11",
             "", ""),
            ("4",  "Total memory capacity",
             f"Min. {mem_tb:.0f} TB ({mem_gb:,} GB) RAM",
             "", ""),
            ("5",  "Memory type / speed",
             f"{mem_type} {mem_freq} MHz — DDIMM modules",
             "", ""),
            ("6",  "Internal NVMe storage",
             f"Min. {nvme_count} × {nvme_desc}" if nvme_count else "Internal NVMe drives",
             "", ""),
            ("7",  "Network connectivity (RoCE)",
             f"Min. {roce_n} × {roce_spd} GbE RoCE (dual-port)" if roce_n else f"{roce_spd} GbE RoCE",
             "", ""),
            ("8",  "Fibre Channel connectivity",
             f"Min. {fc_ports} × FC 32 Gb/s ports" if fc_ports else "FC 32 Gb/s ports",
             "", ""),
            ("9",  "Operating system support",
             (f"Linux ({os_p})" + (f" + {os_s}" if os_s else "")),
             "", ""),
            ("10", "SAP HANA certification",
             "SAP HANA TDI (Tailored Data Centre Integration) certification required" if sap else "Optional",
             "", ""),
            ("11", "Virtualisation platform",
             "IBM PowerVM — LPAR support, live partition mobility required" if pvm else "OS-level virtualisation",
             "", ""),
            ("12", "High Availability software",
             "IBM PowerHA SystemMirror or equivalent — active/standby clustering" if pha else "Optional HA",
             "", ""),
            ("13", "Security software",
             "IBM PowerSC or equivalent (hardening, STIG, audit)" if psc else "Optional",
             "", ""),
            ("14", "Management console (HMC)",
             "IBM HMC Virtual Appliance or physical HMC" if hmc else "Server management tool",
             "", ""),
            ("15", "Support service level",
             f"{sup_name}" if sup_name != "Expert Care" else "Min. 24×7 with fix-time SLA",
             "", ""),
            ("16", "Support duration",
             f"Min. {sup_years} years" if sup_years else "Min. 3 years",
             "", ""),
            ("17", "Expert Labs services",
             "IBM Expert Labs or certified partner — on-site installation and configuration" if labs else "Deployment services quoted separately",
             "", ""),
        ]

    # Build table
    tbl = doc.add_table(rows=1 + len(rows), cols=5)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Set column widths
    col_widths = [Cm(0.9), Cm(4.5), Cm(8.0), Cm(2.2), Cm(2.8)]
    for i, w in enumerate(col_widths):
        for cell in tbl.columns[i].cells:
            cell.width = w

    # Header row
    hdr_row = tbl.rows[0]
    for i, hdr in enumerate(headers):
        cell = hdr_row.cells[i]
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "161616")
        shd.set(qn("w:color"), "161616")
        shd.set(qn("w:val"), "clear")
        tcPr.append(shd)
        p = cell.paragraphs[0]
        run = p.add_run(hdr)
        run.font.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = IBM_WHITE

    # Data rows
    for row_i, (num, req, desc, met, note) in enumerate(rows):
        trow = tbl.rows[row_i + 1]
        _bg = "F4F4F4" if row_i % 2 == 1 else "FFFFFF"
        _data = [num, req, desc, met, note]
        for col_i, val in enumerate(_data):
            cell = trow.cells[col_i]
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn
            shd = OxmlElement("w:shd")
            shd.set(qn("w:fill"), _bg)
            shd.set(qn("w:color"), _bg)
            shd.set(qn("w:val"), "clear")
            tcPr.append(shd)
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(9)
            run.font.color.rgb = IBM_DARK


def _add_footer_note(doc, lang):
    from app.generators.rfp_generator import _para_space, _add_hrule

    _is_pl = (lang == "pl")
    _add_hrule(doc)
    note = (
        "* Dostawcy są zobowiązani wypełnić kolumny 'Spełnione' i 'Uwagi' dla każdego wymagania. "
        "Brak odpowiedzi oznacza niespełnienie wymagania. Ceny są cenami katalogowymi — "
        "wymagana indywidualna wycena."
        if _is_pl else
        "* Vendors are required to complete the 'Met' and 'Comments' columns for each requirement. "
        "No response will be interpreted as non-compliance. Prices are list prices — "
        "individual quotation required."
    )
    p = doc.add_paragraph(note)
    _para_space(p, before=6, after=0)
    for run in p.runs:
        run.font.size = Pt(8)
        run.font.color.rgb = IBM_GRAY
        run.font.italic = True


# ---------------------------------------------------------------------------
# DOCX helpers
# ---------------------------------------------------------------------------

def _set_page_margins(doc):
    from app.generators.exec_summary import _set_page_margins as _fs_margins
    _fs_margins(doc)


def _set_default_font(doc):
    from app.generators.exec_summary import _set_default_font as _fs_font
    _fs_font(doc)
