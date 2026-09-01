"""
Special Bid generator for IBM Storage Scale System (3500 / 6000).
Reuses the same DOCX template as FlashSystem; the underlying
generate_special_bid() is template-agnostic — only the pricing and
narrative texts differ for Storage Scale.
"""
from __future__ import annotations

from typing import Any

from .special_bid_generator import generate_special_bid
from ..knowledge.product_db import get_model_info


def generate_scale_special_bid(
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
    Generate a Special Bid request DOCX for a Storage Scale opportunity.

    Auto-builds pricing justification and opportunity context with
    Scale-appropriate language if the caller leaves them blank.
    """
    model_code = project.get("model_code", "")
    model_info = get_model_info(model_code)
    model_name = model_info.get("name", model_code)
    n          = max(1, int(num_systems))
    curr       = project.get("currency", "EUR")

    list_hw  = project.get("list_price_hw",      0.0)
    list_sw  = project.get("list_price_sw",      0.0)
    list_sup = project.get("list_price_support", 0.0)
    ship     = project.get("shipping",           0.0)
    d        = discount_pct / 100
    net_tot  = (list_hw + list_sw + list_sup) * (1 - d) * n + ship * n
    list_tot = (list_hw + list_sw + list_sup + ship) * n

    num_nodes    = project.get("num_nodes",    1) or 1
    raw_tib      = project.get("raw_tib",      0.0)
    usable_tib   = project.get("usable_tib",   0.0)
    tp_mib       = project.get("perf_throughput_mib", 0.0)
    network_type = project.get("network_type", "high-speed fabric")

    # Auto-build opportunity context if blank
    if not opportunity_context:
        _tp_str = f", delivering {tp_mib:,.0f} MiB/s sequential throughput" if tp_mib else ""
        opportunity_context = (
            f"The customer requires a parallel file storage solution to support "
            f"AI training, large-scale analytics, or HPC workloads. "
            f"The proposed configuration comprises {n} × {model_name} "
            f"({num_nodes} storage node(s) per system), "
            f"providing {raw_tib:.0f} TiB raw / {usable_tib:.0f} TiB usable capacity"
            f"{_tp_str} with {network_type} connectivity."
        )

    # Auto-build pricing justification if blank
    if not business_justification:
        dev     = discount_pct - 60.0
        dev_str = (
            f"a {dev:.1f}-point deviation above the standard 60% baseline"
            if dev > 0 else "within the standard 60% baseline"
        )
        _sys_str  = f" for {n} × {model_name}" if n > 1 else ""
        _ib_n     = project.get("ib_adapters", 0)
        _ib_d     = project.get("ib_adapter_desc", "CX-7 VPI 200GbE/NDR200")
        _ib_str   = (f", high-speed fabric connectivity via {_ib_n} × {_ib_d} adapters"
                     if _ib_n else "")
        business_justification = (
            f"To win this Storage Scale opportunity on a price-performance basis, "
            f"IBM must achieve a net price of {net_tot:,.0f} {curr}{_sys_str} "
            f"(list: {list_tot:,.0f} {curr}), requiring a {discount_pct:.1f}% discount — {dev_str}. "
            f"The Storage Scale segment is highly competitive; cloud object storage and "
            f"specialist parallel file storage vendors (WEKA, VAST Data, DDN) are actively "
            f"bidding at aggressive price points. "
            f"The requested discount level is required to meet the customer's budget and remain competitive. "
            f"IBM {model_name} differentiates through: NVIDIA-Certified Storage Systems listing "
            f"(validating GPU-accelerated AI/ML readiness), GPFS-based parallel file system with "
            f"linear scalability, enterprise NVMe SSD performance{_ib_str} — "
            f"capabilities that directly address the customer's AI/HPC workload requirements. "
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
