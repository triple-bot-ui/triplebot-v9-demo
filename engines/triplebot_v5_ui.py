# ============================================
# TRIPLE BOT V5
# Structural Validation UI
# ============================================

import streamlit as st
import pandas as pd
from datetime import datetime

from master_engine_v3 import run_structural_validation
from scenario_engine import run_scenario_exploration
from sensitivity_engine import run_sensitivity_analysis
from pre_bim_validation_engine import run_prebim_validation
from engineering_intelligence_engine import generate_engineering_intelligence
from triplebot_report_generator import generate_engineering_report
from boq_engine import generate_boq
from triplebot_diagram_engine import generate_conceptual_diagram

# ============================================
# V8 IMPORT
# ============================================

from engineering_option_engine import generate_engineering_options
from engineering_option_ranking_engine import rank_engineering_options
from engineering_decision_engine_v8 import generate_engineering_decision


st.set_page_config(page_title="Triple Bot V5", layout="wide")

st.title("Triple Bot V5 – Structural Validation")

# ============================================
# SYSTEM TRACEABILITY
# ============================================

SYSTEM_VERSION = "Triple Bot V5"
timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

st.caption(f"System Version: {SYSTEM_VERSION}")
st.caption(f"Timestamp: {timestamp}")

st.info("🔒 Deterministic Engine · No generative AI · All results reproducible")

# ============================================
# INPUT SECTION
# ============================================

foundation_width = st.number_input(
    "Foundation Width (m)", min_value=0.001, value=1.0, step=0.001, format="%.3f"
)

foundation_length = st.number_input(
    "Foundation Length (m)", min_value=0.001, value=1.0, step=0.001, format="%.3f"
)

column_capacity = st.number_input(
    "Column Capacity (kN)", value=500.0, min_value=0.0
)

load_per_storey = st.number_input(
    "Load per Storey (kN)", value=300.0, min_value=0.0
)

st.caption(
    "Load input represents assumed structural load for preliminary validation. "
    "Actual load should be determined according to applicable structural design codes."
)

storeys = st.number_input(
    "Number of Storeys", value=1, min_value=1
)

soil_capacity = st.number_input(
    "Soil Capacity (kN/m²)", value=200.0, min_value=0.0
)

st.caption(
    "Soil capacity should be based on geotechnical investigation or soil report."
)

run = st.button("Run Validation")

# ============================================
# INPUT VALIDATION
# ============================================

if run:

    if foundation_width <= 0 or foundation_length <= 0:
        st.error("Foundation dimensions must be greater than zero.")
        st.stop()

    if column_capacity <= 0:
        st.error("Column capacity must be greater than zero.")
        st.stop()

    if soil_capacity <= 0:
        st.error("Soil capacity must be greater than zero.")
        st.stop()

    total_load = round(load_per_storey * storeys, 3)

    # BUG FIX A: warn early if foundation is clearly undersized
    foundation_area_check = foundation_width * foundation_length
    required_area_check = total_load / soil_capacity
    if foundation_area_check < required_area_check:
        import math
        min_side = math.ceil(math.sqrt(required_area_check) * 100) / 100
        st.warning(
            f"⚠️ Foundation area ({foundation_area_check:.3f} m²) is smaller than "
            f"required area ({required_area_check:.3f} m²). "
            f"Validation will FAIL. Minimum recommended size: {min_side} × {min_side} m."
        )

    st.info(
        "Model scope: single column supported by a spread footing under axial load."
    )

    # ============================================
    # STRUCTURAL VALIDATION
    # ============================================

    result = run_structural_validation(
        foundation_width,
        foundation_length,
        column_capacity,
        total_load,
        soil_capacity
    )

    st.header("Structural Validation Result")

    status = result["status"]
    column_util = result["column_utilization"]
    soil_util = result["soil_utilization"]

    column_margin = result["column_margin"]
    soil_margin = result["soil_margin"]

    governing_mode = result["governing_mode"]

    if status == "SAFE":
        st.success("Status: SAFE")
    elif status == "WARNING":
        st.warning("Status: WARNING — Design is approaching structural limit. Review recommended.")
    else:
        st.error("Status: FAIL")

    # ============================================
    # V8 DECISION
    # ============================================

    input_data = {
        "foundation_width": foundation_width,
        "foundation_length": foundation_length,
        "load_per_storey": load_per_storey,
        "storeys": storeys,
        "soil_capacity": soil_capacity,
        "column_capacity": column_capacity
    }

    options = generate_engineering_options(result, input_data)
    ranked_options = rank_engineering_options(options)
    decision = generate_engineering_decision(ranked_options, result)

    # ============================================
    # ENGINEERING SUMMARY
    # BUG FIX B: removed duplicate "Recommended Action" block
    # (it duplicates the Engineering Decision section below)
    # ============================================

    st.header("Engineering Summary")

    critical_utilization = max(column_util, soil_util)
    design_reserve = (1 - critical_utilization) * 100

    col_sum1, col_sum2, col_sum3 = st.columns(3)

    col_sum1.metric(
        "Critical Utilization",
        f"{critical_utilization:.3f}"
    )

    col_sum2.metric(
        "Design Reserve (%)",
        f"{design_reserve:.1f}"
    )

    col_sum3.metric(
        "Governing Mode",
        governing_mode
    )

    # ============================================
    # STRUCTURAL DIAGRAM
    # BUG FIX C: guard against diagram returning None
    # ============================================

    st.subheader("Structural Conceptual Diagram")

    try:
        diagram = generate_conceptual_diagram(
            foundation_width,
            foundation_length,
            total_load,
            result["soil_pressure"]
        )
        if diagram is not None:
            st.image(diagram)
        else:
            st.warning("Diagram could not be generated.")
    except Exception as e:
        st.warning(f"Diagram generation failed: {e}")

    # ============================================
    # UTILIZATION DISPLAY
    # BUG FIX D: clamp to [0.0, 1.0] — negative values crash st.progress()
    # BUG FIX (Issue 3): show overflow label so util=1.2 and util=1000
    # are visually distinguishable (bar is always full when >1, but
    # label shows actual severity)
    # ============================================

    st.subheader("Utilization Overview")

    st.write("Column Utilization")
    st.progress(max(0.0, min(column_util, 1.0)))
    if column_util > 1.0:
        st.caption(f"⚠️ Overloaded — {column_util:.1f}× capacity ({column_util*100:.0f}%)")

    st.write("Soil Utilization")
    st.progress(max(0.0, min(soil_util, 1.0)))
    if soil_util > 1.0:
        st.caption(f"⚠️ Overloaded — {soil_util:.1f}× capacity ({soil_util*100:.0f}%)")

    col1, col2 = st.columns(2)

    col1.metric("Column Utilization", f"{column_util:.3f}")
    col2.metric("Soil Utilization", f"{soil_util:.3f}")

    col1.metric("Column Margin (kN)", f"{column_margin:.2f}")
    col2.metric("Soil Margin (kN/m²)", f"{soil_margin:.2f}")

    st.write(f"Governing Mode: **{governing_mode}**")

    # ============================================
    # SAFETY FACTORS
    # BUG FIX E: reuse result["soil_pressure"] instead of recalculating
    # BUG FIX (Issue 2): use dynamic decimal places so values like
    # 0.001 never round-display as 0.00
    # ============================================

    st.subheader("Safety Factors")

    soil_pressure = result["soil_pressure"]

    column_sf = column_capacity / total_load
    soil_sf = soil_capacity / soil_pressure if soil_pressure > 0 else float('inf')

    def format_sf(value):
        if value >= 0.01:
            return f"{value:.4f}"
        elif value >= 0.0001:
            return f"{value:.6f}"
        else:
            return f"{value:.2e}"

    col3, col4 = st.columns(2)

    col3.metric("Column Safety Factor", format_sf(column_sf))
    col4.metric("Soil Safety Factor", format_sf(soil_sf))

    # ============================================
    # SCENARIO
    # ============================================

    st.header("Scenario Exploration")

    scenario_df = run_scenario_exploration(
        load_per_storey,
        storeys,
        foundation_width,
        foundation_length,
        column_capacity,
        soil_capacity
    )

    st.dataframe(pd.DataFrame(scenario_df))

    # ============================================
    # SENSITIVITY
    # ============================================

    st.header("Sensitivity Analysis")

    sens_df = run_sensitivity_analysis(
        load_per_storey,
        storeys,
        foundation_width,
        foundation_length,
        column_capacity,
        soil_capacity
    )

    st.dataframe(pd.DataFrame(sens_df))

    # ============================================
    # PRE-BIM
    # ============================================

    st.header("Pre-BIM Validation")

    prebim = run_prebim_validation(
        load_per_storey,
        storeys,
        foundation_width,
        foundation_length,
        column_capacity,
        soil_capacity
    )

    col5, col6 = st.columns(2)

    col5.metric("Total Load (kN)", prebim["total_load"])
    col6.metric("Soil Pressure (kN/m²)", prebim["soil_pressure"])

    col5.metric("Foundation Area (m²)", prebim["foundation_area"])
    col6.metric("Required Area (m²)", prebim["required_area"])

    st.write(f"Utilization: {prebim['utilization']}")
    st.write(f"Status: {prebim['status']}")

    # ============================================
    # CONSTRUCTION RECOMMENDATION
    # BUG FIX G: use st.error() for UNSAFE — was st.success() (green box) which is misleading
    # ============================================

    st.header("Construction Recommendation")

    intelligence = generate_engineering_intelligence(result)

    if status == "SAFE":
        st.success(intelligence["recommendation"])
    elif status == "WARNING":
        st.warning(intelligence["recommendation"])
    else:
        st.error(intelligence["recommendation"])

    # ============================================
    # ENGINEERING DECISION
    # BUG FIX H: guard against load_reduction being None before * 100
    # ============================================

    st.header("Engineering Decision")

    st.caption(
        "V8 recommendations are advisory optimization suggestions "
        "generated by the decision layer."
    )

    if status == "SAFE":
        st.write("No engineering action required.")

    elif status == "WARNING":
        st.warning("⚠️ Design is near structural limit. Engineer review is recommended before proceeding.")

    else:

        if decision.get("best_option"):

            option = decision["best_option"]
            option_type = option.get("option_type")

            if option_type == "FOUNDATION_INCREASE":
                size = option.get("foundation_size")
                st.write(f"Recommended: Increase foundation size to {size} m")

            elif option_type == "COLUMN_UPGRADE":
                capacity = option.get("column_capacity")
                st.write(f"Recommended: Upgrade column capacity to {capacity} kN")

            elif option_type == "LOAD_REDUCTION":
                load_reduction = option.get("load_reduction")
                if load_reduction is not None:
                    st.write(f"Recommended: Reduce load by {load_reduction * 100:.1f}%")
                else:
                    st.write("Recommended: Reduce structural load.")

            else:
                st.write("Engineering optimization available.")

        else:
            st.write("No engineering action required.")

    # ============================================
    # BOQ SECTION
    # BUG FIX I: use recommended foundation size for BOQ when status is FAIL
    # ============================================

    st.header("Bill of Quantities")

    boq_width = foundation_width
    boq_length = foundation_length

    if status != "SAFE" and decision.get("best_option"):
        option = decision["best_option"]
        if option.get("option_type") == "FOUNDATION_INCREASE":
            rec_size = option.get("foundation_size")
            if rec_size is not None:
                boq_width = rec_size
                boq_length = rec_size
                st.caption(
                    f"BOQ calculated using recommended foundation size: "
                    f"{rec_size} × {rec_size} m (not the input size)."
                )

    boq = generate_boq(
        boq_width,
        boq_length,
        total_load,
        soil_capacity
    )

    col7, col8 = st.columns(2)

    col7.metric("Foundation Area (m²)", boq["foundation_area"])
    col8.metric("Foundation Depth (m)", boq["foundation_depth"])

    col7.metric("Concrete Volume (m³)", boq["concrete_volume_m3"])
    col8.metric("Excavation Volume (m³)", boq["excavation_volume_m3"])

    st.metric("Reinforcement Estimate (kg)", boq["reinforcement_estimate"])

    # ============================================
    # REPORT
    # ============================================

    st.header("Download Engineering Report")

    pdf = generate_engineering_report(
        result,
        intelligence,
        prebim,
        boq,
        decision
    )

    st.download_button(
        label="Download PDF Report",
        data=pdf,
        file_name="engineering_report.pdf",
        mime="application/pdf"
    )
