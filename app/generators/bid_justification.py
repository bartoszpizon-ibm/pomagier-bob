"""
Business Justification generator.

Two modes:
  1. Ollama (local LLM, http://localhost:11434) — if available and a model is loaded
  2. Static f-string template — always works, zero dependencies
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any

_OLLAMA_BASE = "http://localhost:11434"
_PREFERRED_MODELS = ["mistral", "llama3", "llama3.2", "llama2", "phi3", "gemma2"]


# ── Ollama helpers ────────────────────────────────────────────────────────────

def ollama_status() -> dict[str, Any]:
    """Return {"available": bool, "model": str | None, "models": list[str]}."""
    try:
        req = urllib.request.Request(f"{_OLLAMA_BASE}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
        models = [m["name"].split(":")[0] for m in data.get("models", [])]
        chosen = next((m for m in _PREFERRED_MODELS if m in models), None)
        if chosen is None and models:
            chosen = models[0]
        return {"available": bool(chosen), "model": chosen, "models": models}
    except Exception:
        return {"available": False, "model": None, "models": []}


def _ollama_generate(model: str, prompt: str, timeout: int = 90) -> str:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.55,   # enough variation for Regenerate, not too random
            "num_predict": 220,    # ~2 sentences max
            "top_p": 0.85,
        },
    }).encode()
    req = urllib.request.Request(
        f"{_OLLAMA_BASE}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    return data.get("response", "").strip()


# ── Prompt builder (few-shot) ─────────────────────────────────────────────────

_FEW_SHOT_EN = """
EXAMPLE 1 — Private sector, new customer, single SBO, competitor Dell EMC, budget 800k EUR:
BITE is one of the 3 largest telcos in the Baltics and is looking to procure storage for internal use; it is critical we provide the best price possible as additional purchases of 200–300k EUR are planned later this year. We unfortunately lost this client to Hitachi last year, so aggressive pricing is required to re-establish IBM's position and prevent a repeated loss.

EXAMPLE 2 — Public sector, new customer, single SBO, competitors Dell EMC and NetApp, budget 250k EUR:
Riga Technical University has issued a formal public-sector RFP; as a publicly funded institution, all bids are subject to strict budget caps and full procurement transparency, and the target price of approximately 250k EUR excluding VAT is non-negotiable. This is a highly competitive opportunity where Dell EMC and NetApp are bidding aggressively, and winning it would mark the first IBM ESS installation in the Baltics — follow-on expansion projects will go to the incumbent by default.

EXAMPLE 3 — Private sector, existing customer, multiple SBO, competitor Dell PowerScale, budget 400k EUR:
The customer is an existing IBM account that is now evaluating Dell PowerScale as an alternative — Dell has submitted pricing close to the customer's confirmed budget of 400k EUR and is actively trying to displace IBM in this account. Exception pricing is required to retain the existing IBM footprint, match the competitive price point, and prevent Dell from gaining their first installation at this customer.

EXAMPLE 4 — Private sector, new customer, single SBO, competitors Dell PowerScale and Hitachi, strategic account:
Giraffe360 is a high-growth data-intensive customer with confirmed expansion plans and a strategy to repatriate workloads from cloud to on-premises IBM ESS3500; this is a net-new IBM deployment with no existing IBM footprint, and given strong competitive pressure from Dell PowerScale and Hitachi, exceptional pricing is required to secure the initial installation and block competitor entry. The customer's budget is approximately 800k EUR and this deal is the foundation for significant follow-on revenue at improved margins.

EXAMPLE 5 — Public sector, existing customer, single SBO, competitor HPE, budget 180k EUR:
The customer is a government agency and an existing IBM storage account; HPE has submitted a competing proposal priced aggressively at levels close to the confirmed public procurement budget of 180k EUR, and is actively working to replace the IBM infrastructure. As a public-sector entity, the tender is legally binding and price is the primary evaluation criterion — the requested discount is required to retain the IBM position and prevent HPE from displacing us in this account.
"""

_FEW_SHOT_PL = """
PRZYKŁAD 1 — Sektor prywatny, nowy klient, pojedyncze SBO, konkurent Dell EMC, budżet 800k EUR:
BITE jest jednym z 3 największych operatorów telekomunikacyjnych w krajach bałtyckich i planuje zakup macierzy do użytku wewnętrznego; kluczowe jest zaoferowanie najlepszej możliwej ceny, ponieważ w bieżącym roku planowane są kolejne zakupy w wysokości 200–300k EUR. Ubiegłego roku przegraliśmy z Hitachi, dlatego agresywne warunki cenowe są niezbędne do odbudowania pozycji IBM.

PRZYKŁAD 2 — Sektor publiczny, nowy klient, pojedyncze SBO, konkurenci Dell EMC i NetApp, budżet 250k EUR:
Ryski Uniwersytet Techniczny ogłosił przetarg publiczny; jako jednostka finansowana ze środków publicznych, wszystkie oferty podlegają ścisłym limitom budżetowym i pełnej transparentności procesu zamówień, a docelowa cena ok. 250k EUR netto jest nieprzekraczalna. Dell EMC i NetApp składają agresywne oferty bliskie temu poziomowi, a wygranie tego przetargu oznaczałoby pierwszą instalację IBM ESS w krajach bałtyckich.

PRZYKŁAD 3 — Sektor prywatny, istniejący klient, wielokrotne SBO, konkurent Dell PowerScale, budżet 400k EUR:
Klient jest istniejącym kontem IBM, które rozważa teraz Dell PowerScale jako alternatywę — Dell złożył ofertę bliską potwierdzonemu budżetowi klienta w wysokości 400k EUR i aktywnie stara się wyprzeć IBM z tego konta. Wyjątkowe warunki cenowe są niezbędne do utrzymania istniejącej instalacji IBM, dopasowania się do konkurencyjnego poziomu cenowego i uniemożliwienia Dellowi zdobycia pierwszej instalacji u tego klienta.
"""


def _build_prompt(
    bid_data: dict[str, Any],
    client_type: str,
    competitors: list[str],
    extra_notes: str,
    lang: str,
    sbo_type: str,
    cust_status: str,
    bid_validity_days: int = 0,
    bid_validity_reason: str = "",
) -> str:
    client     = bid_data.get("client_name") or "[Client]"
    model_name = bid_data.get("model_name")  or "IBM Storage"
    curr       = bid_data.get("currency", "EUR")
    net        = bid_data.get("net_price", 0.0)
    list_p     = bid_data.get("list_price", 0.0)
    disc       = bid_data.get("discount_pct", 0.0)
    opp_ctx    = (bid_data.get("opportunity_context") or "")[:300]
    comp_str   = ", ".join(competitors) if competitors else "key competing vendors"
    sector     = "public sector" if client_type == "public" else "private sector"
    extra      = extra_notes.strip() if extra_notes else ""
    few_shot   = _FEW_SHOT_PL if lang == "pl" else _FEW_SHOT_EN
    lang_instr = (
        "Write in Polish. Use direct, professional language — no marketing fluff."
        if lang == "pl" else
        "Write in English. Use direct, professional language — no marketing fluff."
    )

    is_new_cust  = "new" in cust_status.lower()
    is_pub_sect  = client_type == "public"
    is_extended  = bid_validity_days > 30

    # Context hints injected into the prompt so the model uses them explicitly
    pub_hint = (
        "IMPORTANT: This is a PUBLIC SECTOR customer — mention that it is a public tender/procurement, "
        "that budget caps are legally binding and price is the primary evaluation criterion."
        if is_pub_sect else ""
    )
    new_hint = (
        "IMPORTANT: This is a NEW customer with NO existing IBM footprint — "
        "mention this is a net-new IBM deployment and that winning secures the initial IBM installation."
        if is_new_cust else
        "IMPORTANT: This is an EXISTING IBM customer — mention that a competitor (name them) is already "
        "present or is actively bidding with prices close to the customer's budget, trying to displace IBM. "
        "Emphasise that exception pricing is required to RETAIN the existing IBM account."
    )
    validity_hint = (
        f"IMPORTANT: The bid validity requested is {bid_validity_days} days (extended beyond the standard "
        f"30-day period). Mention this in the justification and briefly explain the reason: "
        f"{bid_validity_reason if bid_validity_reason else 'extended procurement / approval cycle'}."
        if is_extended else ""
    )

    return f"""You are writing a Business Justification for an IBM Hardware Special Bid pricing request.
The text must be EXACTLY 2 sentences. No bullet points, no headers, no greeting.
Style: direct, factual, operational — like the examples below. Include specific numbers (budget, price, %).
{lang_instr}

--- STYLE EXAMPLES ---
{few_shot}
--- END EXAMPLES ---

Now write a NEW Business Justification for this deal:
- Customer: {client} ({sector}, {cust_status.lower()})
- Product: {model_name}
- List price: {list_p:,.0f} {curr} | Requested BP price: {net:,.0f} {curr} | Discount: {disc:.1f}%
- SBO type: {sbo_type}
- Competitors: {comp_str}
{f'- Opportunity context: {opp_ctx}' if opp_ctx else ''}
{f'- Additional context: {extra}' if extra else ''}
{pub_hint}
{new_hint}
{validity_hint}

Business Justification (2 sentences only, no labels):"""


# ── Static fallback ───────────────────────────────────────────────────────────

def _static_bj(
    bid_data: dict[str, Any],
    client_type: str,
    competitors: list[str],
    extra_notes: str,
    lang: str,
    sbo_type: str,
    cust_status: str,
    bid_validity_days: int = 0,
    bid_validity_reason: str = "",
) -> str:
    client     = bid_data.get("client_name") or "[Client]"
    model_name = bid_data.get("model_name")  or "IBM Storage"
    curr       = bid_data.get("currency", "EUR")
    net        = bid_data.get("net_price", 0.0)
    list_p     = bid_data.get("list_price", 0.0)
    disc       = bid_data.get("discount_pct", 0.0)
    dev        = disc - 60.0
    dev_str    = (f"{dev:.1f} pp above the standard 60% baseline"
                  if dev > 0 else "within the standard 60% baseline")
    comp_str   = ", ".join(competitors) if competitors else "key competitors"
    extra_sent = f" {extra_notes.strip()}" if extra_notes and extra_notes.strip() else ""
    is_pub     = client_type == "public"
    is_new     = "new" in cust_status.lower()
    is_multi   = sbo_type.lower() == "multiple"

    is_extended = bid_validity_days > 30
    multi_str  = " This is a multiple-SBO deal with strong follow-on potential." if is_multi else ""
    multi_pl   = " Jest to deal wielokrotnego SBO z potencjałem dalszych zamówień." if is_multi else ""

    _vr = bid_validity_reason if bid_validity_reason else "extended procurement cycle"
    validity_str = (
        f" Extended bid validity of {bid_validity_days} days has been requested due to: {_vr}."
        if is_extended else ""
    )
    validity_pl = (
        f" Wnioskowany termin ważności oferty wynosi {bid_validity_days} dni z uwagi na: {_vr}."
        if is_extended else ""
    )

    if is_pub:
        sector_str = "public-sector tender"
        pub_note   = (
            " As a publicly funded institution, this procurement is subject to strict budget caps "
            "and full transparency requirements — price is the primary evaluation criterion."
        )
        pub_pl     = (
            " Jako jednostka sektora publicznego, zamówienie podlega ścisłym limitom budżetowym "
            "i wymogom transparentności — cena jest głównym kryterium oceny ofert."
        )
    else:
        sector_str = "competitive RFP"
        pub_note   = ""
        pub_pl     = ""

    if is_new:
        new_str = "establish the initial IBM footprint at this customer"
        new_pl  = "zdobycie pierwszej instalacji IBM u tego klienta"
        cust_note  = ""
        cust_pl    = ""
    else:
        new_str = "retain the existing IBM account"
        new_pl  = "utrzymanie istniejącej instalacji IBM"
        cust_note  = (
            f" {comp_str} {'is' if len(competitors) == 1 else 'are'} already present at this account "
            f"and {'has' if len(competitors) == 1 else 'have'} submitted pricing aggressively close to "
            f"the customer's confirmed budget, actively trying to displace IBM."
        )
        cust_pl    = (
            f" {comp_str} {'jest' if len(competitors) == 1 else 'są'} już obecny/-i u tego klienta "
            f"i {'złożył' if len(competitors) == 1 else 'złożyli'} agresywną ofertę bliską "
            f"potwierdzonemu budżetowi, próbując wyprzeć IBM."
        )

    if lang == "pl":
        is_pub_pl_label = "przetarg publiczny" if is_pub else "konkurencyjny przetarg"
        return (
            f"{client} prowadzi {is_pub_pl_label} na dostawę {model_name}; "
            f"wymagana cena BP {net:,.0f} {curr} (lista: {list_p:,.0f} {curr}, upust {disc:.1f}% — {dev_str}) "
            f"jest niezbędna, aby zmieścić się w budżecie klienta i wyprzedzić {comp_str}.{pub_pl}{cust_pl}"
            f" Wyjątkowe warunki cenowe są konieczne do {new_pl} i zablokowania wejścia konkurencji."
            f"{multi_pl}{validity_pl}{extra_sent}"
        )

    return (
        f"{client} is running a {sector_str} for {model_name}; the requested BP price of "
        f"{net:,.0f} {curr} (list: {list_p:,.0f} {curr}, {disc:.1f}% discount — {dev_str}) "
        f"is required to fit within the customer's budget and stay ahead of {comp_str}.{pub_note}{cust_note}"
        f" Exceptional pricing support is necessary to {new_str} and prevent competitor entry."
        f"{multi_str}{validity_str}{extra_sent}"
    )


# ── Public entry point ────────────────────────────────────────────────────────

def generate_bj(
    bid_data: dict[str, Any],
    client_type: str = "private",
    competitors: list[str] | None = None,
    extra_notes: str = "",
    lang: str = "en",
    force_static: bool = False,
    sbo_type: str = "Single",
    cust_status: str = "New customer",
    bid_validity_days: int = 0,
    bid_validity_reason: str = "",
) -> tuple[str, str]:
    """
    Generate a Business Justification text.
    Returns (bj_text, source) where source is "ollama:<model>" or "static".
    """
    if competitors is None:
        competitors = []

    if not force_static:
        status = ollama_status()
        if status["available"] and status["model"]:
            try:
                prompt = _build_prompt(
                    bid_data, client_type, competitors, extra_notes,
                    lang, sbo_type, cust_status,
                    bid_validity_days=bid_validity_days,
                    bid_validity_reason=bid_validity_reason,
                )
                text = _ollama_generate(status["model"], prompt)
                if text:
                    return text, f"ollama:{status['model']}"
            except Exception:
                pass  # fall through to static

    text = _static_bj(
        bid_data, client_type, competitors, extra_notes,
        lang, sbo_type, cust_status,
        bid_validity_days=bid_validity_days,
        bid_validity_reason=bid_validity_reason,
    )
    return text, "static"
