"""
Reusable tools for agents. Two kinds:

  - SCHEMAS: JSON tool definitions the LLM sees.
  - IMPLS  : deterministic Python functions (calculators). They compute from the
             ARGUMENTS the model passes — they do NOT hardcode any restaurant data.

Inject your app-specific tools (web_search, POS lookups, DB queries) at runtime.
"""

# ----------------------- schemas -----------------------
WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the live web for current, specific, real facts (competitors, hours, prices, reviews, events, suppliers, regulations).",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    },
}

PRIME_COST_SCHEMA = {
    "type": "function",
    "function": {
        "name": "prime_cost",
        "description": "Compute prime cost % (food+bev cost + labor cost) / sales, with a health benchmark.",
        "parameters": {
            "type": "object",
            "properties": {
                "monthly_sales": {"type": "number"},
                "food_cost": {"type": "number"},
                "labor_cost": {"type": "number"},
            },
            "required": ["monthly_sales", "food_cost", "labor_cost"],
        },
    },
}

FOOD_COST_SCHEMA = {
    "type": "function",
    "function": {
        "name": "food_cost_pct",
        "description": "Compute a single item's food-cost % and gross margin from its plate cost and menu price.",
        "parameters": {
            "type": "object",
            "properties": {"item_cost": {"type": "number"}, "menu_price": {"type": "number"}},
            "required": ["item_cost", "menu_price"],
        },
    },
}

BREAK_EVEN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "break_even",
        "description": "Compute break-even covers/month from fixed costs, average check, and variable cost per cover.",
        "parameters": {
            "type": "object",
            "properties": {
                "fixed_costs": {"type": "number"},
                "avg_check": {"type": "number"},
                "variable_cost_per_cover": {"type": "number"},
            },
            "required": ["fixed_costs", "avg_check", "variable_cost_per_cover"],
        },
    },
}


# ----------------------- impls -----------------------
async def prime_cost(monthly_sales: float, food_cost: float, labor_cost: float):
    s = float(monthly_sales) or 1.0
    fp, lp = food_cost / s * 100, labor_cost / s * 100
    prime = fp + lp
    verdict = ("healthy (<=60%)" if prime <= 60 else "watch (60-65%)" if prime <= 65 else "too high (>65%)")
    return {"prime_cost_pct": round(prime, 1), "food_pct": round(fp, 1),
            "labor_pct": round(lp, 1), "benchmark": "target <= 60%", "verdict": verdict}


async def food_cost_pct(item_cost: float, menu_price: float):
    p = float(menu_price) or 1.0
    fc = item_cost / p * 100
    verdict = ("great (<=28%)" if fc <= 28 else "ok (28-35%)" if fc <= 35 else "high (>35%)")
    return {"food_cost_pct": round(fc, 1), "gross_margin": round(p - item_cost, 2),
            "benchmark": "target 28-35%", "verdict": verdict}


async def break_even(fixed_costs: float, avg_check: float, variable_cost_per_cover: float):
    contribution = float(avg_check) - float(variable_cost_per_cover)
    if contribution <= 0:
        return {"error": "avg_check must exceed variable cost per cover"}
    covers = fixed_costs / contribution
    return {"break_even_covers_month": round(covers),
            "break_even_covers_day": round(covers / 30, 1),
            "contribution_margin_per_cover": round(contribution, 2)}


DEFAULT_CALC_IMPLS = {
    "prime_cost": prime_cost,
    "food_cost_pct": food_cost_pct,
    "break_even": break_even,
}
