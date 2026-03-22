# ============================================
# TRIPLE BOT V8
# ENGINE 2 — OPTION RANKING ENGINE
# Deterministic Engineering Decision Ranking
# ============================================

# BUG FIX: engineering_constants_v8.py does not exist in the project.
# Constants are now defined inline to prevent ImportError crash.
FOUNDATION_COST_WEIGHT = 1.0
COLUMN_COST_WEIGHT = 1.0
LOAD_REDUCTION_PENALTY = 1.0
TARGET_UTILIZATION = 0.8


def calculate_option_score(option):

    option_type = option.get("option_type")

    score = 0

    # ----------------------------------------
    # FOUNDATION OPTION
    # ----------------------------------------

    if option_type == "FOUNDATION_INCREASE":

        foundation_size = option.get("foundation_size", 0)
        soil_utilization = option.get("soil_utilization", 1)

        foundation_cost = foundation_size * FOUNDATION_COST_WEIGHT

        utilization_penalty = abs(TARGET_UTILIZATION - soil_utilization)

        score = foundation_cost + utilization_penalty

    # ----------------------------------------
    # COLUMN OPTION
    # ----------------------------------------

    elif option_type == "COLUMN_UPGRADE":

        column_capacity = option.get("column_capacity", 0)
        column_utilization = option.get("column_utilization", 1)

        column_cost = column_capacity * 0.01 * COLUMN_COST_WEIGHT

        utilization_penalty = abs(TARGET_UTILIZATION - column_utilization)

        score = column_cost + utilization_penalty

    # ----------------------------------------
    # LOAD REDUCTION OPTION
    # ----------------------------------------

    elif option_type == "LOAD_REDUCTION":

        load_reduction = option.get("load_reduction", 0)

        score = load_reduction * 10 * LOAD_REDUCTION_PENALTY

    else:

        score = 999

    return round(score, 3)


def rank_engineering_options(options):

    ranked_options = []

    for option in options:

        score = calculate_option_score(option)

        option_with_score = option.copy()

        option_with_score["decision_score"] = score

        ranked_options.append(option_with_score)

    ranked_options = sorted(
        ranked_options,
        key=lambda x: x["decision_score"]
    )

    return ranked_options
