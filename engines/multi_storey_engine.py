# ============================================
# TRIPLE BOT — MULTI STOREY STRUCTURAL ENGINE
# VERSION: V3.1 FINAL+
# MODULE: Multi-Storey Structural Model
# Conservative Engineering Upgrade
# ============================================

import math


def calculate_total_load(load_per_storey, storeys):
    total_load = load_per_storey * storeys
    return total_load


def apply_load_factor(total_load, load_factor):
    return total_load * load_factor


def calculate_allowable_capacity(capacity, safety_factor):
    return capacity / safety_factor


def check_column_capacity(design_load, column_capacity, column_safety_factor):

    allowable_capacity = calculate_allowable_capacity(
        column_capacity,
        column_safety_factor
    )

    utilization = design_load / allowable_capacity
    margin = allowable_capacity - design_load

    if utilization <= 1.0:
        status = "SAFE"
    else:
        status = "FAIL"

    return {
        "allowable_capacity": allowable_capacity,
        "utilization": utilization,
        "margin": margin,
        "status": status
    }


def check_soil_capacity(design_load, foundation_area, soil_capacity, soil_safety_factor):

    allowable_soil_capacity = calculate_allowable_capacity(
        soil_capacity,
        soil_safety_factor
    )

    soil_pressure = design_load / foundation_area
    utilization = soil_pressure / allowable_soil_capacity
    margin = allowable_soil_capacity - soil_pressure

    if utilization <= 1.0:
        status = "SAFE"
    else:
        status = "FAIL"

    return {
        "soil_pressure": soil_pressure,
        "allowable_soil_capacity": allowable_soil_capacity,
        "utilization": utilization,
        "margin": margin,
        "status": status
    }


def detect_limit_state(column_utilization, soil_utilization):

    if soil_utilization > 1:
        return "SOIL_CAPACITY_EXCEEDED"

    if column_utilization > 1:
        return "COLUMN_CAPACITY_EXCEEDED"

    return "SAFE_STRUCTURE"


def generate_recommendation(limit_state):

    if limit_state == "SOIL_CAPACITY_EXCEEDED":
        return "Increase foundation area"

    if limit_state == "COLUMN_CAPACITY_EXCEEDED":
        return "Increase column capacity or reduce load"

    return "Structure within conservative safety limits"


def calculate_required_foundation(design_load, allowable_soil_capacity):

    required_area = design_load / allowable_soil_capacity

    square_size = math.sqrt(required_area)

    return {
        "recommended_foundation_area": required_area,
        "recommended_square_size": square_size
    }


def multi_storey_validation(
    load_per_storey,
    storeys,
    column_capacity,
    foundation_area,
    soil_capacity,
    load_factor=1.2,
    column_safety_factor=1.5,
    soil_safety_factor=3.0
):

    total_load = calculate_total_load(load_per_storey, storeys)

    design_load = apply_load_factor(
        total_load,
        load_factor
    )

    column_check = check_column_capacity(
        design_load,
        column_capacity,
        column_safety_factor
    )

    soil_check = check_soil_capacity(
        design_load,
        foundation_area,
        soil_capacity,
        soil_safety_factor
    )

    column_utilization = column_check["utilization"]
    soil_utilization = soil_check["utilization"]

    if soil_utilization > column_utilization:
        governing_mode = "SOIL"
    else:
        governing_mode = "COLUMN"

    critical_utilization = max(column_utilization, soil_utilization)

    limit_state = detect_limit_state(
        column_utilization,
        soil_utilization
    )

    recommendation = generate_recommendation(limit_state)

    recommended_foundation_area = None
    recommended_square_size = None

    if limit_state == "SOIL_CAPACITY_EXCEEDED":

        required = calculate_required_foundation(
            design_load,
            soil_check["allowable_soil_capacity"]
        )

        recommended_foundation_area = required["recommended_foundation_area"]
        recommended_square_size = required["recommended_square_size"]

    if column_check["status"] == "SAFE" and soil_check["status"] == "SAFE":
        overall_status = "SAFE"
    else:
        overall_status = "FAIL"

    return {
        "total_load": total_load,
        "design_load": design_load,
        "column_utilization": column_utilization,
        "soil_utilization": soil_utilization,
        "column_margin": column_check["margin"],
        "soil_margin": soil_check["margin"],
        "critical_utilization": critical_utilization,
        "governing_mode": governing_mode,
        "limit_state": limit_state,
        "recommendation": recommendation,
        "recommended_foundation_area": recommended_foundation_area,
        "recommended_square_size": recommended_square_size,
        "status": overall_status
    }


def calculate_max_storeys(
    load_per_storey,
    column_capacity,
    foundation_area,
    soil_capacity,
    load_factor=1.2,
    column_safety_factor=1.5,
    soil_safety_factor=3.0,
    max_test=100
):

    for storey in range(1, max_test + 1):

        result = multi_storey_validation(
            load_per_storey,
            storey,
            column_capacity,
            foundation_area,
            soil_capacity,
            load_factor,
            column_safety_factor,
            soil_safety_factor
        )

        if result["status"] == "FAIL":
            return storey - 1

    return max_test