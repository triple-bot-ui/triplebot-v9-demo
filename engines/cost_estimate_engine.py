# ============================================
# TRIPLE BOT V9.8
# COST ESTIMATE ENGINE
# MULTI-REGION SUPPORT: TH / CN / US
# ============================================

REGION_RATES = {
    "Thailand": {
        "currency":          "THB",
        "symbol":            "฿",
        "concrete":          2500.0,   # THB/m³
        "excavation":        350.0,    # THB/m³
        "reinforcement":     25.0,     # THB/kg
        "column_upgrade":    10.0,     # THB/kN
    },
    "China": {
        "currency":          "CNY",
        "symbol":            "¥",
        "concrete":          450.0,    # CNY/m³
        "excavation":        80.0,     # CNY/m³
        "reinforcement":     6.0,      # CNY/kg
        "column_upgrade":    2.0,      # CNY/kN
    },
    "United States": {
        "currency":          "USD",
        "symbol":            "$",
        "concrete":          180.0,    # USD/m³
        "excavation":        35.0,     # USD/m³
        "reinforcement":     2.2,      # USD/kg
        "column_upgrade":    0.8,      # USD/kN
    },
}

DEFAULT_REGION = "Thailand"


def get_region_rates(region=None):
    return REGION_RATES.get(region, REGION_RATES[DEFAULT_REGION])


def generate_cost_estimate(boq, region=None):
    """
    Generate preliminary cost estimate from BOQ.
    Uses region-specific benchmark rates.
    Deterministic — no live market data.
    """
    rates    = get_region_rates(region)
    currency = rates["currency"]
    symbol   = rates["symbol"]

    concrete_volume   = float(boq.get("concrete_volume_m3", 0.0))
    excavation_volume = float(boq.get("excavation_volume_m3", 0.0))
    reinforcement_kg  = float(boq.get("reinforcement_estimate", 0.0))

    concrete_cost     = concrete_volume   * rates["concrete"]
    excavation_cost   = excavation_volume * rates["excavation"]
    reinforcement_cost = reinforcement_kg * rates["reinforcement"]
    total_cost        = concrete_cost + excavation_cost + reinforcement_cost

    return {
        "region":                       region or DEFAULT_REGION,
        "currency":                     currency,
        "symbol":                       symbol,

        # Rates
        "concrete_rate_thb_per_m3":     round(rates["concrete"], 2),
        "excavation_rate_thb_per_m3":   round(rates["excavation"], 2),
        "reinforcement_rate_thb_per_kg": round(rates["reinforcement"], 2),
        "column_upgrade_rate_thb_per_kn": round(rates["column_upgrade"], 2),

        # Costs
        "concrete_cost_thb":            round(concrete_cost, 2),
        "excavation_cost_thb":          round(excavation_cost, 2),
        "reinforcement_cost_thb":       round(reinforcement_cost, 2),
        "total_cost_thb":               round(total_cost, 2),
    }
