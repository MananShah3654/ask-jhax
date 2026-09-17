"""
360-degree restaurant-COO specialist roster.

Nothing is hardcoded: each agent is a role PROMPT + a set of injected TOOLS.
The specific restaurant's data arrives at runtime via memory/RAG context, so the
same roster works for ANY restaurant.

Usage:
    from ai_core.rosters import restaurant_coo_roster
    roster = restaurant_coo_roster(web_search=my_search_fn)   # inject your live search
    coo = COO(roster, memory=..., cache=..., rag=..., rag_namespace=...)

`web_search` = your async fn (query:str)->dict. If omitted, search-dependent
agents still run but are told search is unavailable (they'll reason + flag gaps).
"""
from .config import Config
from .agents import Agent
from .tools import (
    WEB_SEARCH_SCHEMA, PRIME_COST_SCHEMA, FOOD_COST_SCHEMA, BREAK_EVEN_SCHEMA,
    DEFAULT_CALC_IMPLS,
)

_BASE = (
    "You are a specialist advisor on a restaurant operator's virtual leadership team, "
    "led by an AI COO. You are commercially sharp, direct, and honest — never sycophantic. "
    "Use the provided restaurant context; if a fact is missing, use your tools or say so plainly. "
    "Always finish with concrete, this-week execution steps. Keep it scannable."
)


def _spec(role: str) -> str:
    return f"{_BASE}\n\nYOUR SPECIALTY: {role}"


def restaurant_coo_roster(web_search=None, strong_model=None, extra: dict = None):
    model = strong_model or Config.strong()

    if web_search is None:
        from .search import gemini_web_search  # default: live Gemini Google Search (like jhax)
        web_search = gemini_web_search

    search_impl = web_search
    search_tools = [WEB_SEARCH_SCHEMA]
    search_impls = {"web_search": search_impl}

    def A(name, desc, role, tools=None, impls=None):
        return Agent(name, desc, _spec(role), model=model,
                     tools=tools or [], tool_impls=impls or {})

    roster = {
        # --- MARKET & GROWTH ---
        "competitor_intel": A(
            "competitor_intel",
            "Real nearby competitors, their positioning, pricing, ratings, promos, and how to win vs each.",
            "Competitive intelligence & market positioning.",
            search_tools, search_impls),
        "local_demand": A(
            "local_demand",
            "Local events, holidays, weather, sports, seasonality and demand forecasting for the next 1-8 weeks.",
            "Local demand, events & seasonality — surface tie-in plays.",
            search_tools, search_impls),
        "growth_expansion": A(
            "growth_expansion",
            "Second location, franchising, catering, ghost kitchens, new dayparts — trade-offs and readiness.",
            "Growth, expansion & new revenue lines. Give real trade-offs, not cheerleading.",
            search_tools, search_impls),

        # --- MONEY ---
        "finance_pnl": A(
            "finance_pnl",
            "P&L, prime cost, break-even, cash flow, margins, budgeting — the numbers.",
            "Restaurant finance & unit economics. Use calculators; show the math.",
            [PRIME_COST_SCHEMA, BREAK_EVEN_SCHEMA], dict(DEFAULT_CALC_IMPLS)),
        "pricing_menu": A(
            "pricing_menu",
            "Menu engineering (Star/Plowhorse/Puzzle/Dog), re-pricing, plate cost, menu design/psychology.",
            "Menu engineering & pricing strategy. Use food-cost math.",
            [FOOD_COST_SCHEMA], {"food_cost_pct": DEFAULT_CALC_IMPLS["food_cost_pct"]}),
        "purchasing_inventory": A(
            "purchasing_inventory",
            "Supplier negotiation, food-cost control, inventory/par levels, waste, shrinkage, spec sheets.",
            "Purchasing, inventory & food-cost control.",
            search_tools, search_impls),

        # --- PEOPLE ---
        "labor_staffing": A(
            "labor_staffing",
            "Scheduling, labor cost %, hiring, retention, tips/pay structures, training, culture.",
            "Labor, staffing & people ops. Balance service quality vs labor cost.",
            [PRIME_COST_SCHEMA], {"prime_cost": DEFAULT_CALC_IMPLS["prime_cost"]}),

        # --- OPERATIONS & GUEST ---
        "operations": A(
            "operations",
            "Service speed, throughput, table turns, kitchen flow, ticket times, SOPs, bottlenecks.",
            "Operations & throughput. Diagnose bottlenecks, give measurable fixes.",
            search_tools, search_impls),
        "guest_experience": A(
            "guest_experience",
            "Loyalty, CRM, repeat visits, reservations, hospitality standards, complaints recovery.",
            "Guest experience, loyalty & retention.",
            search_tools, search_impls),
        "reviews_reputation": A(
            "reviews_reputation",
            "Review sentiment themes, responding to reviews, ratings recovery, online reputation.",
            "Reviews & reputation management. Draft real, gracious review replies when asked.",
            search_tools, search_impls),

        # --- REVENUE CHANNELS ---
        "marketing_content": A(
            "marketing_content",
            "Social content, campaigns, promos, email/WhatsApp broadcasts, ready-to-use copy.",
            "Marketing & content. Output copy-paste-ready drafts, not descriptions.",
            search_tools, search_impls),
        "delivery_offpremise": A(
            "delivery_offpremise",
            "DoorDash/UberEats/Grubhub economics, commissions, delivery menu, packaging, first-party ordering.",
            "Delivery & off-premise strategy. Watch the commission math.",
            search_tools, search_impls),
        "events_catering": A(
            "events_catering",
            "Private events, catering packages, group bookings, event pricing and upsells.",
            "Events & catering revenue.",
            search_tools, search_impls),

        # --- RISK & FUTURE ---
        "compliance_safety": A(
            "compliance_safety",
            "Food safety, health-code readiness, licensing pointers, insurance basics (GENERAL guidance only).",
            "Compliance & safety — give general pointers and ALWAYS recommend a licensed professional for legal/tax/health filings.",
            search_tools, search_impls),
        "tech_automation": A(
            "tech_automation",
            "POS, KDS, online ordering, reservations, loyalty tech, automation, data/reporting stack.",
            "Restaurant technology & automation. Recommend practical, ROI-positive tools.",
            search_tools, search_impls),
        "crisis_pr": A(
            "crisis_pr",
            "Bad viral reviews, PR incidents, closures, refunds, staff issues — rapid response playbooks.",
            "Crisis & PR response. Calm, fast, specific. Draft public statements when asked.",
            search_tools, search_impls),
    }

    if extra:
        roster.update(extra)
    return roster
