# ============================================
# TRIPLE BOT V3
# Pre-BIM Validation Engine
# ============================================

def run_prebim_validation(
    load_per_storey,
    number_of_storeys,
    foundation_width,
    foundation_length,
    column_capacity,
    soil_capacity
):

    # ----------------------------------------
    # TOTAL LOAD
    # ----------------------------------------

    # FIX: round total_load immediately to prevent floating point
    # artifacts like 299.999 in downstream calculations
    total_load = round(load_per_storey * number_of_storeys, 3)

    # ----------------------------------------
    # FOUNDATION AREA
    # ----------------------------------------

    foundation_area = foundation_width * foundation_length

    # ----------------------------------------
    # SAFE DIVISION GUARD
    # ----------------------------------------

    if foundation_area == 0:
        soil_pressure = float("inf")
    else:
        soil_pressure = total_load / foundation_area

    if soil_capacity == 0:
        required_area = float("inf")
        utilization = float("inf")
    else:
        required_area = total_load / soil_capacity
        utilization = soil_pressure / soil_capacity

    # ----------------------------------------
    # STATUS
    # ----------------------------------------

    if utilization <= 1.0:
        status = "PASS"
    else:
        status = "FAIL"

    # ----------------------------------------
    # RESULT
    # ----------------------------------------

    result = {
        "total_load": round(total_load, 2),
        "foundation_area": round(foundation_area, 3),
        "soil_pressure": round(soil_pressure, 3),
        "required_area": round(required_area, 3),
        "utilization": round(utilization, 3),
        "status": status
    }

    return result