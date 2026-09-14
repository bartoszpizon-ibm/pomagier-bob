"""
Special Bid generator for IBM Power11 servers (L1124 / E1150 / E1180).
Reuses the same DOCX template as FlashSystem; the underlying
generate_special_bid() is template-agnostic — only the pricing and
narrative texts differ for Power.
"""
from __future__ import annotations

from typing import Any

from .special_bid_generator import generate_special_bid
from ..knowledge.product_db import get_model_info


def generate_power_special_bid(
    project: dict[str, Any],
    client_name: str = "",
    seller_name: str = "",
    distributor_name: str = "",
    reseller_name: str = "",
    discount_pct: float = 60.0,
    eu_margin_pct: float = 15.0,
    opportunity_context: str = "",
    deal_background: str = "",
    competitor_info: str = "",
    deal_history: str = "",
    business_justification: str = "",
    extended_validity_days: int = 0,
    extended_validity_reason: str = "",
    num_systems: int = 1,
) -> bytes:
    """
    Generate a Special Bid request DOCX for an IBM Power11 server opportunity.

    Auto-builds pricing justification and opportunity context with
    Power-appropriate language if the caller leaves them blank.
    """
    model_code = project.get("model_code", "")
    model_info = get_model_info(model_code)
    model_name = model_info.get("name", project.get("model_name", model_code))
    n          = max(1, int(num_systems))
    curr       = project.get("currency", "PLN")

    list_hw   = project.get("list_price_hw",       0.0)
    list_sw   = project.get("list_price_sw",        0.0)
    list_sup  = project.get("list_price_support",   0.0)
    list_svc  = project.get("list_price_services",  0.0)
    ship      = project.get("shipping",             0.0)
    d         = discount_pct / 100
    net_tot   = (list_hw + list_sw + list_sup + list_svc) * (1 - d) * n + ship * n
    list_tot  = (list_hw + list_sw + list_sup + list_svc + ship) * n

    cores     = project.get("total_cores_activated", project.get("physical_cores", 0))
    mem_tb    = project.get("memory_tb", 0.0)
    fc_ports  = project.get("fc_ports", 0)
    sap_hana  = project.get("sap_hana", False)
    sup_info  = project.get("support_info") or {}
    sup_name  = sup_info.get("name", "IBM Expert Care")
    sup_years = sup_info.get("years", 5)
    labs      = project.get("expert_labs", False)

    # Auto-build opportunity context if blank
    if not opportunity_context:
        _sap_str  = ", SAP HANA TDI certified" if sap_hana else ""
        _labs_str = ", IBM Expert Labs onsite deployment included" if labs else ""
        opportunity_context = (
            f"The customer requires an enterprise IBM Power11 server for mission-critical "
            f"{'SAP HANA and ' if sap_hana else ''}compute workloads. "
            f"The proposed configuration is {model_name} — {cores} activated processor cores, "
            f"{mem_tb:.1f} TB DDR5 memory{_sap_str}, {fc_ports} × 32 Gb FC ports{_labs_str}. "
            f"Support: {sup_name} ({sup_years} years)."
            + (f" {n} × systems required." if n > 1 else "")
        )

    # Auto-build pricing justification if blank
    if not business_justification:
        dev     = discount_pct - 60.0
        dev_str = (
            f"a {dev:.1f}-point deviation above the standard 60% baseline"
            if dev > 0 else "within the standard 60% baseline"
        )
        _sys_str = f" for {n} × {model_name}" if n > 1 else ""
        _power_diff = (
            "IBM Power11 differentiates through: (1) on-chip Matrix Math Accelerator (MMA) "
            "for AI inferencing without additional GPU cost; "
            "(2) SAP HANA TDI certification with the largest certified memory per socket; "
            "(3) PowerVM enterprise hypervisor with sub-second LPAR failover; "
            "(4) end-to-end hardware memory encryption at DDIMM level — "
            "capabilities unavailable on x86 alternative platforms."
            if sap_hana else
            "IBM Power11 differentiates through: (1) on-chip Matrix Math Accelerator (MMA) "
            "for AI inferencing without additional GPU cost; "
            "(2) PowerVM enterprise hypervisor with live partition mobility and sub-second failover; "
            "(3) hardware memory encryption at DDIMM level; "
            "(4) native AIX + Linux multi-OS support in a single frame — "
            "key advantages over competing x86 and alternative RISC platforms."
        )
        business_justification = (
            f"To win this Power11 server opportunity on a price-performance basis, "
            f"IBM must achieve a net price of {net_tot:,.0f} {curr}{_sys_str} "
            f"(IBM list: {list_tot:,.0f} {curr}), requiring a {discount_pct:.1f}% discount — {dev_str}. "
            f"The enterprise server market is highly competitive; HPE Superdome Flex, "
            f"Dell PowerEdge (x86 alternative), and Oracle SPARC/x86 platforms are expected "
            f"to be priced aggressively in this evaluation. "
            f"The requested discount level is required to meet the customer's budget "
            f"and reflect IBM's competitive positioning in the RISC/Power segment. "
            f"{_power_diff} "
            f"[Add specific competitor pricing intelligence here.]"
        )

    return generate_special_bid(
        project=project,
        client_name=client_name,
        seller_name=seller_name,
        distributor_name=distributor_name,
        reseller_name=reseller_name,
        discount_pct=discount_pct,
        eu_margin_pct=eu_margin_pct,
        opportunity_context=opportunity_context,
        deal_background=deal_background,
        competitor_info=competitor_info,
        deal_history=deal_history,
        business_justification=business_justification,
        extended_validity_days=extended_validity_days,
        extended_validity_reason=extended_validity_reason,
        num_systems=num_systems,
    )
