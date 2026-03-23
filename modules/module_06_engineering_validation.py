# ============================================
# TRIPLE BOT V9.7
# Module 06 — Engineering Validation Interface
# UI: Decision Layer only, detail in expander
# UPDATE: Added Calculation Transparency section
# ============================================

def run_engineering_validation(project_data):

    foundation_width  = project_data["foundation_width"]
    foundation_length = project_data["foundation_length"]
    column_capacity   = project_data["column_capacity"]
    soil_capacity     = project_data["soil_capacity"]
    num_floors        = project_data["num_floors"]
    building_width    = project_data["building_width"]
    building_length   = project_data["building_length"]

    floor_area = building_width * building_length
    total_load = project_data.get("total_load")
    if total_load is None:
        total_load = floor_area * 7.5 * num_floors

    engineering_load_per_storey = project_data.get(
        "engineering_load_per_storey",
        total_load / num_floors if num_floors > 0 else 0.0
    )

    input_payload = dict(project_data)
    input_payload["engineering_load_per_storey"] = engineering_load_per_storey
    input_payload["total_load"] = total_load

    from master_engine_v3 import run_structural_validation
    from scenario_engine import run_scenario_exploration
    from sensitivity_engine import run_sensitivity_analysis
    from pre_bim_validation_engine import run_prebim_validation

    validation_result = run_structural_validation(
        foundation_width, foundation_length,
        column_capacity, total_load, soil_capacity
    )
    scenario_result = run_scenario_exploration(
        engineering_load_per_storey, num_floors,
        foundation_width, foundation_length,
        column_capacity, soil_capacity
    )
    sensitivity_result = run_sensitivity_analysis(
        engineering_load_per_storey, num_floors,
        foundation_width, foundation_length,
        column_capacity, soil_capacity
    )
    prebim_result = run_prebim_validation(
        engineering_load_per_storey, num_floors,
        foundation_width, foundation_length,
        column_capacity, soil_capacity
    )

    return {
        "validation":   validation_result,
        "scenario":     scenario_result,
        "sensitivity":  sensitivity_result,
        "prebim":       prebim_result,
        "input":        input_payload
    }


def display_validation_results(st, results):

    validation     = results["validation"]
    prebim         = results["prebim"]
    input_data     = results["input"]
    status         = validation["status"]
    column_util    = validation["column_utilization"]
    soil_util      = validation["soil_utilization"]
    governing_mode = validation["governing_mode"]
    soil_pressure  = validation.get("soil_pressure", prebim.get("soil_pressure", 1.0))

    # ── CSS ──
    st.markdown("""
    <style>
    .vf-wrap {
        border: 1px solid #e0e0de;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 16px;
        font-family: 'DM Mono', monospace;
    }
    .vf-status-fail {
        background: #2a2a2a;
        color: #fff;
        padding: 10px 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .vf-status-pass {
        background: #2a2a2a;
        color: #fff;
        padding: 10px 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .vf-status-label {
        font-size: 13px;
        font-weight: 400;
        letter-spacing: .04em;
    }
    .vf-status-mode {
        font-size: 10px;
        color: #aaa;
        letter-spacing: .1em;
    }
    .vf-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        background: #fff;
    }
    .vf-cell {
        padding: 14px 18px;
        border-bottom: 1px solid #f0f0ee;
        border-right: 1px solid #f0f0ee;
    }
    .vf-cell:nth-child(even) { border-right: none; }
    .vf-cell-label {
        font-size: 9px;
        color: #bbb;
        letter-spacing: .1em;
        text-transform: uppercase;
        margin-bottom: 3px;
    }
    .vf-cell-val {
        font-size: 20px;
        font-weight: 400;
        color: #111;
        line-height: 1.1;
    }
    .vf-cell-val.bad  { color: #666; }
    .vf-cell-val.good { color: #222; }
    .vf-cell-sub {
        font-size: 10px;
        color: #aaa;
        margin-top: 2px;
    }
    .calc-wrap {
        border: 1px solid #e8e8e6;
        border-radius: 6px;
        background: #fafaf8;
        padding: 14px 18px;
        font-family: 'DM Mono', monospace;
        margin-bottom: 12px;
    }
    .calc-title {
        font-size: 9px;
        color: #bbb;
        letter-spacing: .1em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .calc-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 6px;
        gap: 8px;
    }
    .calc-formula {
        font-size: 10px;
        color: #999;
        flex: 1;
    }
    .calc-eq {
        font-size: 10px;
        color: #bbb;
        white-space: nowrap;
        margin: 0 8px;
    }
    .calc-result {
        font-size: 11px;
        font-weight: 600;
        color: #333;
        white-space: nowrap;
    }
    .calc-divider {
        border: none;
        border-top: 1px solid #eee;
        margin: 8px 0;
    }
    .calc-note {
        font-size: 9px;
        color: #bbb;
        margin-top: 8px;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Status label ──
    is_fail = status == "FAIL"
    status_icon = "✗ FAIL — Redesign required" if is_fail else ("⚠ WARNING" if status == "WARNING" else "✓ SAFE")

    critical_util  = max(column_util, soil_util)
    design_reserve = (1 - critical_util) * 100

    st.markdown(f"""
    <div class="vf-wrap">
      <div class="vf-status-fail">
        <span class="vf-status-label">{status_icon}</span>
        <span class="vf-status-mode">GOVERNING · {governing_mode}</span>
      </div>
      <div class="vf-grid">
        <div class="vf-cell">
          <div class="vf-cell-label">Soil Utilization</div>
          <div class="vf-cell-val bad">{soil_util:.3f}</div>
          <div class="vf-cell-sub">Limit = 1.010 (Engineering Tolerance)</div>
        </div>
        <div class="vf-cell">
          <div class="vf-cell-label">Column Utilization</div>
          <div class="vf-cell-val bad">{column_util:.3f}</div>
          <div class="vf-cell-sub">Limit = 1.010 (Engineering Tolerance)</div>
        </div>
        <div class="vf-cell">
          <div class="vf-cell-label">Critical Utilization</div>
          <div class="vf-cell-val">{critical_util:.3f}</div>
          <div class="vf-cell-sub">Max of soil / column</div>
        </div>
        <div class="vf-cell">
          <div class="vf-cell-label">Design Reserve</div>
          <div class="vf-cell-val">{design_reserve:.1f}%</div>
          <div class="vf-cell-sub">Positive = margin remaining</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ============================================
    # CALCULATION TRANSPARENCY — NEW SECTION
    # ============================================

    floor_area       = input_data["building_width"] * input_data["building_length"]
    total_load       = input_data["total_load"]
    foundation_area  = input_data["foundation_width"] * input_data["foundation_length"]
    required_area    = total_load / input_data["soil_capacity"] if input_data["soil_capacity"] > 0 else 0
    load_factor      = 7.5  # kN/m² — internal benchmark

    col_util_calc    = total_load / input_data["column_capacity"] if input_data["column_capacity"] > 0 else 0
    soil_util_calc   = total_load / (foundation_area * input_data["soil_capacity"]) if foundation_area > 0 and input_data["soil_capacity"] > 0 else 0
    soil_pres_calc   = total_load / foundation_area if foundation_area > 0 else 0

    with st.expander("▸ Calculation Path", expanded=False):
        st.markdown(f"""
        <div class="calc-wrap">
          <div class="calc-title">Load Calculation</div>

          <div class="calc-row">
            <span class="calc-formula">Floor Area = Width × Length</span>
            <span class="calc-eq">= {input_data['building_width']} × {input_data['building_length']}</span>
            <span class="calc-result">= {floor_area:.2f} m²</span>
          </div>

          <div class="calc-row">
            <span class="calc-formula">Total Load = Floor Area × {load_factor} kN/m² × Floors</span>
            <span class="calc-eq">= {floor_area:.2f} × {load_factor} × {input_data['num_floors']}</span>
            <span class="calc-result">= {total_load:.1f} kN</span>
          </div>

          <hr class="calc-divider"/>
          <div class="calc-title">Foundation Check</div>

          <div class="calc-row">
            <span class="calc-formula">Foundation Area = Width × Length</span>
            <span class="calc-eq">= {input_data['foundation_width']} × {input_data['foundation_length']}</span>
            <span class="calc-result">= {foundation_area:.4f} m²</span>
          </div>

          <div class="calc-row">
            <span class="calc-formula">Required Area = Total Load ÷ Soil Capacity</span>
            <span class="calc-eq">= {total_load:.1f} ÷ {input_data['soil_capacity']}</span>
            <span class="calc-result">= {required_area:.4f} m²</span>
          </div>

          <div class="calc-row">
            <span class="calc-formula">Soil Pressure = Total Load ÷ Foundation Area</span>
            <span class="calc-eq">= {total_load:.1f} ÷ {foundation_area:.4f}</span>
            <span class="calc-result">= {soil_pres_calc:.2f} kN/m²</span>
          </div>

          <hr class="calc-divider"/>
          <div class="calc-title">Utilization Check</div>

          <div class="calc-row">
            <span class="calc-formula">Soil Utilization = Soil Pressure ÷ Soil Capacity</span>
            <span class="calc-eq">= {soil_pres_calc:.2f} ÷ {input_data['soil_capacity']}</span>
            <span class="calc-result">= {soil_util_calc:.3f}</span>
          </div>

          <div class="calc-row">
            <span class="calc-formula">Column Utilization = Total Load ÷ Column Capacity</span>
            <span class="calc-eq">= {total_load:.1f} ÷ {input_data['column_capacity']}</span>
            <span class="calc-result">= {col_util_calc:.3f}</span>
          </div>

          <div class="calc-row">
            <span class="calc-formula">Pass Condition: Utilization ≤ 1.010</span>
            <span class="calc-eq"></span>
            <span class="calc-result">Limit = 1.010</span>
          </div>

          <hr class="calc-divider"/>
          <div class="calc-note">
            Load basis: {load_factor} kN/m² includes safety factor (~1.5×) above typical residential dead+live load of 5 kN/m².<br>
            All calculations are deterministic and reproducible.<br>
            Final verification must be conducted by a licensed structural engineer.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Technical detail hidden ──
    with st.expander("▸ Validation Detail", expanded=False):
        import pandas as pd

        c1, c2 = st.columns(2)
        with c1:
            st.caption("Pre-BIM Check")
            st.markdown(f"""
            <table style="font-size:11px;width:100%;font-family:'DM Mono',monospace">
              <tr><td style="color:#aaa">Total Load</td><td style="font-weight:400">{prebim['total_load']} kN</td></tr>
              <tr><td style="color:#aaa">Soil Pressure</td><td style="font-weight:400">{prebim['soil_pressure']} kN/m²</td></tr>
              <tr><td style="color:#aaa">Foundation Area</td><td style="font-weight:400">{prebim['foundation_area']} m²</td></tr>
              <tr><td style="color:#aaa">Required Area</td><td style="font-weight:400">{prebim['required_area']} m²</td></tr>
              <tr><td style="color:#aaa">Status</td><td style="font-weight:400">{prebim['status']}</td></tr>
            </table>
            """, unsafe_allow_html=True)

        with c2:
            total_load_v   = results["input"]["total_load"]
            col_capacity   = results["input"]["column_capacity"]
            soil_cap       = results["input"]["soil_capacity"]
            column_sf      = col_capacity / total_load_v if total_load_v > 0 else float("inf")
            soil_sf        = soil_cap / soil_pressure if soil_pressure > 0 else float("inf")
            col_margin     = validation["column_margin"]
            soil_margin    = validation["soil_margin"]

            st.caption("Safety Factors & Margins")
            st.markdown(f"""
            <table style="font-size:11px;width:100%;font-family:'DM Mono',monospace">
              <tr><td style="color:#aaa">Column Safety Factor</td><td style="font-weight:400">{column_sf:.4f}</td></tr>
              <tr><td style="color:#aaa">Soil Safety Factor</td><td style="font-weight:400">{soil_sf:.4f}</td></tr>
              <tr><td style="color:#aaa">Column Margin (kN)</td><td style="font-weight:400">{col_margin:.2f}</td></tr>
              <tr><td style="color:#aaa">Soil Margin (kN/m²)</td><td style="font-weight:400">{soil_margin:.2f}</td></tr>
            </table>
            """, unsafe_allow_html=True)

        st.caption("Scenario Exploration")
        st.dataframe(pd.DataFrame(results["scenario"]), use_container_width=True)

        st.caption("Sensitivity Analysis")
        st.dataframe(pd.DataFrame(results["sensitivity"]), use_container_width=True)


def extract_validation_for_decision(results):
    validation = results["validation"]
    input_data = results["input"]
    return {
        "total_load":         input_data["total_load"],
        "column_utilization": validation["column_utilization"],
        "soil_utilization":   validation["soil_utilization"],
        "column_margin":      validation["column_margin"],
        "soil_margin":        validation["soil_margin"],
        "soil_pressure":      validation.get("soil_pressure"),
        "governing_mode":     validation["governing_mode"],
        "status":             validation["status"]
    }
