# ============================================
# TRIPLE BOT
# Sensitivity Analysis Engine
# ============================================

import pandas as pd


def run_sensitivity_analysis(
    load_per_storey,
    number_of_storeys,
    foundation_width,
    foundation_length,
    column_capacity,
    soil_capacity
):

    base_total_load = round(load_per_storey * number_of_storeys, 3)
    foundation_area = foundation_width * foundation_length

    load_factors = [0.6, 0.8, 1.0, 1.2]
    soil_factors = [0.8, 1.0, 1.2, 1.4]

    results = []

    for lf in load_factors:
        for sf in soil_factors:

            total_load = base_total_load * lf
            adjusted_soil_capacity = soil_capacity * sf

            # --------------------------------
            # SAFE DIVISION GUARD
            # --------------------------------

            if foundation_area == 0:
                soil_pressure = float("inf")
            else:
                soil_pressure = total_load / foundation_area

            if column_capacity == 0:
                column_utilization = float("inf")
            else:
                column_utilization = total_load / column_capacity

            if adjusted_soil_capacity == 0:
                soil_utilization = float("inf")
            else:
                soil_utilization = soil_pressure / adjusted_soil_capacity

            utilization_ratio = max(column_utilization, soil_utilization)

            if utilization_ratio <= 1.0:
                status = "SAFE"
            else:
                status = "FAIL"

            if soil_utilization > column_utilization:
                governing_mode = "SOIL"
            else:
                governing_mode = "COLUMN"

            results.append({
                "load": round(total_load, 2),
                "soil_capacity": round(adjusted_soil_capacity, 2),
                "column_utilization": round(column_utilization, 3),
                "soil_utilization": round(soil_utilization, 3),
                "governing_mode": governing_mode,
                "status": status
            })

    return pd.DataFrame(results)