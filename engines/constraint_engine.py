# =========================================
# TRIPLE BOT V4
# STRUCTURAL CONSTRAINT ENGINE
# =========================================


def run_constraint_check(
    foundation_width,
    foundation_length,
    column_capacity,
    total_load,
    soil_capacity
):

    foundation_area = foundation_width * foundation_length

    # BUG FIX: guard division by zero before calculating utilization
    if column_capacity == 0:
        column_utilization = float("inf")
    else:
        column_utilization = total_load / column_capacity

    if foundation_area == 0:
        soil_pressure = float("inf")
        soil_utilization = float("inf")
    else:
        soil_pressure = total_load / foundation_area
        if soil_capacity == 0:
            soil_utilization = float("inf")
        else:
            soil_utilization = soil_pressure / soil_capacity

    constraints = []

    # -------------------------------
    # Constraint 1
    # Column Utilization Limit
    # -------------------------------

    if column_utilization > 0.9:
        constraints.append({
            "constraint": "COLUMN_UTILIZATION_LIMIT",
            "status": "WARNING",
            "message": "Column utilization exceeds recommended engineering limit (0.9)."
        })

    # -------------------------------
    # Constraint 2
    # Soil Utilization Limit
    # -------------------------------

    if soil_utilization > 0.8:
        constraints.append({
            "constraint": "SOIL_UTILIZATION_LIMIT",
            "status": "WARNING",
            "message": "Soil utilization exceeds allowable bearing capacity."
        })

    # -------------------------------
    # Constraint 3
    # Minimum Foundation Area
    # -------------------------------

    min_foundation_area = 0.5

    if foundation_area < min_foundation_area:
        constraints.append({
            "constraint": "MIN_FOUNDATION_SIZE",
            "status": "WARNING",
            "message": "Foundation area smaller than recommended minimum."
        })

    # -------------------------------
    # Governing Constraint Detection
    # -------------------------------

    if soil_utilization > column_utilization and soil_utilization > 1.0:
        constraints.append({
            "constraint": "CRITICAL_SOIL_FAILURE",
            "status": "CRITICAL",
            "message": "Soil bearing capacity governs structural failure."
        })

    elif column_utilization >= soil_utilization and column_utilization > 1.0:
        constraints.append({
            "constraint": "CRITICAL_COLUMN_FAILURE",
            "status": "CRITICAL",
            "message": "Column capacity governs structural failure."
        })

    # -------------------------------
    # Final Constraint Status
    # -------------------------------

    if len(constraints) == 0:

        return {
            "constraint_status": "PASS",
            "constraints": []
        }

    else:

        return {
            "constraint_status": "WARNING",
            "constraints": constraints
        }
