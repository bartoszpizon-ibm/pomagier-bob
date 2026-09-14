"""
Executive Summary DOCX generator for IBM Power11 servers (L1124 / E1150 / E1180).
Produces an IBM-branded Word document from a parsed project dict
returned by app.parsers.power_parser.parse_power_project().
"""
from __future__ import annotations

import io
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Inches

from ..knowledge.product_db import get_model_info, get_docs

# IBM design tokens
IBM_BLUE       = RGBColor(0x00, 0x62, 0xFF)
IBM_DARK       = RGBColor(0x16, 0x16, 0x16)
IBM_GRAY       = RGBColor(0x52, 0x52, 0x52)
IBM_LIGHT_GRAY = RGBColor(0xF4, 0xF4, 0xF4)
IBM_WHITE      = RGBColor(0xFF, 0xFF, 0xFF)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGOS_DIR  = ASSETS_DIR / "logos"
IMAGES_DIR = ASSETS_DIR / "images"

# ---------------------------------------------------------------------------
# Performance data per model (indicative, from IBM benchmarks)
# ---------------------------------------------------------------------------
_PERF_DATA: dict[str, dict[str, str]] = {
    "9856-42H": {  # L1124
        "sap_hana":     "Up to 2 TB HANA in-memory",
        "saps":         "~10,000 SAPS per core (OLTP benchmark)",
        "db_latency":   "Sub-millisecond DB response at peak load",
        "memory_bw":    ">200 GB/s memory bandwidth",
    },
    "9043-MRU": {  # E1150
        "sap_hana":     "Up to 16 TB HANA in-memory (scalable)",
        "saps":         "250,000+ SAPS @ 64 cores",
        "ai":           "AI inferencing + in-memory analytics",
        "memory_bw":    ">400 GB/s memory bandwidth",
    },
    "9080-HEU": {  # E1180
        "sap_hana":     "Up to 64 TB HANA in-memory (4-node scale-out)",
        "saps":         "48-core sustained compute",
        "memory_bw":    ">500 GB/s memory bandwidth",
        "scale_out":    "4-node scale-out for largest HANA deployments",
    },
}

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
_TRANS: dict[str, dict[str, str]] = {
    "en": {
        "cover_subtitle":  "Technical Executive Summary",
        "prepared_for":    "Prepared for",
        "prepared_by":     "Prepared by",
        "date":            "Date",
        "valid_until":     "Valid until",
        "config_id":       "Configuration ID",
        "sec_exec":        "Executive Summary",
        "sec_config":      "Solution Configuration",
        "sec_performance": "Performance Profile",
        "sec_software":    "Software & Subscriptions",
        "sec_support":     "Service & Support",
        "sec_pricing":     "Pricing Summary",
        "sec_next":        "Next Steps",
        "key_highlights":  "Key Solution Highlights",
        "platform_advantages": "Platform Advantages",
        "adv1": (
            "Power11 Matrix Math Accelerator (MMA) — on-chip AI/ML acceleration "
            "embedded in every processor core, delivering inferencing throughput "
            "without requiring additional GPUs or accelerator cards."
        ),
        "adv2": (
            "Hardware Memory Encryption — end-to-end encryption at the DDIMM level "
            "provides data-at-rest security for SAP HANA and sensitive enterprise "
            "workloads without measurable performance overhead."
        ),
        "adv3": (
            "PowerVM enterprise hypervisor — industry-leading LPAR virtualisation "
            "with live partition mobility, active memory sharing, and sub-second "
            "failover for mission-critical workloads."
        ),
        "adv4": (
            "SAP HANA Tailored Data Centre Integration (TDI) certified — "
            "IBM Power11 servers are independently validated for SAP HANA scale-up "
            "and scale-out deployments, with the largest certified memory per socket."
        ),
        "body": (
            "This proposal {client_str}recommends the {model_name} IBM Power11 server. "
            "The system is equipped with {cores} activated processor cores ({processor_desc}), "
            "{memory_tb:.1f} TB DDR5 memory, {nvme_count} NVMe drives, "
            "and {fc_ports} × 32 Gb Fibre Channel ports. "
            "All hardware is covered by {support_name} for {support_years} years."
        ),
        "multi_system_note": "This document covers a configuration of {n} × {model}. Specifications below refer to a single system.",
        "support_24x7":    "24×7 around-the-clock support with a hardware fix-time SLA",
        "support_9x5":     "9×5 business-hours support",
        "no_support":      "No support information found in configuration.",
        "sup_pkg":         "Support Package",
        "sup_level":       "Level",
        "sup_term":        "Term",
        "sup_years_unit":  "{n} years",
        "sup_coverage":    "Coverage Hours",
        "sup_fixtime":     "Hardware Fix-Time SLA",
        "sup_fixtime_yes": "Yes — 24-hour on-site committed fix",
        "sup_fixtime_no":  "No fix-time SLA",
        "sup_desc":        "Description",
        "cfg_model":       "Model",
        "cfg_mtm":         "Machine Type-Model",
        "cfg_form":        "Form Factor",
        "cfg_processor":   "Processor",
        "cfg_cores":       "Activated Cores",
        "cfg_physical":    "Physical Cores (total)",
        "cfg_memory":      "Memory Capacity",
        "cfg_mem_type":    "Memory Type / Speed",
        "cfg_mem_mirror":  "Memory Mirroring",
        "cfg_nvme":        "Internal NVMe Storage",
        "cfg_fc":          "Fibre Channel Connectivity",
        "cfg_roce":        "Network (RoCE)",
        "cfg_psu":         "Power Supply",
        "cfg_os":          "Operating System",
        "cfg_sap":         "SAP HANA Certified",
        "cfg_powervm":     "Virtualisation (PowerVM)",
        "cfg_powerha":     "High Availability (PowerHA)",
        "cfg_powersc":     "Security (PowerSC)",
        "cfg_powervc":     "Cloud Mgmt (PowerVC)",
        "cfg_hmc":         "Management Console (HMC)",
        "cfg_expert_labs": "Expert Labs Deployment",
        "cfg_support":     "Support Package",
        "perf_sap_hana":   "SAP HANA In-Memory",
        "perf_saps":       "SAPS (OLTP benchmark)",
        "perf_memory_bw":  "Memory Bandwidth",
        "perf_ai":         "AI/Inference Capability",
        "perf_scale":      "Scale-Out",
        "perf_latency":    "DB Response Latency",
        "sw_title":        "Software Components",
        "price_info":      "List prices from IBM e-config · Discount applied: {d:.1f}% · Offer valid until: {vu}",
        "price_cat":       "Category",
        "price_qty":       "Qty",
        "price_list":      "List Price ({curr})",
        "price_disc":      "Discount",
        "price_eu_col":    "End User Price ({curr})",
        "price_hw":        "Hardware ({mc})",
        "price_sup":       "Expert Care Support",
        "price_sw":        "Software / Subscriptions",
        "price_svc":       "Professional Services",
        "price_ship":      "Shipping & Handling (non-discountable)",
        "price_total":     "TOTAL LIST PRICE",
        "price_eu_row":    "END USER PRICE",
        "price_fn": (
            "* Prices are exclusive of applicable taxes. "
            "This offer is valid for 30 days from the date of preparation. "
            "Final pricing subject to IBM approval. "
            "Shipping and handling charges are non-discountable."
        ),
        "next_1_title":    "Technical Deep-Dive / Workshop",
        "next_1_body":     "Schedule a technical session with {client} to validate the proposed Power11 configuration against SAP HANA sizing, AIX/Linux workload requirements, and network architecture.",
        "next_2_title":    "Formal Quotation",
        "next_2_body":     "Upon request, IBM or an authorised IBM Business Partner will issue a formal quotation valid for 30 days referencing the configuration from this document.",
        "next_3_title":    "Order Placement",
        "next_3_body":     "Orders are placed through an IBM Authorised Distributor or directly with IBM. Standard lead time for IBM Power11 servers is 6–10 weeks ARO (After Receipt of Order).",
        "next_4_title":    "IBM Expert Labs Deployment",
        "next_4_body":     "IBM Expert Labs will manage on-site installation, AIX/Linux OS configuration, PowerVM LPAR setup, network integration, and initial performance baseline testing.",
        "docs_heading":    "Product Documentation",
        "docs_ibm_docs":   "IBM Documentation",
        "docs_sales_manual": "IBM Sales Manual",
        "contact":         "Contact: {name} · IBM Power Sales",
        "disclaimer": (
            "This document is prepared for IBM Business Partners and their customers. "
            "Prices shown are list prices from IBM e-config and do not constitute a binding offer. "
            "Performance data is indicative and based on IBM published benchmarks — no guarantees expressed or implied. "
            "IBM, Power, AIX, PowerVM, PowerHA, SAP HANA are trademarks of their respective owners."
        ),
    },
    "pl": {
        "cover_subtitle":  "Techniczne Podsumowanie Wykonawcze",
        "prepared_for":    "Przygotowane dla",
        "prepared_by":     "Przygotowane przez",
        "date":            "Data",
        "valid_until":     "Ważne do",
        "config_id":       "ID konfiguracji",
        "sec_exec":        "Podsumowanie Wykonawcze",
        "sec_config":      "Konfiguracja rozwiązania",
        "sec_performance": "Profil wydajności",
        "sec_software":    "Oprogramowanie i subskrypcje",
        "sec_support":     "Serwis i wsparcie",
        "sec_pricing":     "Zestawienie cenowe",
        "sec_next":        "Kolejne kroki",
        "key_highlights":  "Kluczowe cechy rozwiązania",
        "platform_advantages": "Zalety platformy",
        "adv1": (
            "Power11 Matrix Math Accelerator (MMA) — sprzętowe przyspieszenie AI/ML "
            "wbudowane w każdy rdzeń procesora, dostarczające przepustowość wnioskowania "
            "bez potrzeby dodatkowych kart GPU lub akceleratorów."
        ),
        "adv2": (
            "Sprzętowe szyfrowanie pamięci — szyfrowanie end-to-end na poziomie modułów DDIMM "
            "zapewnia bezpieczeństwo danych w spoczynku dla SAP HANA i wrażliwych obciążeń "
            "korporacyjnych bez mierzalnego wpływu na wydajność."
        ),
        "adv3": (
            "Hypervisor PowerVM klasy enterprise — wiodąca w branży wirtualizacja LPAR "
            "z migracji partycji na żywo, współdzieleniem pamięci i przełączeniem awaryjnym "
            "poniżej sekundy dla obciążeń krytycznych."
        ),
        "adv4": (
            "Certyfikacja SAP HANA Tailored Data Centre Integration (TDI) — "
            "serwery IBM Power11 są niezależnie certyfikowane dla wdrożeń SAP HANA scale-up "
            "i scale-out, z największą certyfikowaną ilością pamięci na gniazdo."
        ),
        "body": (
            "Niniejsza propozycja {client_str}rekomenduje serwer IBM Power11 {model_name}. "
            "System wyposażony jest w {cores} aktywowanych rdzeni procesorów ({processor_desc}), "
            "{memory_tb:.1f} TB pamięci DDR5, {nvme_count} napędów NVMe, "
            "oraz {fc_ports} portów Fibre Channel 32 Gb. "
            "Całość sprzętu objęta jest pakietem {support_name} przez {support_years} lat."
        ),
        "multi_system_note": "Niniejszy dokument obejmuje konfigurację {n} × {model}. Parametry poniżej dotyczą pojedynczego systemu.",
        "support_24x7":    "24×7 wsparcie całodobowe z fix-time SLA",
        "support_9x5":     "9×5 wsparcie w godzinach roboczych",
        "no_support":      "Brak informacji o wsparciu w konfiguracji.",
        "sup_pkg":         "Pakiet wsparcia",
        "sup_level":       "Poziom",
        "sup_term":        "Okres",
        "sup_years_unit":  "{n} lat",
        "sup_coverage":    "Godziny dostępności",
        "sup_fixtime":     "Fix-time SLA",
        "sup_fixtime_yes": "Tak — 24h on-site committed fix",
        "sup_fixtime_no":  "Brak fix-time SLA",
        "sup_desc":        "Opis",
        "cfg_model":       "Model",
        "cfg_mtm":         "Machine Type-Model",
        "cfg_form":        "Obudowa",
        "cfg_processor":   "Procesor",
        "cfg_cores":       "Aktywowane rdzenie",
        "cfg_physical":    "Fizyczne rdzenie (łącznie)",
        "cfg_memory":      "Pojemność pamięci",
        "cfg_mem_type":    "Typ / taktowanie pamięci",
        "cfg_mem_mirror":  "Mirroring pamięci",
        "cfg_nvme":        "Wewnętrzna pamięć NVMe",
        "cfg_fc":          "Łączność Fibre Channel",
        "cfg_roce":        "Sieć (RoCE)",
        "cfg_psu":         "Zasilanie",
        "cfg_os":          "System operacyjny",
        "cfg_sap":         "Certyfikacja SAP HANA",
        "cfg_powervm":     "Wirtualizacja (PowerVM)",
        "cfg_powerha":     "Wysoka dostępność (PowerHA)",
        "cfg_powersc":     "Bezpieczeństwo (PowerSC)",
        "cfg_powervc":     "Zarządzanie chmurą (PowerVC)",
        "cfg_hmc":         "Konsola zarządzania (HMC)",
        "cfg_expert_labs": "Wdrożenie Expert Labs",
        "cfg_support":     "Pakiet wsparcia",
        "perf_sap_hana":   "SAP HANA In-Memory",
        "perf_saps":       "SAPS (benchmark OLTP)",
        "perf_memory_bw":  "Przepustowość pamięci",
        "perf_ai":         "Możliwości AI/Inference",
        "perf_scale":      "Scale-Out",
        "perf_latency":    "Czas odpowiedzi DB",
        "sw_title":        "Komponenty oprogramowania",
        "price_info":      "Ceny katalogowe z IBM e-config · Rabat: {d:.1f}% · Oferta ważna do: {vu}",
        "price_cat":       "Kategoria",
        "price_qty":       "Ilość",
        "price_list":      "Cena katalogowa ({curr})",
        "price_disc":      "Rabat",
        "price_eu_col":    "Cena dla klienta ({curr})",
        "price_hw":        "Sprzęt ({mc})",
        "price_sup":       "Expert Care Support",
        "price_sw":        "Oprogramowanie / Subskrypcje",
        "price_svc":       "Usługi profesjonalne",
        "price_ship":      "Dostawa i obsługa (nie podlega rabatowi)",
        "price_total":     "ŁĄCZNA CENA KATALOGOWA",
        "price_eu_row":    "CENA DLA KLIENTA",
        "price_fn": (
            "* Ceny nie zawierają podatków. "
            "Niniejsza oferta jest ważna przez 30 dni od daty sporządzenia. "
            "Ostateczna cena podlega zatwierdzeniu przez IBM. "
            "Opłaty za dostawę i obsługę nie podlegają rabacie."
        ),
        "next_1_title":    "Sesja techniczna / warsztat",
        "next_1_body":     "Zaplanuj sesję techniczną z {client}, aby zweryfikować konfigurację Power11 pod kątem wymiarowania SAP HANA, wymagań obciążeń AIX/Linux i architektury sieciowej.",
        "next_2_title":    "Formalna wycena",
        "next_2_body":     "Na żądanie IBM lub autoryzowany IBM Business Partner wystawi formalną wycenę ważną 30 dni, z odniesieniem do konfiguracji z niniejszego dokumentu.",
        "next_3_title":    "Złożenie zamówienia",
        "next_3_body":     "Zamówienia składane są przez autoryzowanego dystrybutora IBM lub bezpośrednio w IBM. Standardowy czas realizacji serwerów IBM Power11 wynosi 6–10 tygodni od przyjęcia zamówienia.",
        "next_4_title":    "Wdrożenie IBM Expert Labs",
        "next_4_body":     "IBM Expert Labs zarządza instalacją on-site, konfiguracją AIX/Linux, konfiguracji LPAR PowerVM, integracją sieciową i wstępnymi testami wydajności.",
        "docs_heading":    "Dokumentacja produktu",
        "docs_ibm_docs":   "IBM Documentation",
        "docs_sales_manual": "IBM Sales Manual",
        "contact":         "Kontakt: {name} · IBM Power Sales",
        "disclaimer": (
            "Niniejszy dokument przygotowany jest dla IBM Business Partners i ich klientów. "
            "Prezentowane ceny są cenami katalogowymi z IBM e-config i nie stanowią wiążącej oferty. "
            "Dane wydajnościowe mają charakter orientacyjny i oparte są na opublikowanych wynikach IBM — "
            "nie stanowią gwarancji. "
            "IBM, Power, AIX, PowerVM, PowerHA, SAP HANA są znakami towarowymi ich właścicieli."
        ),
    },
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_power_exec_summary(
    project: dict[str, Any],
    client_name: str = "",
    seller_name: str = "",
    discount_pct: float = 60.0,
    num_systems: int = 1,
    eu_margin_pct: float = 15.0,
    lang: str = "en",
) -> bytes:
    """Generate Power11 Executive Summary DOCX and return as bytes."""
    T = _TRANS.get(lang, _TRANS["en"])

    doc = Document()
    _set_page_margins(doc)
    _set_default_font(doc)

    model_code = project.get("model_code", "")
    model_info = get_model_info(model_code)
    pricing    = _calc_pricing(project, discount_pct, num_systems=num_systems, eu_margin_pct=eu_margin_pct)

    _add_cover_page(doc, project, model_info, client_name, seller_name, T)
    doc.add_page_break()

    _add_logo_header(doc)
    _add_exec_summary_text(doc, project, model_info, client_name, T, num_systems=num_systems)
    _add_section_heading(doc, T["sec_config"])
    _add_config_table(doc, project, model_info, T)
    _add_section_heading(doc, T["sec_performance"])
    _add_performance_section(doc, project, T)
    _add_section_heading(doc, T["sec_software"])
    _add_software_section(doc, project, T)
    _add_section_heading(doc, T["sec_support"])
    _add_support_section(doc, project, T)
    _add_section_heading(doc, T["sec_pricing"])
    _add_pricing_table(doc, pricing, project, T)
    _add_section_heading(doc, T["sec_next"])
    _add_next_steps(doc, project, model_info, client_name, seller_name, T)
    _add_footer_disclaimer(doc, T)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def _add_cover_page(doc, project, model_info, client_name, seller_name, T):
    from app.generators.exec_summary import (
        _add_logo_header, _set_cell_bg, _set_cell_text, _para_space,
        _get_logo_png, _convert_to_png,
    )

    _add_logo_header(doc)

    # Server image
    _img_name = model_info.get("image", "")
    if _img_name:
        _img_path = IMAGES_DIR / _img_name
        if _img_path.exists():
            try:
                img_p = doc.add_paragraph()
                img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                _para_space(img_p, before=16, after=8)
                run = img_p.add_run()
                run.add_picture(str(_img_path), width=Inches(3.0))
            except Exception:
                pass

    # Title block
    title_p = doc.add_paragraph()
    _para_space(title_p, before=20, after=4)
    run = title_p.add_run(T["cover_subtitle"])
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = IBM_DARK

    model_name = model_info.get("name", project.get("model_name", "IBM Power Server"))
    sub_p = doc.add_paragraph()
    _para_space(sub_p, before=0, after=24)
    run = sub_p.add_run(model_name)
    run.font.size = Pt(16)
    run.font.color.rgb = IBM_BLUE

    # Meta table
    table = doc.add_table(rows=4, cols=2)
    table.style = "Table Grid"
    _date_fmt = "%d.%m.%Y" if T.get("date") == "Data" else "%B %d, %Y"
    today = date.today()
    valid = today + timedelta(days=30)

    meta_rows = [
        (T["prepared_for"], client_name or "—"),
        (T["prepared_by"],  seller_name or "—"),
        (T["date"],         today.strftime(_date_fmt)),
        (T["valid_until"],  valid.strftime(_date_fmt)),
    ]
    for i, (label, value) in enumerate(meta_rows):
        row = table.rows[i]
        _set_cell_bg(row.cells[0], IBM_DARK)
        _set_cell_text(row.cells[0], label, bold=True, color=IBM_WHITE, size=9)
        _set_cell_text(row.cells[1], value, size=10)


# ---------------------------------------------------------------------------
# Logo header
# ---------------------------------------------------------------------------

def _add_logo_header(doc):
    from app.generators.exec_summary import _add_logo_header as _fs_logo
    _fs_logo(doc)


# ---------------------------------------------------------------------------
# Executive Summary narrative
# ---------------------------------------------------------------------------

def _add_exec_summary_text(doc, project, model_info, client_name, T, num_systems: int = 1):
    from app.generators.exec_summary import _add_section_heading, _para_space

    _add_section_heading(doc, T["sec_exec"])

    model_name    = model_info.get("name", project.get("model_name", "IBM Power Server"))
    cores         = project.get("total_cores_activated", project.get("physical_cores", 0))
    processor_desc = project.get("processor_desc", "Power11 processor")
    memory_tb     = project.get("memory_tb", 0.0)
    nvme_count    = project.get("nvme_count", 0)
    fc_ports      = project.get("fc_ports", 0)
    support_info  = project.get("support_info") or {}
    support_name  = support_info.get("name", "IBM Expert Care")
    support_years = support_info.get("years", 5)
    client_str    = f"for {client_name} " if client_name else ""

    if num_systems > 1:
        note_p = doc.add_paragraph()
        _para_space(note_p, before=0, after=8)
        run = note_p.add_run(T["multi_system_note"].format(n=num_systems, model=model_name))
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = IBM_BLUE

    body = T["body"].format(
        client_str=client_str,
        model_name=model_name,
        cores=cores,
        processor_desc=processor_desc,
        memory_tb=memory_tb,
        nvme_count=nvme_count,
        fc_ports=fc_ports,
        support_name=support_name,
        support_years=support_years,
    )
    p = doc.add_paragraph(body)
    _para_space(p, before=0, after=12)
    for run in p.runs:
        run.font.size = Pt(10)
        run.font.color.rgb = IBM_DARK

    # Highlights
    _hl_key = "highlights_pl" if T.get("key_highlights") == "Kluczowe cechy rozwiązania" else "highlights"
    highlights = model_info.get(_hl_key) or model_info.get("highlights", [])
    if highlights:
        hl_p = doc.add_paragraph()
        run = hl_p.add_run(T["key_highlights"])
        run.font.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = IBM_BLUE
        _para_space(hl_p, before=6, after=2)
        for hl in highlights:
            bp = doc.add_paragraph(style="List Bullet")
            run = bp.add_run(hl)
            run.font.size = Pt(10)
            run.font.color.rgb = IBM_DARK
            _para_space(bp, before=0, after=1)

    # Platform advantages
    adv_p = doc.add_paragraph()
    run = adv_p.add_run(T["platform_advantages"])
    run.font.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = IBM_BLUE
    _para_space(adv_p, before=8, after=2)

    for key in ("adv1", "adv2", "adv3", "adv4"):
        ap = doc.add_paragraph(style="List Bullet")
        run = ap.add_run(T[key])
        run.font.size = Pt(10)
        run.font.color.rgb = IBM_DARK
        _para_space(ap, before=0, after=2)


# ---------------------------------------------------------------------------
# Configuration table
# ---------------------------------------------------------------------------

def _add_config_table(doc, project, model_info, T):
    from app.generators.exec_summary import _make_two_col_table

    model_name  = model_info.get("name", project.get("model_name", "—"))
    model_code  = project.get("model_code", "—")
    cores       = project.get("total_cores_activated", project.get("physical_cores", 0))
    phys_cores  = project.get("physical_cores", cores)
    proc_desc   = project.get("processor_desc", "—")
    proc_ghz    = ""
    if project.get("processor_ghz_min") and project.get("processor_ghz_max"):
        proc_ghz = (f"{project['processor_ghz_min']} – {project['processor_ghz_max']} GHz")
    proc_full   = f"{proc_desc} ({proc_ghz})" if proc_ghz else proc_desc

    mem_gb   = project.get("memory_gb", 0)
    mem_tb   = project.get("memory_tb", 0.0)
    mem_type = project.get("memory_type", "DDR5")
    mem_freq = project.get("memory_freq_mhz", 4000)
    mem_mirr = project.get("memory_mirroring", False)
    mem_str  = (f"{mem_tb:.1f} TB  /  {mem_gb:,} GB  ({mem_type} {mem_freq} MHz)"
                if mem_tb else f"{mem_gb:,} GB ({mem_type} {mem_freq} MHz)")
    mem_mirr_str = "Active Memory Mirroring enabled" if mem_mirr else "Standard"

    nvme_count = project.get("nvme_count", 0)
    nvme_desc  = project.get("nvme_desc", "NVMe U.2")
    nvme_str   = f"{nvme_count} × {nvme_desc}" if nvme_count else "—"

    fc_ports   = project.get("fc_ports", 0)
    fc_str     = f"{fc_ports} × 32 Gb Fibre Channel" if fc_ports else "—"

    roce_n     = project.get("roce_adapters", 0)
    roce_spd   = project.get("roce_speed_gbps", 25)
    roce_str   = f"{roce_n} × {roce_spd} GbE RoCE (dual-port)" if roce_n else "—"

    psu_cnt    = project.get("power_supply_count", 0)
    psu_str    = f"{psu_cnt} × hot-swap redundant PSU" if psu_cnt else "Redundant hot-swap"

    os_p       = project.get("os_primary", "Linux")
    os_s       = project.get("os_secondary", "")
    os_str     = os_p
    if os_s:
        os_str += f" + {os_s}"

    sap_str    = "Yes — SAP HANA TDI Certified" if project.get("sap_hana") else "No"
    pvm_str    = "Included (PowerVM for Linux)" if project.get("powervm") else "Not configured"
    pha_str    = "Included (PowerHA SystemMirror)" if project.get("powerha") else "Not configured"
    psc_str    = "Included (PowerSC)" if project.get("powersc") else "Not configured"
    pvc_str    = "Included (PowerVC)" if project.get("powervc") else "Not configured"
    hmc_str    = "Included (HMC Virtual Appliance)" if project.get("hmc_virtual") else "Not configured"

    labs_str   = ""
    if project.get("expert_labs"):
        qty   = project.get("expert_labs_qty", 1)
        price = project.get("expert_labs_price", 0.0)
        curr  = project.get("currency", "PLN")
        labs_str = (f"{qty} × Onsite Project Unit"
                    + (f" ({price:,.0f} {curr})" if price else ""))

    sup_info = project.get("support_info") or {}
    sup_str  = (f"{sup_info.get('name', '—')} · {sup_info.get('coverage', '—')} · "
                f"{sup_info.get('years', '—')} yr")

    rows = [
        (T["cfg_model"],    model_name),
        (T["cfg_mtm"],      model_code),
        (T["cfg_form"],     f"{model_info.get('form_factor','4U')} rack-mountable"),
        (T["cfg_processor"], proc_full),
        (T["cfg_cores"],    f"{cores} cores activated"),
        (T["cfg_physical"], f"{phys_cores} total physical cores"),
        (T["cfg_memory"],   mem_str),
        (T["cfg_mem_mirror"], mem_mirr_str),
        (T["cfg_nvme"],     nvme_str),
        (T["cfg_fc"],       fc_str),
        (T["cfg_roce"],     roce_str),
        (T["cfg_psu"],      psu_str),
        (T["cfg_os"],       os_str),
        (T["cfg_sap"],      sap_str),
        (T["cfg_powervm"],  pvm_str),
        (T["cfg_powerha"],  pha_str),
        (T["cfg_hmc"],      hmc_str),
    ]
    if project.get("powersc"):
        rows.insert(-2, (T["cfg_powersc"], psc_str))
    if project.get("powervc"):
        rows.insert(-2, (T["cfg_powervc"], pvc_str))
    if labs_str:
        rows.append((T["cfg_expert_labs"], labs_str))
    rows.append((T["cfg_support"], sup_str))

    _make_two_col_table(doc, rows)


# ---------------------------------------------------------------------------
# Performance section
# ---------------------------------------------------------------------------

def _add_performance_section(doc, project, T):
    from app.generators.exec_summary import _make_two_col_table, _para_space

    model_code = project.get("model_code", "")
    perf = _PERF_DATA.get(model_code, {})
    if not perf:
        p = doc.add_paragraph("Performance data not available for this model.")
        _para_space(p, before=0, after=6)
        for run in p.runs:
            run.font.size = Pt(9)
        return

    rows = []
    if "sap_hana" in perf:
        rows.append((T["perf_sap_hana"], perf["sap_hana"]))
    if "saps" in perf:
        rows.append((T["perf_saps"], perf["saps"]))
    if "memory_bw" in perf:
        rows.append((T["perf_memory_bw"], perf["memory_bw"]))
    if "ai" in perf:
        rows.append((T["perf_ai"], perf["ai"]))
    if "scale_out" in perf:
        rows.append((T["perf_scale"], perf["scale_out"]))
    if "db_latency" in perf:
        rows.append((T["perf_latency"], perf["db_latency"]))

    _make_two_col_table(doc, rows)


# ---------------------------------------------------------------------------
# Software section
# ---------------------------------------------------------------------------

def _add_software_section(doc, project, T):
    from app.generators.exec_summary import _para_space

    sw_items = []
    if project.get("powervm"):
        sw_items.append("IBM PowerVM (5765-VE4 / 5765-VL4) — enterprise hypervisor for LPAR virtualisation")
    if project.get("powerha"):
        sw_items.append("IBM PowerHA SystemMirror (5765-H39) — high availability clustering for AIX and Linux")
    if project.get("powersc"):
        sw_items.append("IBM PowerSC (5765-SC2) — security and compliance for IBM Power")
    if project.get("powervc"):
        sw_items.append("IBM PowerVC (5765-VC2) — cloud management for IBM Power (OpenStack-based)")
    if project.get("hmc_virtual"):
        sw_items.append("IBM HMC Virtual Appliance (5765-HMU) — hardware management console")
    if project.get("sap_hana"):
        sw_items.append("SUSE Linux Enterprise Server for SAP Applications (5639-SAP)")
    if project.get("os_aix"):
        sw_items.append("IBM AIX 7.3 — enterprise UNIX operating system")

    _title_p = doc.add_paragraph()
    run = _title_p.add_run(T["sw_title"])
    run.font.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = IBM_BLUE
    _para_space(_title_p, before=0, after=2)

    if sw_items:
        for item in sw_items:
            bp = doc.add_paragraph(style="List Bullet")
            run = bp.add_run(item)
            run.font.size = Pt(10)
            run.font.color.rgb = IBM_DARK
            _para_space(bp, before=0, after=1)
    else:
        p = doc.add_paragraph("Software components as per configuration.")
        _para_space(p, before=0, after=6)
        for run in p.runs:
            run.font.size = Pt(9)


# ---------------------------------------------------------------------------
# Support section
# ---------------------------------------------------------------------------

def _add_support_section(doc, project, T):
    from app.generators.exec_summary import _make_two_col_table, _para_space

    support_info = project.get("support_info") or {}
    if not support_info:
        p = doc.add_paragraph(T["no_support"])
        return

    rows = [
        (T["sup_pkg"],      support_info.get("name", "—")),
        (T["sup_level"],    support_info.get("level", "—")),
        (T["sup_term"],     T["sup_years_unit"].format(n=support_info.get("years", "—"))),
        (T["sup_coverage"], support_info.get("coverage", "—")),
        (T["sup_fixtime"],  T["sup_fixtime_yes"] if support_info.get("fix_time") else T["sup_fixtime_no"]),
        (T["sup_desc"],     support_info.get("description", "")),
    ]
    _make_two_col_table(doc, rows)


# ---------------------------------------------------------------------------
# Pricing table
# ---------------------------------------------------------------------------

def _add_pricing_table(doc, pricing, project, T):
    from app.generators.exec_summary import _add_pricing_table as _fs_pricing
    _fs_pricing(doc, pricing, project, T)


# ---------------------------------------------------------------------------
# Next steps + documentation links
# ---------------------------------------------------------------------------

def _add_next_steps(doc, project, model_info, client_name, seller_name, T):
    from app.generators.exec_summary import _para_space

    _client = client_name or "your organisation"
    steps = [
        (T["next_1_title"], T["next_1_body"].format(client=_client)),
        (T["next_2_title"], T["next_2_body"]),
        (T["next_3_title"], T["next_3_body"]),
        (T["next_4_title"], T["next_4_body"]),
    ]
    for i, (title, body) in enumerate(steps):
        row_p = doc.add_paragraph()
        _para_space(row_p, before=4 if i > 0 else 0, after=0)
        num_run = row_p.add_run(f"{i+1}. ")
        num_run.font.bold = True
        num_run.font.size = Pt(10)
        num_run.font.color.rgb = IBM_BLUE
        title_run = row_p.add_run(title)
        title_run.font.bold = True
        title_run.font.size = Pt(10)
        title_run.font.color.rgb = IBM_DARK

        body_p = doc.add_paragraph(body)
        _para_space(body_p, before=1, after=4)
        for run in body_p.runs:
            run.font.size = Pt(9)
            run.font.color.rgb = IBM_GRAY

    # Contact
    contact_p = doc.add_paragraph()
    _para_space(contact_p, before=8, after=0)
    cr = contact_p.add_run(T["contact"].format(name=seller_name or "your IBM Sales Representative"))
    cr.font.size = Pt(9)
    cr.font.bold = True
    cr.font.color.rgb = IBM_BLUE

    # Docs links
    _short    = model_info.get("short", "")
    _docs     = get_docs(_short) if _short else {}
    _docs_url = _docs.get("docs_url", "")
    _sm_url   = _docs.get("sales_manual_url", "")
    if _docs_url or _sm_url:
        doc.add_paragraph()
        heading_p = doc.add_paragraph()
        _para_space(heading_p, before=8, after=2)
        hr = heading_p.add_run(T["docs_heading"])
        hr.font.size = Pt(9)
        hr.font.bold = True
        hr.font.color.rgb = IBM_DARK

        def _link_para(label, url):
            p = doc.add_paragraph()
            _para_space(p, before=1, after=1)
            lbl = p.add_run(f"{label}: ")
            lbl.font.size = Pt(9)
            lbl.font.color.rgb = IBM_GRAY
            r_id = p.part.relate_to(url,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                is_external=True)
            hl = OxmlElement("w:hyperlink")
            hl.set(qn("r:id"), r_id)
            wr = OxmlElement("w:r")
            rpr = OxmlElement("w:rPr")
            style = OxmlElement("w:rStyle")
            style.set(qn("w:val"), "Hyperlink")
            rpr.append(style)
            sz = OxmlElement("w:sz")
            sz.set(qn("w:val"), "18")
            rpr.append(sz)
            wr.append(rpr)
            wt = OxmlElement("w:t")
            wt.text = url
            wr.append(wt)
            hl.append(wr)
            p._p.append(hl)

        if _docs_url:
            _link_para(T["docs_ibm_docs"], _docs_url)
        if _sm_url:
            _link_para(T["docs_sales_manual"], _sm_url)


# ---------------------------------------------------------------------------
# Footer disclaimer
# ---------------------------------------------------------------------------

def _add_footer_disclaimer(doc, T):
    from app.generators.exec_summary import _add_hrule, _para_space

    doc.add_paragraph()
    _add_hrule(doc)
    p = doc.add_paragraph()
    _para_space(p, before=4, after=0)
    run = p.add_run(T["disclaimer"])
    run.font.size = Pt(8)
    run.font.color.rgb = IBM_GRAY
    run.font.italic = True


# ---------------------------------------------------------------------------
# Pricing calculation
# ---------------------------------------------------------------------------

def _calc_pricing(project, discount_pct, num_systems=1, eu_margin_pct=15.0):
    from app.generators.exec_summary import _calc_pricing as _fs_calc
    return _fs_calc(project, discount_pct, num_systems=num_systems, eu_margin_pct=eu_margin_pct)


# ---------------------------------------------------------------------------
# DOCX helpers
# ---------------------------------------------------------------------------

def _set_page_margins(doc):
    from app.generators.exec_summary import _set_page_margins as _fs_margins
    _fs_margins(doc)


def _set_default_font(doc):
    from app.generators.exec_summary import _set_default_font as _fs_font
    _fs_font(doc)


def _add_section_heading(doc, text):
    from app.generators.exec_summary import _add_section_heading as _fs_heading
    _fs_heading(doc, text)
