"""
Product knowledge base: feature codes → descriptions, support codes → SLA, model → image/name.
"""

# ---------------------------------------------------------------------------
# Support feature-code → SLA mapping
# ---------------------------------------------------------------------------
# fix_time_hours: IBM Expert Care SLA commitment
# Basic — no fix-time; Advanced — NBD (next business day); Premium — 4h on-site
SUPPORT_CODES: dict[str, dict] = {
    # ALCN — 5 year Advanced 24hr Committed Fix (used in FS7600, FS9600 configs)
    "ALCN": {
        "name": "Expert Care Advanced 5 Year (24h Committed Fix)",
        "level": "Advanced",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "24h on-site committed fix",
        "description": "24×7 support with 24-hour on-site committed hardware fix-time SLA.",
    },
    "ALK3": {
        "name": "Expert Care Basic 3 Year",
        "level": "Basic",
        "years": 3,
        "coverage": "9×5",
        "fix_time": False,
        "fix_time_hours": None,
        "description": "9×5 business-hours support, no hardware fix-time SLA.",
    },
    "ALK5": {
        "name": "Expert Care Advanced 5 Year",
        "level": "Advanced",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "Next Business Day",
        "description": "24×7 around-the-clock support with hardware fix-time SLA.",
    },
    "ALKB": {
        "name": "Expert Care Basic 1 Year",
        "level": "Basic",
        "years": 1,
        "coverage": "9×5",
        "fix_time": False,
        "fix_time_hours": None,
        "description": "9×5 business-hours support, no hardware fix-time SLA.",
    },
    "ALKC": {
        "name": "Expert Care Advanced 1 Year",
        "level": "Advanced",
        "years": 1,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "Next Business Day",
        "description": "24×7 around-the-clock support with hardware fix-time SLA.",
    },
    "ALKD": {
        "name": "Expert Care Premium 1 Year",
        "level": "Premium",
        "years": 1,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "4 hours on-site",
        "description": "24×7 support with 4h on-site fix-time SLA and dedicated Technical Account Manager.",
    },
    "ALKE": {
        "name": "Expert Care Basic 3 Year",
        "level": "Basic",
        "years": 3,
        "coverage": "9×5",
        "fix_time": False,
        "fix_time_hours": None,
        "description": "9×5 business-hours support, no hardware fix-time SLA.",
    },
    "ALKF": {
        "name": "Expert Care Premium 3 Year",
        "level": "Premium",
        "years": 3,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "4 hours on-site",
        "description": "24×7 support with 4h on-site fix-time SLA and dedicated Technical Account Manager.",
    },
    "ALKG": {
        "name": "Expert Care Premium 5 Year",
        "level": "Premium",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "4 hours on-site",
        "description": "24×7 support with 4h on-site fix-time SLA and dedicated Technical Account Manager.",
    },
    # Fallback for Advanced 5Y
    "EC_ADVANCED_5Y": {
        "name": "Expert Care Advanced 5 Year",
        "level": "Advanced",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "Next Business Day",
        "description": "24×7 around-the-clock support with hardware fix-time SLA.",
    },
    "ALKH": {
        "name": "Expert Care Advanced 3 Year",
        "level": "Advanced",
        "years": 3,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "Next Business Day",
        "description": "24×7 around-the-clock support with hardware fix-time SLA.",
    },
    "ALKJ": {
        "name": "Expert Care Advanced 5 Year",
        "level": "Advanced",
        "years": 5,
        "coverage": "24×7",
        "fix_time": True,
        "fix_time_hours": "Next Business Day",
        "description": "24×7 around-the-clock support with hardware fix-time SLA.",
    },
}

# ---------------------------------------------------------------------------
# Feature code → human-readable label
# ---------------------------------------------------------------------------
FEATURE_LABELS: dict[str, str] = {
    # ── FlashSystem FCM5 drives — verified from e-config CSV exports ──────────
    # FS5600 / FS5200 / FS7600 family
    "ADSJ": "6.6 TB FlashCore Module 5 (NVMe)",
    "ADSL": "26.4 TB FlashCore Module 5 (NVMe)",
    "ADSC": "38.4 TB FlashCore Module 5 (NVMe)",
    # FS9600 / FS9500 family (higher-density FCM5)
    "ADSM": "52.8 TB FlashCore Module 5 (NVMe)",
    "ADSN": "105.6 TB FlashCore Module 5 (NVMe)",
    # ── FlashSystem FCM4 drives ───────────────────────────────────────────────
    "ADSB": "4.8 TB FlashCore Module 4 (NVMe)",
    "ADSE": "9.6 TB FlashCore Module 4 (NVMe)",
    "ADSK": "19.2 TB FlashCore Module 4 (NVMe)",
    # ── FlashSystem 7300 NVMe SSD drives ─────────────────────────────────────
    "ADUQ": "15.36 TB NVMe SSD (FS7300)",
    "ADUR": "7.68 TB NVMe SSD (FS7300)",
    # ── FlashSystem 5045 / 5015 SAS Flash Drives ─────────────────────────────
    "AL83": "15.36 TB 12 Gb SAS 2.5\" Flash Drive",
    "AL84": "7.68 TB 12 Gb SAS 2.5\" Flash Drive",
    "AL85": "3.84 TB 12 Gb SAS 2.5\" Flash Drive",
    # ── FlashSystem 5045 / 5015 NL-SAS HDD (LFF expansion) ───────────────────
    "AL3F": "16 TB 7.2K 3.5\" NL-SAS HDD",
    "AL3G": "8 TB 7.2K 3.5\" NL-SAS HDD",
    "AL3H": "4 TB 7.2K 3.5\" NL-SAS HDD",
    # DS8000 drives
    "1752": "DS8000 2.5\" 15K SAS HDD",
    "1753": "DS8000 2.5\" SSD Flash",
    "1754": "DS8000 Exp Frame",
    # ── Connectivity ─────────────────────────────────────────────────────────
    "ALB9": "32 Gb FC Adapter Pair (4-port)",
    "ALBB": "32 Gb FC Adapter Pair (2-port)",
    "ALB7": "16 Gb FC Adapter Pair (4-port)",
    "ALBG": "16 Gb FC Adapter Pair (4-port) — FS5045/FS5015",
    "ALBC": "25 Gb iSCSI/NVMe-oF Adapter (4-port)",
    "ACSR": "5 m OM3 Fiber Cable (LC)",
    "ACSS": "25 m OM3 Fiber Cable (LC)",
    "ACUB": "1.5 m 12 Gb SAS Cable (mSAS HD)",
    # ── Encryption & security ─────────────────────────────────────────────────
    "ACEG": "Encryption Activated (Software)",
    "ALEC": "Encryption USB Drive Pack",
    # ── Cache upgrades ────────────────────────────────────────────────────────
    "ALGA": "32 GB Cache Upgrade",
    "ALGB": "64 GB Cache Upgrade",
    # ── Support ──────────────────────────────────────────────────────────────
    "ALH0": "Expert Care Indicator",
    "ALK3": "Expert Care Basic 3 Year",
    "ALK5": "Expert Care Advanced 5 Year",
    "ALKH": "Expert Care Advanced 3 Year",
    "ALKJ": "Expert Care Advanced 5 Year",
    "ALKF": "Expert Care Premium 3 Year",
    "ALKG": "Expert Care Premium 5 Year",
    # ── Misc ─────────────────────────────────────────────────────────────────
    "AKCH": "Standard S&H Indicator",
    "9730": "Power Cord — PDU Connection",
    "AHZE": "Hybrid Flash Indicator",
    "AHZD": "All Flash Solution Indicator",
    "ACEV": "IBM Spectrum Virtualize Subscription",
    "ACEW": "IBM Storage Insights Pro (1Y)",
    "ACEX": "IBM Copy Services (Metro Mirror / Global Mirror)",
}

# ---------------------------------------------------------------------------
# Model → product metadata
# ---------------------------------------------------------------------------
# Mapping of e-config model codes to product metadata.
# Multiple codes can map to the same model (different configs/generations).
# ── Documentation links per product family (short name → urls) ────────────
_DOCS: dict[str, dict[str, str]] = {
    # ── Storage Scale ─────────────────────────────────────────────────────────
    "SS3500": {
        "docs_url":         "https://www.ibm.com/docs/en/storage-scale-system/3500",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-storage-scale-system-3500",
    },
    "SS6000": {
        "docs_url":         "https://www.ibm.com/docs/en/storage-scale-system/6000",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-storage-scale-system-6000",
    },
    "FS5600": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-5x00/9.1.3?topic=flashsystem-5600",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-storage-flashsystem-5600",
    },
    "FS5200": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-5x00/9.1.3?topic=flashsystem-5200",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-storage-flashsystem-5200",
    },
    "FS5045": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-5x00/9.1.3?topic=flashsystem-5045",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/flashsystem-5015-flashsystem-5045-2023-10-10",
    },
    "FS5015": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-5x00/9.1.3?topic=flashsystem-5015",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/flashsystem-5015-flashsystem-5045-2023-10-10",
    },
    "FS7300": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-7x00/9.1.3?topic=flashsystem-7300",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-storage-flashsystem-7300",
    },
    "FS7600": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-7x00/9.1.3?topic=flashsystem-7600",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-507501-storage-flashsystem-7600",
    },
    "FS9200": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-9x00/9.1.3?topic=flashsystem-9200",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-storage-flashsystem-9200",
    },
    "FS9500": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-9x00/9.1.3?topic=flashsystem-9500",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-storage-flashsystem-9500",
    },
    "FS9600": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-9x00/9.1.3?topic=flashsystem-9600",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-507801-storage-flashsystem-9600",
    },
    "FSC200": {
        "docs_url":         "https://www.ibm.com/docs/en/flashsystem-c200",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-storage-flashsystem-c200",
    },
    "DS8910F": {
        "docs_url":         "https://www.ibm.com/docs/en/ds8900",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-storage-ds8910f",
    },
    "DS8900F": {
        "docs_url":         "https://www.ibm.com/docs/en/ds8900",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-storage-ds8900f",
    },
    "E1080": {
        "docs_url":         "https://www.ibm.com/docs/en/power10/9080-HEX",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-servers-power-e1080",
    },
    "S1022": {
        "docs_url":         "https://www.ibm.com/docs/en/power10/9043-MRX",
        "sales_manual_url": "https://www.ibm.com/docs/en/announcements/family-512701-servers-power-s1022",
    },
}

MODEL_DB: dict[str, dict] = {
    # ── FlashSystem 5600 ───────────────────────────────────────────────────────
    "5127-A20": {
        "name": "IBM FlashSystem 5600",
        "short": "FS5600",
        "family": "FlashSystem",
        "form_factor": "1U",
        "total_drive_slots": 12,
        "image": "5127-A20.webp",
        "description": (
            "IBM FlashSystem 5600 is an all-NVMe enterprise storage system delivering "
            "industry-leading performance, built-in AI-powered ransomware detection via "
            "FlashCore Modules 5, and comprehensive data protection in a compact 1U form factor."
        ),
        "highlights": [
            "All-NVMe architecture with PCIe 4.0 internal bus",
            "AI-powered ransomware detection in every FlashCore Module 5",
            "Distributed RAID 6 with >2 TB/h rebuild throughput",
            "256 GB base cache (expandable to 512 GB)",
            "Software-defined encryption (no performance impact)",
            "Single management plane: GUI, CLI, REST API, Ansible",
        ],
        "highlights_pl": [
            "Architektura all-NVMe z magistralą wewnętrzną PCIe 4.0",
            "Sprzętowe wykrywanie ransomware w każdym FlashCore Module 5",
            "Distributed RAID 6 z przepustowością odbudowy >2 TB/h",
            "256 GB pamięci cache w bazowej konfiguracji (rozbudowa do 512 GB)",
            "Programowe szyfrowanie danych bez wpływu na wydajność",
            "Jednolita warstwa zarządzania: GUI, CLI, REST API, Ansible",
        ],
    },
    # ── FlashSystem 5200 ───────────────────────────────────────────────────────
    "5127-A10": {
        "name": "IBM FlashSystem 5200",
        "short": "FS5200",
        "family": "FlashSystem",
        "form_factor": "1U",
        "total_drive_slots": 12,
        "image": "IBM-FS5000-FS.png",
        "description": (
            "IBM FlashSystem 5200 delivers NVMe performance for mid-range workloads "
            "in a cost-efficient 1U package."
        ),
        "highlights": [
            "All-NVMe architecture",
            "Distributed RAID with fast rebuild",
            "Flexible connectivity: FC and iSCSI/NVMe-oF",
        ],
        "highlights_pl": [
            "Architektura all-NVMe",
            "Distributed RAID z szybką odbudową",
            "Elastyczna łączność: FC oraz iSCSI/NVMe-oF",
        ],
    },
    # ── FlashSystem 9600 ───────────────────────────────────────────────────────
    "5078-A40": {
        "name": "IBM FlashSystem 9600",
        "short": "FS9600",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 32,
        "image": "IBM-FS9600-FS.png",
        "description": (
            "IBM FlashSystem 9600 is the new generation flagship all-NVMe array with "
            "FlashCore Module 5 and AI-powered cyber resilience for the most demanding workloads."
        ),
        "highlights": [
            "Up to 19.2M IOPS per system",
            "Sub-100 µs latency end-to-end",
            "AI-powered ransomware detection via FCM5",
            "Policy-based active-active HA replication up to 4 nodes",
            "Integrated Cyber Vault with immutable snapshots",
        ],
        "highlights_pl": [
            "Do 19,2 mln IOPS na system",
            "Opóźnienie end-to-end poniżej 100 µs",
            "Sprzętowe wykrywanie ransomware w każdym FlashCore Module 5",
            "Replikacja active-active HA sterowana politykami do 4 węzłów",
            "Zintegrowany Cyber Vault z niezmiennymi snapshotami",
        ],
    },
    "5147-F99": {
        "name": "IBM FlashSystem 9600",
        "short": "FS9600",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 32,
        "image": "IBM-FS9600-FS.png",
        "description": (
            "IBM FlashSystem 9600 is the new generation flagship all-NVMe array with "
            "FlashCore Module 5 and AI-powered cyber resilience for the most demanding workloads."
        ),
        "highlights": [
            "Up to 19.2M IOPS per system",
            "Sub-100 µs latency end-to-end",
            "AI-powered ransomware detection via FCM5",
            "Policy-based active-active HA replication up to 4 nodes",
            "Integrated Cyber Vault with immutable snapshots",
        ],
        "highlights_pl": [
            "Do 19,2 mln IOPS na system",
            "Opóźnienie end-to-end poniżej 100 µs",
            "Sprzętowe wykrywanie ransomware w każdym FlashCore Module 5",
            "Replikacja active-active HA sterowana politykami do 4 węzłów",
            "Zintegrowany Cyber Vault z niezmiennymi snapshotami",
        ],
    },
    "5147-F96": {
        "name": "IBM FlashSystem 9500",
        "short": "FS9500",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 48,
        "image": "IBM-FS9600-FS.png",
        "description": (
            "IBM FlashSystem 9500 is the flagship enterprise all-NVMe array delivering "
            "millions of IOPS and sub-100µs latency for mission-critical workloads."
        ),
        "highlights": [
            "Up to 19.2M IOPS per system",
            "Sub-100 µs latency",
            "Policy-based active-active HA replication up to 4 nodes",
            "Integrated Cyber Vault with immutable copies",
        ],
        "highlights_pl": [
            "Do 19,2 mln IOPS na system",
            "Opóźnienie poniżej 100 µs",
            "Replikacja active-active HA sterowana politykami do 4 węzłów",
            "Zintegrowany Cyber Vault z niezmiennymi kopiami danych",
        ],
    },
    # ── FlashSystem 7600 ───────────────────────────────────────────────────────
    "5075-A30": {
        "name": "IBM FlashSystem 7600",
        "short": "FS7600",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 32,
        "image": "IBM-FS7600-FS.png",
        "description": (
            "IBM FlashSystem 7600 is a high-performance mid-to-enterprise NVMe array "
            "with FlashCore Module 5 and built-in AI-driven cyber resilience."
        ),
        "highlights": [
            "All-NVMe with FlashCore Module 5",
            "AI-powered ransomware detection at drive level",
            "Distributed RAID 6 with >2 TB/h rebuild",
            "NVMe-oF and Fibre Channel connectivity",
            "Integrated IBM Storage Virtualize",
        ],
        "highlights_pl": [
            "Architektura all-NVMe z FlashCore Module 5",
            "Sprzętowe wykrywanie ransomware na poziomie napędu",
            "Distributed RAID 6 z przepustowością odbudowy >2 TB/h",
            "Łączność NVMe-oF i Fibre Channel",
            "Zintegrowany IBM Storage Virtualize",
        ],
    },
    "5147-F76": {
        "name": "IBM FlashSystem 7600",
        "short": "FS7600",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 32,
        "image": "IBM-FS7600-FS.png",
        "description": (
            "IBM FlashSystem 7600 is a high-performance mid-to-enterprise NVMe array "
            "with FlashCore Module 5 and built-in AI-driven cyber resilience."
        ),
        "highlights": [
            "All-NVMe with FlashCore Module 5",
            "AI-powered ransomware detection at drive level",
            "Distributed RAID 6 with >2 TB/h rebuild",
            "NVMe-oF and Fibre Channel connectivity",
            "Integrated IBM Storage Virtualize",
        ],
        "highlights_pl": [
            "Architektura all-NVMe z FlashCore Module 5",
            "Sprzętowe wykrywanie ransomware na poziomie napędu",
            "Distributed RAID 6 z przepustowością odbudowy >2 TB/h",
            "Łączność NVMe-oF i Fibre Channel",
            "Zintegrowany IBM Storage Virtualize",
        ],
    },
    # ── FlashSystem 9200 ───────────────────────────────────────────────────────
    "5147-F92": {
        "name": "IBM FlashSystem 9200",
        "short": "FS9200",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 32,
        "image": "IBM-FS9600-FS.png",
        "description": (
            "IBM FlashSystem 9200 delivers high-end NVMe performance with integrated "
            "Spectrum Virtualize, designed for hybrid cloud and mission-critical applications."
        ),
        "highlights": [
            "Millions of IOPS at sub-200 µs latency",
            "Integrated HyperSwap for zero-RPO HA",
            "Active-active clustering across sites",
            "AI-powered analytics via IBM Storage Insights",
        ],
        "highlights_pl": [
            "Miliony IOPS przy opóźnieniu poniżej 200 µs",
            "Zintegrowany HyperSwap dla HA z RPO=0",
            "Klastrowanie active-active między lokalizacjami",
            "Analityka AI w IBM Storage Insights",
        ],
    },
    # ── FlashSystem 5045 / 5015 (4680-xxx — current SAS-based generation) ──────
    # MTM: 4680-3P4 = FS5045 SFF Control Enclosure (2U, up to 24 × 2.5" SAS Flash drives)
    #      4680-3P1 = FS5015 SFF Control Enclosure (2U, up to 12 × 2.5" SAS Flash drives)
    #      4680-12H / 4680-12L = LFF Expansion Enclosure (up to 12 × 3.5" NL-SAS HDD per shelf)
    "4680-3P4": {
        "name": "IBM FlashSystem 5045",
        "short": "FS5045",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 24,
        "image": "IBM-FS5000-FS.png",
        "description": (
            "IBM FlashSystem 5045 is a 2U enterprise storage system with 24 SAS Flash Drive "
            "slots and optional NL-SAS HDD expansion — delivering high-capacity all-flash or "
            "hybrid configurations with IBM Storage Virtualize and integrated cyber resilience."
        ),
        "highlights": [
            "Up to 24 × 2.5\" SAS Flash Drives in 2U",
            "Optional LFF NL-SAS HDD expansion for hybrid configurations",
            "WORM snapshots and software ransomware detection via IBM Storage Insights",
            "Distributed RAID 6 with fast rebuild — hot-add drives online",
            "16 Gb FC and iSCSI host connectivity",
        ],
        "highlights_pl": [
            "Do 24 napędów SAS Flash 2,5\" w obudowie 2U",
            "Opcjonalna rozbudowa o dyski NL-SAS HDD dla konfiguracji hybrydowych",
            "Niezmienne migawki WORM i programowe wykrywanie ransomware (IBM Storage Insights)",
            "Distributed RAID 6 z szybką odbudową — napędy dodawalne online",
            "Łączność hostów: 16 Gb FC oraz iSCSI",
        ],
    },
    "4680-3P1": {
        "name": "IBM FlashSystem 5015",
        "short": "FS5015",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 12,
        "image": "IBM-FS5000-FS.png",
        "description": (
            "IBM FlashSystem 5015 is an entry-level 2U storage system with 12 SAS Flash Drive "
            "slots and optional NL-SAS HDD expansion — cost-effective enterprise storage "
            "with IBM Storage Virtualize and built-in cyber resilience."
        ),
        "highlights": [
            "Up to 12 × 2.5\" SAS Flash Drives in 2U",
            "Optional LFF NL-SAS HDD expansion for hybrid configurations",
            "WORM snapshots and software ransomware detection via IBM Storage Insights",
            "Distributed RAID 6 with fast rebuild — hot-add drives online",
            "16 Gb FC and iSCSI host connectivity",
        ],
        "highlights_pl": [
            "Do 12 napędów SAS Flash 2,5\" w obudowie 2U",
            "Opcjonalna rozbudowa o dyski NL-SAS HDD dla konfiguracji hybrydowych",
            "Niezmienne migawki WORM i programowe wykrywanie ransomware (IBM Storage Insights)",
            "Distributed RAID 6 z szybką odbudową — napędy dodawalne online",
            "Łączność hostów: 16 Gb FC oraz iSCSI",
        ],
    },
    # ── FlashSystem 5045 / 5015 (legacy 5075-xxx / 5147-xxx generation) ────────
    "5075-A05": {
        "name": "IBM FlashSystem 5045",
        "short": "FS5045",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 24,
        "image": "IBM-FS5000-FS.png",
        "description": (
            "IBM FlashSystem 5045 is a compact enterprise storage system delivering "
            "performance and data protection with optional hybrid expansion."
        ),
        "highlights": [
            "Up to 24 × 2.5\" SAS Flash Drives in 2U",
            "Optional LFF NL-SAS HDD expansion for hybrid configurations",
            "AI-powered ransomware detection and WORM snapshots",
            "Distributed RAID 6 with fast rebuild",
            "FC and iSCSI connectivity",
        ],
        "highlights_pl": [
            "Do 24 napędów SAS Flash 2,5\" w obudowie 2U",
            "Opcjonalna rozbudowa o dyski NL-SAS HDD dla konfiguracji hybrydowych",
            "Sprzętowe wykrywanie ransomware i niezmienne snapshoty WORM",
            "Distributed RAID 6 z szybką odbudową",
            "Łączność FC oraz iSCSI",
        ],
    },
    "5075-A01": {
        "name": "IBM FlashSystem 5015",
        "short": "FS5015",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 12,
        "image": "IBM-FS5000-FS.png",
        "description": (
            "IBM FlashSystem 5015 is an entry-level enterprise storage system with optional "
            "hybrid HDD expansion, built-in cyber resilience, and IBM Storage Virtualize."
        ),
        "highlights": [
            "Up to 12 × 2.5\" SAS Flash Drives in 2U",
            "Optional LFF NL-SAS HDD expansion for hybrid configurations",
            "AI-powered ransomware detection and WORM snapshots",
            "Distributed RAID with fast rebuild",
            "FC and iSCSI connectivity",
        ],
        "highlights_pl": [
            "Do 12 napędów SAS Flash 2,5\" w obudowie 2U",
            "Opcjonalna rozbudowa o dyski NL-SAS HDD dla konfiguracji hybrydowych",
            "Sprzętowe wykrywanie ransomware i niezmienne snapshoty WORM",
            "Distributed RAID z szybką odbudową",
            "Łączność FC oraz iSCSI",
        ],
    },
    "5147-F55": {
        "name": "IBM FlashSystem 5045",
        "short": "FS5045",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 24,
        "image": "IBM-FS5000-FS.png",
        "description": (
            "IBM FlashSystem 5045 is a compact enterprise storage system delivering "
            "performance and data protection with optional hybrid expansion."
        ),
        "highlights": [
            "Up to 24 × 2.5\" SAS Flash Drives in 2U",
            "Optional LFF NL-SAS HDD expansion for hybrid configurations",
            "AI-powered ransomware detection and WORM snapshots",
            "Distributed RAID 6 with fast rebuild",
            "FC and iSCSI connectivity",
        ],
        "highlights_pl": [
            "Do 24 napędów SAS Flash 2,5\" w obudowie 2U",
            "Opcjonalna rozbudowa o dyski NL-SAS HDD dla konfiguracji hybrydowych",
            "Sprzętowe wykrywanie ransomware i niezmienne snapshoty WORM",
            "Distributed RAID 6 z szybką odbudową",
            "Łączność FC oraz iSCSI",
        ],
    },
    "5147-F51": {
        "name": "IBM FlashSystem 5015",
        "short": "FS5015",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 24,
        "image": "IBM-FS5000-FS.png",
        "description": (
            "IBM FlashSystem 5015 is an entry-level enterprise storage system with optional "
            "hybrid HDD expansion, built-in cyber resilience, and IBM Storage Virtualize."
        ),
        "highlights": [
            "Up to 24 × 2.5\" SAS Flash Drives in 2U",
            "Optional LFF NL-SAS HDD expansion for hybrid configurations",
            "AI-powered ransomware detection and WORM snapshots",
            "Distributed RAID with fast rebuild",
            "FC and iSCSI connectivity",
        ],
        "highlights_pl": [
            "Do 24 × dysków SAS Flash 2,5\" w obudowie 2U",
            "Opcjonalna rozbudowa o dyski NL-SAS HDD dla konfiguracji hybrydowych",
            "Sprzętowe wykrywanie ransomware i migawki WORM",
            "Distributed RAID z szybką odbudową",
            "Łączność FC i iSCSI",
        ],
    },
    # ── FlashSystem C200 ────────────────────────────────────────────────────────
    "5076-C20": {
        "name": "IBM FlashSystem C200",
        "short": "FSC200",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 24,
        "image": "IBM-FSc200-FS.png",
        "description": (
            "IBM FlashSystem C200 is a container-native all-flash storage system "
            "optimised for Red Hat OpenShift and Kubernetes environments."
        ),
        "highlights": [
            "Container-native with CSI integration for OpenShift/Kubernetes",
            "NVMe all-flash performance",
            "Integrated Spectrum Virtualize",
            "Purpose-built for cloud-native workloads",
        ],
        "highlights_pl": [
            "Natywna integracja z kontenerami poprzez CSI dla OpenShift/Kubernetes",
            "Wydajność all-flash NVMe",
            "Zintegrowany Spectrum Virtualize",
            "Zaprojektowany z myślą o obciążeniach cloud-native",
        ],
    },
    "5202-C25": {
        "name": "IBM FlashSystem C200",
        "short": "FSC200",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 24,
        "image": "IBM-FSc200-FS.png",
        "drives_count": 24,
        "drive_type": "25.6 TB NVMe SSD",
        "description": (
            "IBM FlashSystem C200 is a container-native all-flash storage system "
            "optimised for Red Hat OpenShift and Kubernetes environments."
        ),
        "highlights": [
            "Container-native with CSI integration for OpenShift/Kubernetes",
            "NVMe all-flash performance",
            "Integrated Spectrum Virtualize",
            "Purpose-built for cloud-native workloads",
        ],
        "highlights_pl": [
            "Natywna integracja z kontenerami poprzez CSI dla OpenShift/Kubernetes",
            "Wydajność all-flash NVMe",
            "Zintegrowany Spectrum Virtualize",
            "Zaprojektowany z myślą o obciążeniach cloud-native",
        ],
    },
    "5147-FC2": {
        "name": "IBM FlashSystem C200",
        "short": "FSC200",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 24,
        "image": "IBM-FSc200-FS.png",
        "description": (
            "IBM FlashSystem C200 is a container-native all-flash storage system "
            "optimised for Red Hat OpenShift and Kubernetes environments."
        ),
        "highlights": [
            "Container-native with CSI integration for OpenShift/Kubernetes",
            "NVMe all-flash performance",
            "Integrated Spectrum Virtualize",
            "Purpose-built for cloud-native workloads",
        ],
        "highlights_pl": [
            "Natywna integracja z kontenerami poprzez CSI dla OpenShift/Kubernetes",
            "Wydajność all-flash NVMe",
            "Zintegrowany Spectrum Virtualize",
            "Zaprojektowany z myślą o obciążeniach cloud-native",
        ],
    },
    # ── FlashSystem 7300 ───────────────────────────────────────────────────────
    "5147-F73": {
        "name": "IBM FlashSystem 7300",
        "short": "FS7300",
        "family": "FlashSystem",
        "form_factor": "2U",
        "total_drive_slots": 24,
        "image": "IBM-FS7600-FS.png",
        "description": (
            "IBM FlashSystem 7300 is a mid-to-high range all-NVMe array optimised for "
            "enterprise workloads requiring high IOPS and low latency at scale."
        ),
        "highlights": [
            "All-NVMe with NVMe-oF connectivity",
            "Distributed RAID 6 with fast rebuild",
            "Integrated Spectrum Virtualize",
            "Scale-up and scale-out architecture",
        ],
        "highlights_pl": [
            "Architektura all-NVMe z łącznością NVMe-oF",
            "Distributed RAID 6 z szybką odbudową",
            "Zintegrowany Spectrum Virtualize",
            "Architektura scale-up i scale-out",
        ],
    },
    # ── Storage Scale System 3500 — ESS (Elastic Storage Server) nodes ────────
    # 5141-FN2: ESS 3500 Capacity Model (NVMe data server + optional HDD shelf)
    "5141-FN2": {
        "name": "IBM Storage Scale System 3500",
        "short": "ESS3500",
        "family": "Storage Scale",
        "form_factor": "2U",
        "image": "IBM-ESS3500.png",
        "description": (
            "IBM Storage Scale System 3500 (ESS 3500) is a hybrid NVMe + HDD parallel "
            "file storage system powered by IBM Storage Scale (GPFS). The data server "
            "delivers NVMe SSD performance while the optional 4U102 HDD shelf provides "
            "high-capacity nearline storage — ideal for AI, HPC, and large-scale analytics."
        ),
        "highlights": [
            "Hybrid NVMe + SAS HDD parallel file storage",
            "IBM Storage Scale (GPFS) — built-in parallel file system",
            "NVMe data server (5141-FN2) with AMD EPYC processor",
            "Optional 4U102 HDD shelf (5147-102) for nearline capacity",
            "NDR InfiniBand 200 Gb/s fabric connectivity",
            "NVIDIA-Certified Storage — validated for GPU-accelerated AI/ML",
            "SED encryption on HDD drives",
            "Scale-out: add nodes non-disruptively",
        ],
    },
    "5141-FN1": {
        "name": "IBM Storage Scale System 3500",
        "short": "ESS3500",
        "family": "Storage Scale",
        "form_factor": "2U",
        "image": "IBM-ESS3500.png",
        "description": (
            "IBM Storage Scale System 3500 (ESS 3500) parallel file storage system "
            "with IBM Storage Scale (GPFS), NVMe data server and optional HDD shelf."
        ),
        "highlights": [
            "Hybrid NVMe + SAS HDD parallel file storage",
            "IBM Storage Scale (GPFS) parallel file system",
            "NDR InfiniBand 200 Gb/s fabric",
            "NVIDIA-Certified Storage for AI/ML workloads",
            "Scale-out architecture",
        ],
    },
    # 5149-23E: ESS Protocol Node / Management Server (utility node)
    "5149-23E": {
        "name": "IBM Storage Scale System 3500",
        "short": "ESS3500",
        "family": "Storage Scale",
        "form_factor": "2U",
        "image": "IBM-ESS3500.png",
        "description": (
            "IBM Storage Scale System 3500 utility server — serves as Protocol Node "
            "or Management Server in ESS 3500 configurations."
        ),
        "highlights": [
            "IBM Storage Scale (GPFS) protocol and management functions",
            "NDR InfiniBand 200 Gb/s connectivity",
            "Red Hat Enterprise Linux pre-installed",
        ],
    },
    # ── Storage Scale System 3500 ──────────────────────────────────────────────
    "4664-S3H": {
        "name": "IBM Storage Scale System 3500",
        "short": "SS3500",
        "family": "Storage Scale",
        "form_factor": "2U",
        "image": None,
        "description": (
            "IBM Storage Scale System 3500 is a high-density, high-performance parallel "
            "file storage system delivering scalable NVMe-based capacity with built-in "
            "IBM Storage Scale (GPFS) software for AI, analytics, and HPC workloads."
        ),
        "highlights": [
            "All-NVMe parallel file storage with IBM Storage Scale (GPFS)",
            "Scale-out architecture — add nodes non-disruptively",
            "High-density 2U node: NVMe SSDs + RDMA networking",
            "Native integration with AI and HPC schedulers",
            "Erasure coding for data protection without dedicated spares",
            "Transparent cloud tiering to object storage",
        ],
    },
    "4664-S3A": {
        "name": "IBM Storage Scale System 3500",
        "short": "SS3500",
        "family": "Storage Scale",
        "form_factor": "2U",
        "image": None,
        "description": (
            "IBM Storage Scale System 3500 is a high-density, high-performance parallel "
            "file storage system delivering scalable NVMe-based capacity with built-in "
            "IBM Storage Scale (GPFS) software for AI, analytics, and HPC workloads."
        ),
        "highlights": [
            "All-NVMe parallel file storage with IBM Storage Scale (GPFS)",
            "Scale-out architecture — add nodes non-disruptively",
            "High-density 2U node: NVMe SSDs + RDMA networking",
            "Native integration with AI and HPC schedulers",
            "Erasure coding for data protection without dedicated spares",
            "Transparent cloud tiering to object storage",
        ],
    },
    # ── Storage Scale System 6000 ──────────────────────────────────────────────
    "4665-S6H": {
        "name": "IBM Storage Scale System 6000",
        "short": "SS6000",
        "family": "Storage Scale",
        "form_factor": "2U",
        "image": None,
        "description": (
            "IBM Storage Scale System 6000 is the flagship all-NVMe parallel file storage "
            "system, purpose-built for the most demanding AI training, analytics, and HPC "
            "workloads, delivering extreme throughput and low latency at scale."
        ),
        "highlights": [
            "Purpose-built for AI training and large-scale analytics",
            "All-NVMe 2U storage server with PCIe 5.0 drives",
            "Up to 368 TB raw per 2U node",
            "NDR InfiniBand and Ethernet connectivity",
            "IBM Storage Scale (GPFS) parallel file system built-in",
            "Erasure coding — no dedicated spare drives required",
            "Transparent cloud tiering and data lifecycle management",
        ],
    },
    "4665-S6A": {
        "name": "IBM Storage Scale System 6000",
        "short": "SS6000",
        "family": "Storage Scale",
        "form_factor": "2U",
        "image": None,
        "description": (
            "IBM Storage Scale System 6000 is the flagship all-NVMe parallel file storage "
            "system, purpose-built for the most demanding AI training, analytics, and HPC "
            "workloads, delivering extreme throughput and low latency at scale."
        ),
        "highlights": [
            "Purpose-built for AI training and large-scale analytics",
            "All-NVMe 2U storage server with PCIe 5.0 drives",
            "Up to 368 TB raw per 2U node",
            "NDR InfiniBand and Ethernet connectivity",
            "IBM Storage Scale (GPFS) parallel file system built-in",
            "Erasure coding — no dedicated spare drives required",
            "Transparent cloud tiering and data lifecycle management",
        ],
    },
    # ── DS8000 ─────────────────────────────────────────────────────────────────
    "2107-E8S": {
        "name": "IBM DS8910F",
        "short": "DS8910F",
        "family": "DS8000",
        "form_factor": "7U",
        "image": None,
        "description": (
            "IBM DS8910F is the flagship enterprise storage system for IBM Z and IBM Power, "
            "delivering sub-100 µs latency, eight-nines availability, and end-to-end encryption."
        ),
        "highlights": [
            "Eight-nines (99.999999%) availability",
            "Pervasive encryption — no performance overhead",
            "Transparent cloud tiering to IBM Cloud Object Storage",
            "Native z/OS Global Mirror and Metro Mirror",
        ],
    },
    "2107-E8E": {
        "name": "IBM DS8900F",
        "short": "DS8900F",
        "family": "DS8000",
        "form_factor": "7U",
        "image": None,
        "description": (
            "IBM DS8900F enterprise storage delivers mission-critical performance "
            "for IBM Z mainframe and IBM Power environments."
        ),
        "highlights": [
            "Optimised for IBM Z and IBM Power workloads",
            "End-to-end AES-256 encryption",
            "Integrated z/OS HyperPAV and parallel access volumes",
            "Global and Metro Mirror replication",
        ],
    },
    # ── IBM Power ──────────────────────────────────────────────────────────────
    "9080-HEX": {
        "name": "IBM Power E1080",
        "short": "E1080",
        "family": "IBM Power",
        "form_factor": "4U",
        "image": None,
        "description": (
            "IBM Power E1080 is the flagship Power10 server designed for "
            "mission-critical AI and enterprise workloads with unmatched RAS features."
        ),
        "highlights": [
            "Up to 240 Power10 cores",
            "MMA (Matrix Math Accelerator) for AI inference",
            "Up to 64 TB of DDR4 memory",
            "Hot-swap everything for maximum availability",
        ],
    },
    "9043-MRX": {
        "name": "IBM Power S1022",
        "short": "S1022",
        "family": "IBM Power",
        "form_factor": "2U",
        "image": None,
        "description": (
            "IBM Power S1022 is a 2-socket Power10 server delivering outstanding "
            "performance-per-watt for cloud, AI, and mixed workloads."
        ),
        "highlights": [
            "Up to 48 Power10 cores in 2U",
            "PCIe 5.0 and OpenCAPI 5.0 I/O",
            "Integrated MMA for on-chip AI acceleration",
            "PowerVM hypervisor for LPAR virtualisation",
        ],
    },
}

def get_docs(short: str) -> dict[str, str]:
    """Return documentation URLs for a product short name (e.g. 'FS5600')."""
    return _DOCS.get(short, {})


def get_model_info(model_code: str) -> dict:
    return MODEL_DB.get(model_code, {
        "name": f"IBM Storage {model_code}",
        "short": model_code,
        "family": "IBM Storage",
        "form_factor": "N/A",
        "image": None,
        "description": "IBM enterprise storage solution.",
        "highlights": [],
    })

def get_support_info(feature_code: str) -> dict | None:
    return SUPPORT_CODES.get(feature_code)

def get_feature_label(feature_code: str) -> str:
    return FEATURE_LABELS.get(feature_code, feature_code)
