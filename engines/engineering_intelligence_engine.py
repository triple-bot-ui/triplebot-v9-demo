# ============================================
# TRIPLE BOT V5
# Engineering Intelligence Engine
# ============================================

def generate_engineering_intelligence(structural_validation):

    column_util = structural_validation.get("column_utilization", 0)
    soil_util = structural_validation.get("soil_utilization", 0)

    column_margin = structural_validation.get("column_margin", 0)
    soil_margin = structural_validation.get("soil_margin", 0)

    governing_mode = structural_validation.get("governing_mode", "UNKNOWN")

    utilization = max(column_util, soil_util)

    # ------------------------------------------------
    # Structural Risk Level
    # ------------------------------------------------
    if utilization < 0.5:
        risk_level = "LOW"

    elif utilization < 0.8:
        risk_level = "MODERATE"

    elif utilization <= 1.0:
        risk_level = "HIGH"

    else:
        risk_level = "CRITICAL"

    # ------------------------------------------------
    # Structural Reserve Interpretation
    # ------------------------------------------------
    if utilization < 0.5:
        reserve_comment = "Large structural reserve detected."

    elif utilization < 0.8:
        reserve_comment = "Adequate structural reserve available."

    elif utilization <= 1.0:
        reserve_comment = "Structural capacity fully utilized."

    else:
        reserve_comment = "Structural capacity exceeded."

    # ------------------------------------------------
    # Governing Behavior
    # ------------------------------------------------
    if governing_mode == "SOIL":
        governing_comment = "Soil capacity governs the structural behavior."

    elif governing_mode == "COLUMN":
        governing_comment = "Column capacity governs the structural behavior."

    else:
        governing_comment = "Governing behavior could not be determined."

    # ------------------------------------------------
    # Engineering Recommendation
    # ------------------------------------------------
    if utilization < 0.5:
        recommendation = "STRUCTURE IS VERY SAFE — Foundation size can potentially be reduced."

    elif utilization < 0.8:
        recommendation = "STRUCTURE IS SAFE — Design is within normal engineering limits."

    elif utilization <= 1.0:
        recommendation = "STRUCTURE AT CAPACITY — Design is at structural limit."

    else:
        recommendation = "STRUCTURE UNSAFE — Redesign required."

    return {
        "recommendation": recommendation,
        "risk_level": risk_level,
        "governing_behavior": governing_comment,
        "structural_reserve": reserve_comment
    }