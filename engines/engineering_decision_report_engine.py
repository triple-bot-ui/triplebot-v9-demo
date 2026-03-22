# ============================================
# ENGINEERING DECISION ENGINE V8
# ============================================

# BUG FIX: added `result` parameter to match how this function is called
# in triplebot_v5_ui.py: generate_engineering_decision(ranked_options, result)
def generate_engineering_decision(ranked_options, result=None):

    decision = {}

    # ไม่มี option
    if not ranked_options:
        decision["best_option"] = None
        decision["summary_action"] = "No optimization required."
        decision["decision_status"] = "NO_OPTIONS_AVAILABLE"
        return decision

    best = ranked_options[0]

    decision["best_option"] = best
    decision["decision_status"] = "OPTION_SELECTED"

    option_type = best.get("option_type")

    # ============================================
    # LOAD REDUCTION
    # ============================================

    if option_type == "LOAD_REDUCTION":

        reduction = best.get("load_reduction", 0)

        decision["summary_action"] = (
            f"Optional optimization: reduce load by {reduction*100:.1f}% "
            "to increase safety margin."
        )

    # ============================================
    # FOUNDATION INCREASE
    # ============================================

    elif option_type == "FOUNDATION_INCREASE":

        size = best.get("foundation_size")

        decision["summary_action"] = (
            f"Optional optimization: increase foundation size to {size} m "
            "to improve soil utilization."
        )

    # ============================================
    # COLUMN UPGRADE
    # ============================================

    elif option_type == "COLUMN_UPGRADE":

        capacity = best.get("column_capacity")

        decision["summary_action"] = (
            f"Optional optimization: upgrade column capacity to {capacity} kN "
            "to improve structural performance."
        )

    # ============================================
    # DEFAULT
    # ============================================

    else:

        decision["summary_action"] = "No optimization required."

    return decision
