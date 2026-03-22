# ============================================
# TRIPLE BOT V5
# Design Solver Engine
# ============================================

# BUG FIX: file was a bare script with no function definition,
# no import math, and a bare `return` statement outside any function.
# Wrapped into a proper function.

import math


def run_design_solver(
    total_load,
    column_capacity,
    soil_capacity,
    foundation_area,
    target_utilization=0.8
):

    # BUG FIX: guard division by zero
    if column_capacity == 0:
        column_utilization = float("inf")
    else:
        column_utilization = total_load / column_capacity

    if soil_capacity == 0 or foundation_area == 0:
        soil_utilization = float("inf")
    else:
        soil_utilization = total_load / (soil_capacity * foundation_area)

    result = {}

    if column_utilization <= 1 and soil_utilization <= 1:

        result["status"] = "SAFE"
        result["recommendation"] = "Design already safe. Optimization possible."

    else:

        result["status"] = "FAIL"
        fixes = []

        if target_utilization == 0:
            required_column_capacity = float("inf")
        else:
            required_column_capacity = total_load / target_utilization

        fixes.append({
            "type": "column",
            "recommended_capacity": round(required_column_capacity, 2)
        })

        if soil_capacity == 0 or target_utilization == 0:
            required_area = float("inf")
            side = float("inf")
        else:
            required_area = total_load / (soil_capacity * target_utilization)
            side = math.sqrt(required_area)

        fixes.append({
            "type": "foundation",
            "recommended_size": round(side, 2)
        })

        result["fix_options"] = fixes

    return result
