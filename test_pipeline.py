"""
Quick smoke test — parse the test files and generate all 3 DOCX outputs.
Run: python3 test_pipeline.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.parsers.econfig_parser import parse_project
from app.generators.exec_summary import generate_exec_summary
from app.generators.rfp_generator import generate_rfp
from app.generators.special_bid_generator import generate_special_bid

CSV         = "TEST-FS5600_120TiB.csv"
CAPACITY    = "TEST-FS5600_120TiB-summary.xlsx"
PERFORMANCE = "TEST-FS5600_120TiB-performance.xlsx"

print("=== BobFromSales — Pipeline Smoke Test ===\n")

print("1. Parsing files...")
project = parse_project(CSV, CAPACITY, PERFORMANCE)

print(f"   Model code     : {project['model_code']}")
print(f"   Drives         : {project['drives_count']} × {project.get('drive_type','?')}")
print(f"   Raw capacity   : {project['raw_tb']:.2f} TB  /  {project['raw_tib']:.2f} TiB")
print(f"   Usable         : {project['usable_tb']:.2f} TB  /  {project['usable_tib']:.2f} TiB")
print(f"   Effective      : {project['effective_tb']:.2f} TB")
print(f"   RAID           : {project['raid_type']}")
print(f"   Cache          : {project['cache_gb']} GB")
print(f"   FC ports       : {project['fc_ports']}")
print(f"   Encryption     : {project['encryption']}")
print(f"   Support        : {project.get('support_info', {}).get('name','N/A')}")
print(f"   List price HW  : {project['list_price_hw']:,.2f} {project['currency']}")
print(f"   List price SUP : {project['list_price_support']:,.2f} {project['currency']}")
print(f"   List price SW  : {project['list_price_sw']:,.2f} {project['currency']}")
print(f"   Shipping       : {project['shipping']:,.2f} {project['currency']}")
print(f"   IOPS           : {project['perf_iops_total']:,}")
print(f"   Max IOPS<1ms   : {project.get('perf_iops_max_sub1ms',0):,} @ {project.get('perf_latency_at_max_sub1ms',0):.3f} ms")
print(f"   Latency        : {project['perf_latency_ms']:.3f} ms")
print(f"   Throughput     : {project['perf_throughput_mib']:,.1f} MiB/s")
print(f"   Power typical  : {project['power_kw_typical']:.3f} kW")
print(f"   Cooling        : {project['cooling_btu']:,.0f} BTU/h")

# ── 1. Executive Summary ─────────────────────────────────────────────────────
print("\n2. Generating Executive Summary DOCX (60% discount)...")
docx_bytes = generate_exec_summary(
    project=project,
    client_name="Test Customer Sp. z o.o.",
    seller_name="Jan Kowalski",
    discount_pct=60.0,
)
out_es = Path("TEST_output_ExecSummary.docx")
out_es.write_bytes(docx_bytes)
print(f"   Output: {out_es}  ({len(docx_bytes)/1024:.1f} KB)")

# ── 2. RFP / RFI ─────────────────────────────────────────────────────────────
print("\n3. Generating RFP / RFI DOCX...")
rfp_bytes = generate_rfp(
    project=project,
    client_name="Test Customer Sp. z o.o.",
    seller_name="Jan Kowalski",
)
out_rfp = Path("TEST_output_RFP.docx")
out_rfp.write_bytes(rfp_bytes)
print(f"   Output: {out_rfp}  ({len(rfp_bytes)/1024:.1f} KB)")

# ── 3. Special Bid Questionnaire ─────────────────────────────────────────────
print("\n4. Generating Special Bid Questionnaire DOCX (68% discount)...")
bid_bytes = generate_special_bid(
    project=project,
    client_name="Test Customer Sp. z o.o.",
    seller_name="Jan Kowalski",
    distributor_name="Arrow Electronics",
    reseller_name="ABC Systems Sp. z o.o.",
    discount_pct=68.0,
    opportunity_context=(
        "RFP na dostawę macierzy all-NVMe do Data Centre klienta. "
        "Zastąpienie incumbenta HPE 3PAR. Deadline składania ofert: 30 dni."
    ),
    deal_background=(
        "Konkurencyjne przetargi publiczne z udziałem Pure Storage i Dell EMC PowerStore. "
        "Wymagania pojemnościowe: min. 80 TiB usable, RAID 6, 24×7 support fix-time."
    ),
    competitor_info=(
        "Incumbent: HPE 3PAR 8400. Główni rywale: Pure Storage FA//C60, Dell EMC PowerStore 1200T. "
        "Estymowana cena Pure: 220k EUR. Dell: 200k EUR. IBM baseline @ 60%: 256k EUR."
    ),
    business_justification=(
        "Wymagany upust 68% (odchylenie 8 pp od baseline 60%) w celu osiągnięcia "
        "target price range 220–235k EUR i skutecznego konkurowania z Pure/Dell."
    ),
    deal_history="Brak poprzednich powiązanych ofert dla tego klienta.",
)
out_bid = Path("TEST_output_SpecialBid.docx")
out_bid.write_bytes(bid_bytes)
print(f"   Output: {out_bid}  ({len(bid_bytes)/1024:.1f} KB)")

print("\n=== All tests passed ✓ ===")
print(f"\nGenerated files:")
print(f"  • {out_es}")
print(f"  • {out_rfp}")
print(f"  • {out_bid}")
