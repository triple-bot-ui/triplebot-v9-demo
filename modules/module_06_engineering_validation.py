# ============================================
# TRIPLE BOT V9.9.5
# Module 06 — Engineering Validation Interface
# FULL FILE REPLACEMENT
# V9.5 STEP 1:
# - Add Input Reliability Flag
# - Keep validation logic stable
# - Keep Trust Layer integration stable
# - No core engineering calculation rewrite
# ============================================

import re
import html


PASS_LIMIT = 1.010
LOAD_FACTOR_KN_M2 = 7.5
SAFETY_FACTOR_APPROX = 1.5


def _clean_text(text):
    if text is None:
        return "—"
    if not isinstance(text, str):
        text = str(text)

    text = html.unescape(text)
    text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text, flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else "—"


def _safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_num(value, decimals=3):
    num = _safe_float(value, None)
    if num is None:
        return "N/A"
    return f"{num:.{decimals}f}"


def _format_delta(value, decimals=3):
    num = _safe_float(value, None)
    if num is None:
        return "N/A"
    return f"{num:+.{decimals}f}"


def _normalize_validation_status(validation_result):
    """
    Product rule:
    If BOTH utilizations are <= 1.010, status must be PASS.
    WARNING should not remain for tolerance-accepted structural results.

    This fixes semantic mismatch at the interface layer
    without rewriting the core calculation engine.
    """
    normalized = dict(validation_result or {})

    original_status = str(normalized.get("status", "")).strip()
    raw_status = original_status.upper()

    soil_util = _safe_float(normalized.get("soil_utilization"))
    column_util = _safe_float(normalized.get("column_utilization"))

    recognized_status_family = (
        raw_status.startswith("PASS")
        or raw_status in ("SAFE", "WARNING", "FAIL")
    )

    normalized["status_original"] = original_status if original_status else "N/A"

    if recognized_status_family and soil_util is not None and column_util is not None:
        if soil_util <= PASS_LIMIT and column_util <= PASS_LIMIT:
            normalized["status"] = "PASS"
        else:
            normalized["status"] = "FAIL"
        return normalized

    if raw_status.startswith("PASS") or raw_status in ("SAFE", "WARNING"):
        normalized["status"] = "PASS"
    elif raw_status == "FAIL":
        normalized["status"] = "FAIL"

    return normalized


def _build_input_reliability(raw_project_data, input_payload):
    """
    Build explicit source flags so engineers know
    which values are user inputs and which values are
    system assumptions / derived values / internal rules.
    """

    def _source_label(source_key):
        mapping = {
            "user": "USER INPUT",
            "derived": "SYSTEM DERIVED",
            "assumption": "SYSTEM ASSUMPTION",
            "default": "SYSTEM DEFAULT",
            "rule": "INTERNAL RULE",
        }
        return mapping.get(source_key, "N/A")

    def _source_class(source_key):
        mapping = {
            "user": "tl-source-user",
            "derived": "tl-source-derived",
            "assumption": "tl-source-assumption",
            "default": "tl-source-default",
            "rule": "tl-source-rule",
        }
        return mapping.get(source_key, "")

    def _row(label, value_display, source_key, note):
        return {
            "label": label,
            "value_display": value_display,
            "source": _source_label(source_key),
            "source_key": source_key,
            "source_class": _source_class(source_key),
            "note": note,
        }

    raw_total_load = raw_project_data.get("total_load")
    raw_load_per_storey = raw_project_data.get("engineering_load_per_storey")

    rows = [
        _row(
            "Building Width",
            f"{_format_num(input_payload.get('building_width'), 3)} m",
            "user",
            "Entered directly by user.",
        ),
        _row(
            "Building Length",
            f"{_format_num(input_payload.get('building_length'), 3)} m",
            "user",
            "Entered directly by user.",
        ),
        _row(
            "Storeys",
            str(input_payload.get("num_floors", "N/A")),
            "user",
            "Entered directly by user.",
        ),
        _row(
            "Foundation Width",
            f"{_format_num(input_payload.get('foundation_width'), 3)} m",
            "user",
            "Entered directly by user.",
        ),
        _row(
            "Foundation Length",
            f"{_format_num(input_payload.get('foundation_length'), 3)} m",
            "user",
            "Entered directly by user.",
        ),
        _row(
            "Column Capacity",
            f"{_format_num(input_payload.get('column_capacity'), 3)} kN",
            "user",
            "Entered directly by user.",
        ),
        _row(
            "Soil Capacity",
            f"{_format_num(input_payload.get('soil_capacity'), 3)} kN/m²",
            "user",
            "Entered directly by user.",
        ),
        _row(
            "Engineering Load per Storey",
            f"{_format_num(input_payload.get('engineering_load_per_storey'), 3)} kN",
            "user" if raw_load_per_storey is not None else "derived",
            "User-supplied if entered. Otherwise derived from total load / storeys.",
        ),
        _row(
            "Total Load",
            f"{_format_num(input_payload.get('total_load'), 3)} kN",
            "user" if raw_total_load is not None else "derived",
            "User-supplied if entered. Otherwise derived from floor area × 7.5 kN/m² × storeys.",
        ),
        _row(
            "Load Factor",
            f"{LOAD_FACTOR_KN_M2:.1f} kN/m²",
            "assumption",
            "Fixed engineering assumption in current V9.9.5 scope.",
        ),
        _row(
            "Load Basis",
            "DL 4.5 + LL 3.0 = 7.5 kN/m²",
            "assumption",
            "System uses fixed gravity-load basis for current scope.",
        ),
        _row(
            "Safety Factor",
            f"~{SAFETY_FACTOR_APPROX:.1f}×",
            "assumption",
            "Internal simplified note used for current validation explanation.",
        ),
        _row(
            "Tolerance Rule",
            f"≤ {PASS_LIMIT:.3f}",
            "rule",
            "Internal pass/fail acceptance rule for this version.",
        ),
    ]

    legend = [
        {"label": "USER INPUT", "meaning": "Value entered directly by user."},
        {"label": "SYSTEM DERIVED", "meaning": "Value calculated automatically from current input."},
        {"label": "SYSTEM ASSUMPTION", "meaning": "Fixed engineering assumption used by this version."},
        {"label": "SYSTEM DEFAULT", "meaning": "Fallback default used when user does not provide value."},
        {"label": "INTERNAL RULE", "meaning": "Rule used by current version for evaluation logic."},
    ]

    return {
        "rows": rows,
        "legend": legend,
    }


def run_engineering_validation(project_data):

    foundation_width = project_data["foundation_width"]
    foundation_length = project_data["foundation_length"]
    column_capacity = project_data["column_capacity"]
    soil_capacity = project_data["soil_capacity"]
    num_floors = project_data["num_floors"]
    building_width = project_data["building_width"]
    building_length = project_data["building_length"]

    floor_area = building_width * building_length
    total_load = project_data.get("total_load")
    if total_load is None:
        total_load = floor_area * LOAD_FACTOR_KN_M2 * num_floors

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
    from trust_layer import run_trust_layer

    validation_result = run_structural_validation(
        foundation_width,
        foundation_length,
        column_capacity,
        total_load,
        soil_capacity
    )

    validation_result = _normalize_validation_status(validation_result)

    scenario_result = run_scenario_exploration(
        engineering_load_per_storey,
        num_floors,
        foundation_width,
        foundation_length,
        column_capacity,
        soil_capacity
    )

    sensitivity_result = run_sensitivity_analysis(
        engineering_load_per_storey,
        num_floors,
        foundation_width,
        foundation_length,
        column_capacity,
        soil_capacity
    )

    prebim_result = run_prebim_validation(
        engineering_load_per_storey,
        num_floors,
        foundation_width,
        foundation_length,
        column_capacity,
        soil_capacity
    )

    trust_result = run_trust_layer(input_payload, validation_result)
    trust_result["input_reliability"] = _build_input_reliability(project_data, input_payload)

    return {
        "validation": validation_result,
        "scenario": scenario_result,
        "sensitivity": sensitivity_result,
        "prebim": prebim_result,
        "input": input_payload,
        "trust": trust_result,
    }


TRUST_CSS = """
<style>
.tl-section {
    border: 1px solid #e0e0de;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 12px;
    font-family: 'DM Mono', monospace;
}
.tl-header {
    background: #2a2a2a;
    color: #fff;
    padding: 8px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.tl-header-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .08em;
    text-transform: uppercase;
}
.tl-header-badge {
    font-size: 10px;
    color: #aaa;
    letter-spacing: .06em;
}
.tl-body {
    background: #fff;
    padding: 12px 16px;
}
.tl-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 5px;
    font-size: 11px;
    gap: 12px;
}
.tl-key { color: #aaa; }
.tl-val { font-weight: 500; color: #222; text-align: right; }
.tl-divider { border: none; border-top: 1px solid #f0f0ee; margin: 8px 0; }

.tl-verdict-CONSISTENT { color: #3a7d44; font-weight: 700; }
.tl-verdict-MISMATCH { color: #b07d00; font-weight: 700; }
.tl-verdict-NO_REFERENCE { color: #888; font-weight: 700; }
.tl-verdict-REFERENCE_ONLY { color: #7a5b00; font-weight: 700; }

.tl-check-CONSISTENT { color: #3a7d44; font-weight: 700; }
.tl-check-MISMATCH { color: #b07d00; font-weight: 700; }
.tl-check-NO_REFERENCE { color: #888; font-weight: 700; }
.tl-check-REFERENCE_ONLY { color: #7a5b00; font-weight: 700; }

.tl-proximity-SAFE { color: #3a7d44; }
.tl-proximity-APPROACHING { color: #b07d00; }
.tl-proximity-NEAR_LIMIT { color: #b07d00; font-weight: 700; }
.tl-proximity-AT_LIMIT { color: #b07d00; font-weight: 700; }
.tl-proximity-OVER_LIMIT { color: #7a3a3a; font-weight: 700; }

.tl-source-user { color: #2f6f3e; font-weight: 700; }
.tl-source-derived { color: #8b6f00; font-weight: 700; }
.tl-source-assumption { color: #a05c00; font-weight: 700; }
.tl-source-default { color: #555; font-weight: 700; }
.tl-source-rule { color: #444; font-weight: 700; }
</style>
"""


def _render_simple_card(st, title, badge, rows):
    st.markdown(
        f"""
        <div class="tl-section">
          <div class="tl-header">
            <span class="tl-header-label">{title}</span>
            <span class="tl-header-badge">{badge}</span>
          </div>
          <div class="tl-body">
        """,
        unsafe_allow_html=True,
    )

    for key, value, value_class in rows:
        value_class_attr = f" {value_class}" if value_class else ""
        st.markdown(
            f"""
            <div class="tl-row">
              <span class="tl-key">{key}</span>
              <span class="tl-val{value_class_attr}">{value}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div></div>", unsafe_allow_html=True)


def _display_trust_layer(st, trust):

    st.markdown(TRUST_CSS, unsafe_allow_html=True)
    st.markdown("#### Trust Layer")

    tv = trust.get("test_validation", {})
    ea = trust.get("expected_actual", {})
    rv = trust.get("required_values", {})
    ab = trust.get("action_block", {})
    at_ = trust.get("assumption_trace", {})
    bw = trust.get("boundary_warning", {})
    ir = trust.get("input_reliability", {})

    # A. REFERENCE CASE MATCHING
    verdict = _clean_text(tv.get("verdict", "NO_REFERENCE"))
    matched = _clean_text(tv.get("matched_case_id", "—"))
    tag = _clean_text(tv.get("tag", "—"))
    confidence = _clean_text(tv.get("confidence", "LOW"))
    sim_score = _safe_float(tv.get("similarity_score", 0.0), 0.0)

    actual_mode = _clean_text(ea.get("actual_governing_mode", "N/A"))
    reference_mode = _clean_text(ea.get("expected_governing_mode", "N/A"))

    verdict_css = f"tl-verdict-{verdict}"
    _render_simple_card(
        st,
        "A · Reference Case Matching",
        f"CONFIDENCE · {confidence}",
        [
            ("Verdict", verdict, verdict_css),
            ("Matched Reference Case", matched, ""),
            ("Reference Tag", tag, ""),
            ("Similarity Score", f"{sim_score:.3f}", ""),
            ("Actual Governing Mode", actual_mode, ""),
            ("Reference Governing Mode", reference_mode, ""),
            (
                "Note",
                "Reference case shown for similarity only. Actual governing mode is determined from current input.",
                "",
            ),
        ],
    )

    # B. EXPECTED VS ACTUAL
    status_check = _clean_text(ea.get("status_check", "NO_REFERENCE"))
    mode_check = _clean_text(ea.get("mode_check", "NO_REFERENCE"))
    soil_check = _clean_text(ea.get("soil_check", "NO_REFERENCE"))
    column_check = _clean_text(ea.get("column_check", "NO_REFERENCE"))

    _render_simple_card(
        st,
        "B · Expected vs Actual",
        "REFERENCE COMPARISON",
        [
            ("Expected Status", _clean_text(ea.get("expected_status", "N/A")), ""),
            ("Actual Status", _clean_text(ea.get("actual_status", "N/A")), ""),
            ("Status Check", status_check, f"tl-check-{status_check}"),
            ("Expected Governing Mode", _clean_text(ea.get("expected_governing_mode", "N/A")), ""),
            ("Actual Governing Mode", _clean_text(ea.get("actual_governing_mode", "N/A")), ""),
            ("Mode Check", mode_check, f"tl-check-{mode_check}"),
            ("Expected Soil Utilization", _format_num(ea.get("expected_soil_utilization")), ""),
            ("Actual Soil Utilization", _format_num(ea.get("actual_soil_utilization")), ""),
            ("Delta Soil Utilization", _format_delta(ea.get("delta_soil_utilization")), ""),
            ("Soil Check", soil_check, f"tl-check-{soil_check}"),
            ("Expected Column Utilization", _format_num(ea.get("expected_column_utilization")), ""),
            ("Actual Column Utilization", _format_num(ea.get("actual_column_utilization")), ""),
            ("Delta Column Utilization", _format_delta(ea.get("delta_column_utilization")), ""),
            ("Column Check", column_check, f"tl-check-{column_check}"),
        ],
    )

    # C. REQUIRED VALUES
    req_area = rv.get("required_foundation_area_m2", "N/A")
    req_size = _clean_text(rv.get("recommended_size_label", "N/A"))
    req_col = rv.get("required_column_capacity_kN", "N/A")
    soil_u = rv.get("soil_utilization", "N/A")
    col_u = rv.get("column_utilization", "N/A")
    reserve = rv.get("reserve_margin_pct")
    reserve_str = f"{reserve:.1f}%" if reserve is not None else "N/A"

    _render_simple_card(
        st,
        "C · Required Values",
        "FOR ENGINEER USE",
        [
            ("Required Foundation Area", f"{req_area} m²", ""),
            ("Recommended Foundation Size", req_size, ""),
            ("Required Column Capacity", f"{req_col} kN", ""),
            ("Soil Utilization", soil_u, ""),
            ("Column Utilization", col_u, ""),
            ("Reserve Margin", reserve_str, ""),
        ],
    )

    # D. ACTION REQUIRED
    primary = ab.get("primary_action")
    all_actions = ab.get("all_actions", [])

    st.markdown("### D · Action Required")

    if not all_actions and primary is None:
        st.info("NO_ACTION — No corrective action required")
    else:
        if primary is not None:
            primary_action = _clean_text(primary.get("action", "N/A"))
            primary_detail = _clean_text(primary.get("detail", "N/A"))
            st.info(f"{primary_action} — {primary_detail}")

        extra_actions = all_actions[1:] if len(all_actions) > 1 else []
        for idx, act in enumerate(extra_actions, start=2):
            action_name = _clean_text(act.get("action", "N/A"))
            action_detail = _clean_text(act.get("detail", "N/A"))
            st.write(f"Step {idx}: {action_name} — {action_detail}")

    # E. ASSUMPTIONS
    _render_simple_card(
        st,
        "E · Assumptions",
        "CALCULATION BASIS",
        [
            ("Storeys", at_.get("storeys", "N/A"), ""),
            ("Load per Storey", f"{at_.get('load_per_storey_kN', 'N/A')} kN", ""),
            ("Load Factor", f"{at_.get('load_factor_kN_m2', 'N/A')} kN/m²", ""),
            ("Total Load", f"{at_.get('total_load_kN', 'N/A')} kN", ""),
            ("Soil Capacity", f"{at_.get('soil_capacity_kN_m2', 'N/A')} kN/m²", ""),
            (
                "Foundation Size",
                f"{at_.get('foundation_width_m', 'N/A')} × {at_.get('foundation_length_m', 'N/A')} m",
                "",
            ),
            ("Foundation Area", f"{at_.get('foundation_area_m2', 'N/A')} m²", ""),
            ("Column Capacity", f"{at_.get('column_capacity_kN', 'N/A')} kN", ""),
            ("Tolerance Rule", _clean_text(at_.get("tolerance_rule", "N/A")), ""),
            ("Load Basis", _clean_text(at_.get("load_basis", "N/A")), ""),
        ],
    )

    # F. BOUNDARY WARNING
    proximity = _clean_text(bw.get("proximity", "SAFE"))
    proximity_detail = _clean_text(bw.get("proximity_detail", ""))
    warning_count = bw.get("warning_count", 0)
    warnings = bw.get("warnings", [])
    margin = bw.get("margin_to_limit", "N/A")

    proximity_css = f"tl-proximity-{proximity}"
    _render_simple_card(
        st,
        "F · Sensitivity / Boundary Warning",
        f"WARNINGS · {warning_count}",
        [
            ("Proximity to Limit", proximity, proximity_css),
            ("Margin to Limit", margin, ""),
            ("Detail", proximity_detail, ""),
        ],
    )

    if warnings:
        for w in warnings:
            scenario = _clean_text(w.get("scenario", ""))
            impact = _clean_text(w.get("impact", ""))
            detail = _clean_text(w.get("detail", ""))
            st.warning(f"{scenario} → {impact} | {detail}")
    else:
        st.caption("No boundary warnings detected.")

    # G. INPUT RELIABILITY
    reliability_rows = []
    for row in ir.get("rows", []):
        label = _clean_text(row.get("label", "N/A"))
        source = _clean_text(row.get("source", "N/A"))
        value_display = _clean_text(row.get("value_display", "N/A"))
        reliability_rows.append(
            (
                label,
                f"{source} — {value_display}",
                row.get("source_class", ""),
            )
        )

    if reliability_rows:
        _render_simple_card(
            st,
            "G · Input Reliability / Data Source",
            "SOURCE FLAGS",
            reliability_rows,
        )

        legend_lines = []
        for item in ir.get("legend", []):
            legend_label = _clean_text(item.get("label", "N/A"))
            legend_meaning = _clean_text(item.get("meaning", "N/A"))
            legend_lines.append(f"- {legend_label}: {legend_meaning}")

        if legend_lines:
            st.caption(" | ".join(legend_lines))


def display_validation_results(st, results):

    validation = results["validation"]
    prebim = results["prebim"]
    input_data = results["input"]
    trust = results.get("trust", {})
    status = validation["status"]
    column_util = validation["column_utilization"]
    soil_util = validation["soil_utilization"]
    governing_mode = validation["governing_mode"]
    soil_pressure = validation.get("soil_pressure", prebim.get("soil_pressure", 1.0))

    st.markdown(
        """
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
        """,
        unsafe_allow_html=True,
    )

    if status == "FAIL":
        status_icon = "✗ FAIL — Redesign required"
    elif status == "PASS":
        status_icon = "✓ PASS — Within limits"
    else:
        status_icon = "⚠ WARNING"

    critical_util = max(column_util, soil_util)
    design_reserve = (1 - critical_util) * 100

    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True,
    )

    floor_area = input_data["building_width"] * input_data["building_length"]
    total_load = input_data["total_load"]
    foundation_area = input_data["foundation_width"] * input_data["foundation_length"]
    required_area = total_load / input_data["soil_capacity"] if input_data["soil_capacity"] > 0 else 0
    load_factor = LOAD_FACTOR_KN_M2

    col_util_calc = total_load / input_data["column_capacity"] if input_data["column_capacity"] > 0 else 0
    soil_util_calc = (
        total_load / (foundation_area * input_data["soil_capacity"])
        if foundation_area > 0 and input_data["soil_capacity"] > 0
        else 0
    )
    soil_pres_calc = total_load / foundation_area if foundation_area > 0 else 0

    with st.expander("▸ Calculation Path", expanded=False):
        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

    with st.expander("▸ Validation Detail", expanded=False):
        import pandas as pd

        c1, c2 = st.columns(2)
        with c1:
            st.caption("Pre-BIM Check")
            st.markdown(
                f"""
                <table style="font-size:11px;width:100%;font-family:'DM Mono',monospace">
                  <tr><td style="color:#aaa">Total Load</td><td style="font-weight:400">{prebim['total_load']} kN</td></tr>
                  <tr><td style="color:#aaa">Soil Pressure</td><td style="font-weight:400">{prebim['soil_pressure']} kN/m²</td></tr>
                  <tr><td style="color:#aaa">Foundation Area</td><td style="font-weight:400">{prebim['foundation_area']} m²</td></tr>
                  <tr><td style="color:#aaa">Required Area</td><td style="font-weight:400">{prebim['required_area']} m²</td></tr>
                  <tr><td style="color:#aaa">Status</td><td style="font-weight:400">{prebim['status']}</td></tr>
                </table>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            total_load_v = results["input"]["total_load"]
            col_capacity = results["input"]["column_capacity"]
            soil_cap = results["input"]["soil_capacity"]
            column_sf = col_capacity / total_load_v if total_load_v > 0 else float("inf")
            soil_sf = soil_cap / soil_pressure if soil_pressure > 0 else float("inf")
            col_margin = validation["column_margin"]
            soil_margin = validation["soil_margin"]

            st.caption("Safety Factors & Margins")
            st.markdown(
                f"""
                <table style="font-size:11px;width:100%;font-family:'DM Mono',monospace">
                  <tr><td style="color:#aaa">Column Safety Factor</td><td style="font-weight:400">{column_sf:.4f}</td></tr>
                  <tr><td style="color:#aaa">Soil Safety Factor</td><td style="font-weight:400">{soil_sf:.4f}</td></tr>
                  <tr><td style="color:#aaa">Column Margin (kN)</td><td style="font-weight:400">{col_margin:.2f}</td></tr>
                  <tr><td style="color:#aaa">Soil Margin (kN/m²)</td><td style="font-weight:400">{soil_margin:.2f}</td></tr>
                </table>
                """,
                unsafe_allow_html=True,
            )

        st.caption("Scenario Exploration")
        st.dataframe(pd.DataFrame(results["scenario"]), use_container_width=True)

        st.caption("Sensitivity Analysis")
        st.dataframe(pd.DataFrame(results["sensitivity"]), use_container_width=True)

    st.divider()

    if trust:
        _display_trust_layer(st, trust)


def extract_validation_for_decision(results):
    validation = results["validation"]
    input_data = results["input"]
    return {
        "total_load": input_data["total_load"],
        "column_utilization": validation["column_utilization"],
        "soil_utilization": validation["soil_utilization"],
        "column_margin": validation["column_margin"],
        "soil_margin": validation["soil_margin"],
        "soil_pressure": validation.get("soil_pressure"),
        "governing_mode": validation["governing_mode"],
        "status": validation["status"],
        "trust": results.get("trust"),
    }