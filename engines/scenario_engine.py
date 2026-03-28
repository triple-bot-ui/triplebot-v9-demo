# ============================================
# TRIPLE BOT
# Scenario Exploration Engine
# ============================================

import pandas as pd


PASS_LIMIT = 1.010


def run_scenario_exploration(
    load_per_storey,
    number_of_storeys,
    foundation_width,
    foundation_length,
    column_capacity,
    soil_capacity
):

    # ============================================
    # Base Load
    # ============================================

    base_total_load = round(load_per_storey * number_of_storeys, 3)

    foundation_area = foundation_width * foundation_length

    # ============================================
    # Scenario Factors
    # ============================================

    scenarios = {
        "LOW_LOAD": 0.8,
        "BASE_LOAD": 1.0,
        "HIGH_LOAD": 1.2
    }

    results = []

    for name, factor in scenarios.items():

        total_load = base_total_load * factor

        # --------------------------------
        # Safe Division Protection
        # --------------------------------

        if foundation_area == 0:
            soil_pressure = float("inf")
        else:
            soil_pressure = total_load / foundation_area

        if column_capacity == 0:
            column_utilization = float("inf")
        else:
            column_utilization = total_load / column_capacity

        if soil_capacity == 0:
            soil_utilization = float("inf")
        else:
            soil_utilization = soil_pressure / soil_capacity

        utilization_ratio = max(column_utilization, soil_utilization)

        if utilization_ratio <= PASS_LIMIT:
            status = "SAFE"
        else:
            status = "FAIL"

        if soil_utilization > column_utilization:
            governing_mode = "SOIL"
        else:
            governing_mode = "COLUMN"

        results.append({
            "scenario": name,
            "total_load": round(total_load, 2),
            "column_utilization": round(column_utilization, 3),
            "soil_utilization": round(soil_utilization, 3),
            "governing_mode": governing_mode,
            "status": status
        })

    return pd.DataFrame(results)