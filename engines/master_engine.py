# ============================================
# TRIPLE BOT V5
# Master Structural Validation Engine
# ============================================

from sensitivity_engine import run_sensitivity_analysis
from scenario_engine import run_scenario_exploration
from pre_bim_validation_engine import run_prebim_validation
from engineering_intelligence_engine import generate_engineering_intelligence

# Load combination
from load_combination_engine import combine_loads

# BUG FIX: construction_output_engine.py does not exist in the project.
# Removed the import to prevent ImportError crash.
# If construction output is needed, create construction_output_engine.py first.


# ============================================
# MAIN STRUCTURAL VALIDATION
# ============================================

def run_structural_validation(
    foundation_width,
    foundation_length,
    column_capacity,
    total_load,
    soil_capacity
):

    foundation_area = foundation_width * foundation_length

    # --------------------------------
    # SOIL PRESSURE
    # --------------------------------

    if foundation_area == 0:
        soil_pressure = float("inf")
    else:
        soil_pressure = total_load / foundation_area

    # --------------------------------
    # COLUMN UTILIZATION
    # --------------------------------

    if column_capacity == 0:
        column_utilization = float("inf")
    else:
        column_utilization = total_load / column_capacity

    # --------------------------------
    # SOIL UTILIZATION
    # --------------------------------

    if soil_capacity == 0:
        soil_utilization = float("inf")
    else:
        soil_utilization = soil_pressure / soil_capacity

    # --------------------------------
    # GOVERNING UTILIZATION
    # --------------------------------

    utilization_ratio = max(column_utilization, soil_utilization)

    if utilization_ratio <= 1.0:
        status = "SAFE"
    else:
        status = "FAIL"

    if soil_utilization > column_utilization:
        governing_mode = "SOIL"
    else:
        governing_mode = "COLUMN"

    # --------------------------------
    # MARGINS
    # --------------------------------

    column_margin = column_capacity - total_load
    soil_margin = soil_capacity - soil_pressure

    result = {
        "status": status,
        "column_utilization": round(column_utilization, 3),
        "soil_utilization": round(soil_utilization, 3),
        "utilization_ratio": round(utilization_ratio, 3),
        "governing_mode": governing_mode,
        "column_margin": round(column_margin, 2),
        "soil_margin": round(soil_margin, 2),
        "foundation_area": foundation_area,
        "soil_pressure": round(soil_pressure, 2) if soil_pressure != float("inf") else float("inf")
    }

    return result


# ============================================
# MASTER ENGINE
# ============================================

def run_master_engine(
    foundation_width,
    foundation_length,
    column_capacity,
    load_per_storey,
    number_of_storeys,
    soil_capacity
):

    # --------------------------------
    # TOTAL LOAD
    # --------------------------------

    total_load = load_per_storey * number_of_storeys

    # --------------------------------
    # STRUCTURAL VALIDATION
    # --------------------------------

    structural_validation = run_structural_validation(
        foundation_width,
        foundation_length,
        column_capacity,
        total_load,
        soil_capacity
    )

    # --------------------------------
    # SENSITIVITY ANALYSIS
    # --------------------------------

    sensitivity = run_sensitivity_analysis(
        load_per_storey,
        number_of_storeys,
        foundation_width,
        foundation_length,
        column_capacity,
        soil_capacity
    )

    # --------------------------------
    # SCENARIO EXPLORATION
    # --------------------------------

    scenario = run_scenario_exploration(
        load_per_storey,
        number_of_storeys,
        foundation_width,
        foundation_length,
        column_capacity,
        soil_capacity
    )

    # --------------------------------
    # PRE-BIM VALIDATION
    # --------------------------------

    prebim = run_prebim_validation(
        load_per_storey,
        number_of_storeys,
        foundation_width,
        foundation_length,
        column_capacity,
        soil_capacity
    )

    # --------------------------------
    # ENGINEERING INTELLIGENCE
    # --------------------------------

    intelligence = generate_engineering_intelligence(structural_validation)

    # --------------------------------
    # FINAL RESULT
    # --------------------------------

    return {
        "structural_validation": structural_validation,
        "sensitivity": sensitivity,
        "scenario": scenario,
        "prebim": prebim,
        "intelligence": intelligence
    }
