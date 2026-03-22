# ============================================
# TRIPLE BOT — MASTER ENGINE
# VERSION: V3.2
# Deterministic Structural Validation System
# ============================================

from multi_storey_engine import multi_storey_validation
from sensitivity_engine import run_sensitivity_analysis
from scenario_engine import run_scenario_exploration
from pre_bim_validation_engine import run_prebim_validation
from engineering_intelligence_engine import generate_engineering_intelligence


def run_triplebot_analysis(
    foundation_width,
    foundation_length,
    load_per_storey,
    storeys,
    soil_capacity,
    column_capacity
):

    # ============================================
    # FOUNDATION
    # ============================================

    foundation_area = foundation_width * foundation_length

    # ============================================
    # STRUCTURAL VALIDATION
    # ============================================

    structural_validation = multi_storey_validation(
        load_per_storey=load_per_storey,
        storeys=storeys,
        column_capacity=column_capacity,
        foundation_area=foundation_area,
        soil_capacity=soil_capacity
    )

    # ============================================
    # ENGINEERING INTELLIGENCE
    # ============================================

    engineering_intelligence = generate_engineering_intelligence(
        structural_validation
    )

    # ============================================
    # SENSITIVITY ANALYSIS
    # BUG FIX: was passing foundation_area instead of
    # storeys, foundation_width, foundation_length
    # ============================================

    sensitivity_analysis = run_sensitivity_analysis(
        load_per_storey,
        storeys,           # was: foundation_area (WRONG)
        foundation_width,  # was: soil_capacity (WRONG)
        foundation_length, # was: column_capacity (WRONG)
        column_capacity,
        soil_capacity
    )

    # ============================================
    # SCENARIO EXPLORATION
    # BUG FIX: same wrong-argument pattern as sensitivity
    # ============================================

    scenario_exploration = run_scenario_exploration(
        load_per_storey,
        storeys,           # was: foundation_area (WRONG)
        foundation_width,  # was: soil_capacity (WRONG)
        foundation_length, # was: column_capacity (WRONG)
        column_capacity,
        soil_capacity
    )

    # ============================================
    # PRE-BIM VALIDATION
    # ============================================

    pre_bim_validation = run_prebim_validation(
        foundation_width,
        foundation_length,
        load_per_storey,
        soil_capacity
    )

    # ============================================
    # INPUT DATA (FOR REPORT)
    # ============================================

    input_data = {
        "foundation_width": foundation_width,
        "foundation_length": foundation_length,
        "column_capacity": column_capacity,
        "soil_capacity": soil_capacity,
        "load_per_storey": load_per_storey,
        "storeys": storeys,
        "column_safety_factor": 1.5,
        "soil_safety_factor": 3.0
    }

    # ============================================
    # FINAL RESULT PACKAGE
    # ============================================

    result = {

        "input_data": input_data,

        "structural_validation": structural_validation,

        "engineering_intelligence": engineering_intelligence,

        "sensitivity_analysis": sensitivity_analysis,

        "scenario_exploration": scenario_exploration,

        "pre_bim_validation": pre_bim_validation
    }

    return result
