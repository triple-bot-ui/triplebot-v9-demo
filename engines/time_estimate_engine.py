# ============================================
# TRIPLE BOT V9.7
# TIME ESTIMATE ENGINE
# RULE-BASED PRELIMINARY TIME LAYER
# ============================================

def generate_time_estimate(decision, corrected_design):
    """
    Generate preliminary time estimate using simple deterministic rules.
    Output unit = days.
    """

    decision_type = decision.get("option_type") if decision else None

    foundation_size = float(corrected_design.get("foundation_width", 0.0))
    column_capacity = float(corrected_design.get("column_capacity", 0.0))

    activity = "General engineering work"
    estimated_days = 0.0
    basis = "No time rule applied."

    if decision_type == "FOUNDATION_INCREASE":

        activity = "Foundation work"

        if foundation_size <= 2.0:
            estimated_days = 1.0
            basis = "Small corrected foundation size (<= 2.0 m)."
        elif foundation_size <= 3.0:
            estimated_days = 2.0
            basis = "Medium corrected foundation size (> 2.0 m and <= 3.0 m)."
        elif foundation_size <= 5.0:
            estimated_days = 3.0
            basis = "Large corrected foundation size (> 3.0 m and <= 5.0 m)."
        else:
            estimated_days = 5.0
            basis = "Extra-large corrected foundation size (> 5.0 m)."

    elif decision_type == "COLUMN_UPGRADE":

        activity = "Column upgrade work"

        if column_capacity <= 500:
            estimated_days = 1.0
            basis = "Minor column upgrade scope (<= 500 kN)."
        elif column_capacity <= 1500:
            estimated_days = 2.0
            basis = "Standard column upgrade scope (> 500 kN and <= 1500 kN)."
        else:
            estimated_days = 3.0
            basis = "Major column upgrade scope (> 1500 kN)."

    elif decision_type == "LOAD_REDUCTION":

        activity = "Load reduction coordination"
        estimated_days = 1.0
        basis = "Administrative / coordination-based load reduction."

    return {
        "activity": activity,
        "estimated_days": round(estimated_days, 1),
        "basis": basis
    }
