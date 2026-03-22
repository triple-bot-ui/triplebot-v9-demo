# ============================================
# TRIPLE BOT V5
# Engineering Risk Indicator
# ============================================

def evaluate_engineering_risk(structural_result):

    soil_util = structural_result["soil_utilization"]
    column_util = structural_result["column_utilization"]

    governing_util = max(soil_util, column_util)

    if governing_util < 0.70:
        risk_level = "SAFE"
        message = "Structure well within safe engineering limits."

    elif governing_util < 0.90:
        risk_level = "CAUTION"
        message = "Structure approaching design limits. Monitor closely."

    elif governing_util < 1.00:
        risk_level = "CRITICAL"
        message = "Structure at critical utilization. Minimal safety margin."

    else:
        risk_level = "FAIL"
        message = "Structural capacity exceeded. Redesign required."

    return {
        "risk_level": risk_level,
        "risk_message": message,
        "governing_utilization": round(governing_util, 3)
    }