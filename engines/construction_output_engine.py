# ============================================
# TRIPLE BOT V5
# Construction Output Engine
# ============================================

import math


# ============================================
# CONSTRUCTION OUTPUT GENERATOR
# ============================================

def generate_construction_output(
    total_load,
    column_capacity,
    soil_capacity,
    foundation_width,
    foundation_length,
    target_utilization=0.8
):

    foundation_area = foundation_width * foundation_length

    # --------------------------------
    # UTILIZATION CALCULATION
    # --------------------------------

    if column_capacity == 0:
        column_utilization = float("inf")
    else:
        column_utilization = total_load / column_capacity

    if soil_capacity == 0 or foundation_area == 0:
        soil_utilization = float("inf")
    else:
        soil_utilization = total_load / (soil_capacity * foundation_area)

    result = {}

    # --------------------------------
    # SAFE CASE
    # --------------------------------

    if column_utilization <= 1 and soil_utilization <= 1:

        result["status"] = "SAFE"

        result["recommendation"] = (
            "Design already structurally safe. Optimization possible."
        )

        result["utilization"] = {
            "column_utilization": round(column_utilization, 3),
            "soil_utilization": round(soil_utilization, 3)
        }

        result["optimization_target"] = {
            "target_utilization": target_utilization
        }

    # --------------------------------
    # FAIL CASE
    # --------------------------------

    else:

        result["status"] = "FAIL"

        fixes = []

        # --------------------------------
        # COLUMN FIX OPTION
        # --------------------------------

        required_column_capacity = total_load / target_utilization

        fixes.append({
            "type": "column_capacity_upgrade",
            "recommended_capacity": round(required_column_capacity, 2)
        })

        # --------------------------------
        # FOUNDATION FIX OPTION
        # --------------------------------

        if soil_capacity == 0:
            required_area = float("inf")
            recommended_side = float("inf")
        else:
            required_area = total_load / (soil_capacity * target_utilization)
            recommended_side = math.sqrt(required_area)

        fixes.append({
            "type": "foundation_resize",
            "recommended_foundation_area": round(required_area, 3),
            "recommended_square_side": round(recommended_side, 2)
        })

        result["fix_options"] = fixes

        result["utilization"] = {
            "column_utilization": round(column_utilization, 3),
            "soil_utilization": round(soil_utilization, 3)
        }

    return result