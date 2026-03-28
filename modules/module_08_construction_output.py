# ============================================
# TRIPLE BOT V9.9.5
# Module 08 — Construction Output System
# FULL FILE REPLACEMENT
# FIX:
# - NO_ACTION wording / summary / time basis only
# - no logic change
# ============================================

import inspect
import io
import csv
import json
import re
import html


PASS_LIMIT = 1.010
DEFAULT_FOUNDATION_DEPTH = 0.4


def _calc_status(su, cu):
    if su <= PASS_LIMIT and cu <= PASS_LIMIT:
        if su > 1.000 or cu > 1.000:
            return "PASS (Engineering Tolerance)"
        return "PASS"
    return "FAIL"


def _classify_design(su, cu):
    try:
        su = float(su)
        cu = float(cu)
    except (TypeError, ValueError):
        return "N/A", "—"

    max_util = max(su, cu)

    if max_util <= 0.85:
        return "CONSERVATIVE", "Significant safety margin on both soil and column"
    elif max_util <= 1.0:
        return "EFFICIENT", "Near-optimal use of structural capacity"
    elif max_util <= PASS_LIMIT:
        return "OPTIMIZED", "At capacity limit — within engineering tolerance ≤1.010"
    else:
        return "OVER-LIMIT", "Exceeds engineering tolerance — redesign required"


def _interpret_utilization(val, label="utilization"):
    try:
        v = float(val)
    except (TypeError, ValueError):
        return f"{val} — {label}"

    if v <= 0.85:
        return f"{val:.3f} — safe with remaining margin"
    elif v <= 1.0:
        return f"{val:.3f} — near capacity limit"
    elif v <= PASS_LIMIT:
        return f"{val:.3f} — at capacity limit (within engineering tolerance)"
    else:
        return f"{val:.3f} — exceeds capacity limit"


_REGION_CURRENCY = {
    "Thailand": {"currency": "THB", "symbol": ""},
    "China": {"currency": "CNY", "symbol": "¥"},
    "United States": {"currency": "USD", "symbol": "$"},
}


def _get_currency_info(project_data):
    region = project_data.get("region", "Thailand")
    info = _REGION_CURRENCY.get(region, _REGION_CURRENCY["Thailand"])
    return info["currency"], info["symbol"], region


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _sanitize_filename(text):
    raw = str(text or "project").strip()
    raw = re.sub(r"\s+", "_", raw)
    raw = re.sub(r"[^A-Za-z0-9_\-]", "", raw)
    return raw or "project"


def _escape_html_text(value):
    if value is None:
        return "—"
    return html.escape(str(value))


def _is_no_action_case(seq_path, final_status):
    if "PASS" not in str(final_status):
        return False

    if not seq_path:
        return True

    if len(seq_path) == 1:
        action = str(seq_path[0].get("action", "")).upper().strip()
        return action == "NO_ACTION"

    return False


def _normalize_display_status(raw_status, soil_util, column_util):
    su = _safe_float(soil_util, None)
    cu = _safe_float(column_util, None)

    if su is None or cu is None:
        text = str(raw_status).strip().upper()
        if text in ("SAFE", "WARNING"):
            return "PASS"
        return str(raw_status)

    calc = _calc_status(su, cu)
    if calc == "FAIL":
        return "FAIL"
    if calc == "PASS (Engineering Tolerance)":
        return "PASS (Engineering Tolerance)"
    return "PASS"


def _build_display_reasoning(reasoning, seq_path, original, corrected, final_status):
    primary_reason = str(reasoning.get("primary_reason", "—")).strip()
    governing_logic = str(reasoning.get("governing_explanation", "—")).strip()
    confidence = str(reasoning.get("confidence_in_selected_action", "—")).strip()

    if _is_no_action_case(seq_path, final_status):
        corr_su = _safe_float(corrected.get("soil_utilization"))
        corr_cu = _safe_float(corrected.get("column_utilization"))

        primary_reason = "No corrective action required."
        governing_logic = (
            f"Current design already satisfies the engineering limit "
            f"(soil utilization {corr_su:.3f} and column utilization {corr_cu:.3f} "
            f"are both within ≤ {PASS_LIMIT:.3f})."
        )
        confidence = confidence if confidence and confidence != "—" else "HIGH"

    return (
        primary_reason if primary_reason else "—",
        governing_logic if governing_logic else "—",
        confidence if confidence else "—",
    )


def _build_physical_explanation(original, corrected, seq_path, total_load, soil_cap, final_status):
    orig_fw = _safe_float(original.get("foundation_width"))
    orig_fl = _safe_float(original.get("foundation_length"))
    orig_cap = _safe_float(original.get("column_capacity"))
    orig_sp = _safe_float(original.get("soil_pressure"))
    orig_su = _safe_float(original.get("soil_utilization"))
    orig_cu = _safe_float(original.get("column_utilization"))
    orig_area = _safe_float(original.get("foundation_area"))

    corr_fw = _safe_float(corrected.get("foundation_width"))
    corr_fl = _safe_float(corrected.get("foundation_length"))
    corr_cap = _safe_float(corrected.get("column_capacity"))
    corr_sp = _safe_float(corrected.get("soil_pressure"))
    corr_su = _safe_float(corrected.get("soil_utilization"))
    corr_cu = _safe_float(corrected.get("column_utilization"))
    corr_area = _safe_float(corrected.get("foundation_area"))

    total_load_f = _safe_float(total_load)
    soil_cap_f = _safe_float(soil_cap)

    def _calc_pressure(width, length):
        area = width * length
        if area <= 0:
            return float("inf")
        return total_load_f / area

    def _step_snapshot(step):
        step_fw = _safe_float(step.get("foundation_width"))
        step_fl = _safe_float(step.get("foundation_length"))
        step_cap = _safe_float(step.get("column_capacity"))
        step_su = _safe_float(step.get("soil_utilization"))
        step_cu = _safe_float(step.get("column_utilization"))
        step_sp = _calc_pressure(step_fw, step_fl)
        return {
            "foundation_width": step_fw,
            "foundation_length": step_fl,
            "column_capacity": step_cap,
            "soil_utilization": step_su,
            "column_utilization": step_cu,
            "soil_pressure": step_sp,
        }

    first_action = seq_path[0]["action"] if seq_path else None
    n_steps = len(seq_path)

    if n_steps >= 2:
        step1 = _step_snapshot(seq_path[0])
        step2 = _step_snapshot(seq_path[1])
        step1_action = str(seq_path[0].get("action", "")).upper().strip()
        step2_action = str(seq_path[1].get("action", "")).upper().strip()

        line1 = (
            f"Initial design failed in both checks: soil utilization = {orig_su:.3f} "
            f"and column utilization = {orig_cu:.3f}."
        )

        if step1_action == "COLUMN_UPGRADE" and step2_action == "FOUNDATION_INCREASE":
            line2 = (
                f"Step 1 upgraded column capacity from {orig_cap:.0f} to {step1['column_capacity']:.0f} kN, "
                f"reducing column utilization from {orig_cu:.3f} to {step1['column_utilization']:.3f}."
            )
            line3 = (
                f"Step 2 increased foundation from {step1['foundation_width']:.2f} × {step1['foundation_length']:.2f} m "
                f"to {step2['foundation_width']:.2f} × {step2['foundation_length']:.2f} m, reducing soil pressure from "
                f"{step1['soil_pressure']:.3f} to {step2['soil_pressure']:.3f} kN/m²; final utilizations = "
                f"soil {step2['soil_utilization']:.3f}, column {step2['column_utilization']:.3f} → {final_status}."
            )
            return line1, line2, line3

        if step1_action == "FOUNDATION_INCREASE" and step2_action == "COLUMN_UPGRADE":
            line2 = (
                f"Step 1 increased foundation from {orig_fw:.2f} × {orig_fl:.2f} m "
                f"to {step1['foundation_width']:.2f} × {step1['foundation_length']:.2f} m, reducing soil pressure from "
                f"{orig_sp:.3f} to {step1['soil_pressure']:.3f} kN/m²."
            )
            line3 = (
                f"Step 2 upgraded column capacity from {orig_cap:.0f} to {step2['column_capacity']:.0f} kN, "
                f"reducing column utilization from {step1['column_utilization']:.3f} to {step2['column_utilization']:.3f}; "
                f"final utilizations = soil {step2['soil_utilization']:.3f}, column {step2['column_utilization']:.3f} "
                f"→ {final_status}."
            )
            return line1, line2, line3

        line2 = (
            f"Step 1 applied {step1_action}: foundation = {step1['foundation_width']:.2f} × "
            f"{step1['foundation_length']:.2f} m, column capacity = {step1['column_capacity']:.0f} kN."
        )
        line3 = (
            f"Step 2 applied {step2_action}: final utilizations = soil {step2['soil_utilization']:.3f}, "
            f"column {step2['column_utilization']:.3f} → {final_status}."
        )
        return line1, line2, line3

    if first_action == "FOUNDATION_INCREASE":
        line1 = (
            f"Soil governs the failure: applied load {total_load_f:.1f} kN over "
            f"{orig_area:.3f} m² produced soil pressure {orig_sp:.3f} kN/m² "
            f"against soil capacity {soil_cap_f:.3f} kN/m²."
        )
        line2 = (
            f"Foundation was increased from {orig_fw:.2f} × {orig_fl:.2f} m "
            f"to {corr_fw:.2f} × {corr_fl:.2f} m, increasing area to {corr_area:.3f} m²."
        )
        line3 = (
            f"Corrected soil pressure = {corr_sp:.3f} kN/m², soil utilization = {corr_su:.3f}, "
            f"column utilization = {corr_cu:.3f} → {final_status}."
        )
        return line1, line2, line3

    if first_action == "COLUMN_UPGRADE":
        line1 = (
            f"Column governs the failure: total load {total_load_f:.1f} kN exceeded "
            f"original column capacity {orig_cap:.0f} kN, producing column utilization {orig_cu:.3f}."
        )
        line2 = (
            f"Foundation remained unchanged at {orig_fw:.2f} × {orig_fl:.2f} m because "
            f"soil utilization {orig_su:.3f} was within the accepted limit."
        )
        line3 = (
            f"Column capacity was upgraded to {corr_cap:.0f} kN; corrected column utilization = {corr_cu:.3f}, "
            f"soil utilization = {corr_su:.3f} → {final_status}."
        )
        return line1, line2, line3

    line1 = "Initial design is within the accepted engineering limit without corrective action."
    line2 = (
        f"Soil utilization = {orig_su:.3f}, column utilization = {orig_cu:.3f}, "
        f"both within ≤ {PASS_LIMIT:.3f}."
    )
    line3 = (
        f"Foundation remains {orig_fw:.2f} × {orig_fl:.2f} m and column capacity remains "
        f"{orig_cap:.0f} kN."
    )
    return line1, line2, line3


def _build_design(
    foundation_width,
    foundation_length,
    total_load,
    soil_capacity,
    column_capacity,
    status_override=None
):
    foundation_area = foundation_width * foundation_length
    soil_pressure = total_load / foundation_area if foundation_area > 0 else float("inf")
    soil_utilization = soil_pressure / soil_capacity if soil_capacity > 0 else float("inf")
    column_utilization = total_load / column_capacity if column_capacity > 0 else float("inf")
    status = _calc_status(soil_utilization, column_utilization)
    if status_override is not None:
        status = status_override
    return {
        "foundation_width": round(foundation_width, 3),
        "foundation_length": round(foundation_length, 3),
        "foundation_area": round(foundation_area, 3),
        "soil_pressure": round(soil_pressure, 3),
        "soil_utilization": round(soil_utilization, 3),
        "column_capacity": round(column_capacity, 3),
        "column_utilization": round(column_utilization, 3),
        "status": status
    }


def _apply_foundation_increase(total_load, soil_capacity, column_capacity):
    required_area = total_load / soil_capacity if soil_capacity > 0 else float("inf")
    new_size = round(required_area ** 0.5, 2)
    corrected_design = _build_design(
        foundation_width=new_size,
        foundation_length=new_size,
        total_load=total_load,
        soil_capacity=soil_capacity,
        column_capacity=column_capacity
    )
    return corrected_design, required_area, new_size


def _apply_column_upgrade(base_design, total_load, target_capacity=None):
    current_capacity = base_design.get("column_capacity", 0.0)
    if target_capacity is None:
        target_capacity = max(current_capacity, total_load)
    upgraded_capacity = round(target_capacity, 2)
    corrected_design = dict(base_design)
    corrected_design["column_capacity"] = round(upgraded_capacity, 3)
    corrected_design["column_utilization"] = round(
        total_load / upgraded_capacity if upgraded_capacity > 0 else float("inf"), 3
    )
    corrected_design["status"] = _calc_status(
        corrected_design["soil_utilization"],
        corrected_design["column_utilization"]
    )
    return corrected_design, upgraded_capacity


def _build_step_record(step_number, action, design, note):
    return {
        "step_number": step_number,
        "action": action,
        "note": note,
        "foundation_width": round(design.get("foundation_width", 0.0), 3),
        "foundation_length": round(design.get("foundation_length", 0.0), 3),
        "column_capacity": round(design.get("column_capacity", 0.0), 3),
        "soil_utilization": round(design.get("soil_utilization", 0.0), 3),
        "column_utilization": round(design.get("column_utilization", 0.0), 3),
        "status": design.get("status", "N/A")
    }


def _estimate_column_upgrade_cost(original_capacity, final_capacity):
    increase_kn = max(0.0, final_capacity - original_capacity)
    rate_thb_per_kn = 10.0
    cost = increase_kn * rate_thb_per_kn
    return {
        "column_upgrade_capacity_increase_kn": round(increase_kn, 3),
        "column_upgrade_rate_thb_per_kn": rate_thb_per_kn,
        "column_upgrade_cost_thb": round(cost, 0)
    }


def _estimate_column_upgrade_time(original_capacity, final_capacity):
    increase_kn = max(0.0, final_capacity - original_capacity)
    days = 1.0 if increase_kn > 0 else 0.0
    return {
        "column_upgrade_capacity_increase_kn": round(increase_kn, 3),
        "column_upgrade_phase_days": days
    }


def _build_option_entry(key, label, design, total_cost_thb, total_days, is_selected=False, note=""):
    return {
        "key": key,
        "label": label,
        "status": design.get("status", "N/A"),
        "total_cost_thb": round(_safe_float(total_cost_thb, 0.0), 0),
        "total_days": round(_safe_float(total_days, 0.0), 1),
        "soil_utilization": round(_safe_float(design.get("soil_utilization", 0.0)), 3),
        "column_utilization": round(_safe_float(design.get("column_utilization", 0.0)), 3),
        "foundation_width": round(_safe_float(design.get("foundation_width", 0.0)), 3),
        "foundation_length": round(_safe_float(design.get("foundation_length", 0.0)), 3),
        "column_capacity": round(_safe_float(design.get("column_capacity", 0.0)), 3),
        "is_selected": bool(is_selected),
        "note": note,
    }


def _build_option_ranking_summary(option_entries):
    if not option_entries:
        return {
            "options": [],
            "pass_options": [],
            "cheapest_overall": None,
            "fastest_overall": None,
            "best_pass_option": None,
            "cheapest": None,
            "fastest": None,
            "balanced": None,
        }

    all_options = list(option_entries)
    pass_options = [o for o in all_options if "PASS" in str(o.get("status", "")).upper()]

    cheapest_overall = min(
        all_options,
        key=lambda o: (o["total_cost_thb"], o["total_days"], o["label"])
    )
    fastest_overall = min(
        all_options,
        key=lambda o: (o["total_days"], o["total_cost_thb"], o["label"])
    )

    if pass_options:
        best_pass_option = min(
            pass_options,
            key=lambda o: (
                o["total_cost_thb"],
                o["total_days"],
                0 if o.get("is_selected") else 1,
                o["label"],
            )
        )
    else:
        best_pass_option = None

    return {
        "options": all_options,
        "pass_options": pass_options,
        "cheapest_overall": cheapest_overall,
        "fastest_overall": fastest_overall,
        "best_pass_option": best_pass_option,
        "cheapest": cheapest_overall,
        "fastest": fastest_overall,
        "balanced": best_pass_option,
    }


def _build_reliability_rows(validation_package, foundation_depth_m, cost_estimate):
    trust = validation_package.get("trust", {}) or {}
    input_reliability = trust.get("input_reliability", {}) or {}
    base_rows = list(input_reliability.get("rows", []))

    normalized_rows = []
    seen_labels = set()

    def _add_row(label, value_display, source, note):
        key = str(label).strip().lower()
        if key in seen_labels:
            return
        seen_labels.add(key)
        normalized_rows.append({
            "label": label,
            "value_display": value_display,
            "source": source,
            "note": note,
        })

    for row in base_rows:
        _add_row(
            row.get("label", "—"),
            row.get("value_display", "—"),
            row.get("source", "—"),
            row.get("note", "—"),
        )

    _add_row(
        "Foundation Depth",
        f"{foundation_depth_m:.3f} m",
        "SYSTEM DEFAULT",
        "Default depth used for preliminary BOQ and cost estimate.",
    )

    concrete_rate = cost_estimate.get("concrete_rate_thb_per_m3")
    excavation_rate = cost_estimate.get("excavation_rate_thb_per_m3")
    reinforcement_rate = cost_estimate.get("reinforcement_rate_thb_per_kg")
    column_rate = cost_estimate.get("column_upgrade_rate_thb_per_kn")

    any_specific_rate = False

    if concrete_rate is not None:
        _add_row(
            "Concrete Rate",
            f"{_safe_float(concrete_rate):.0f} THB/m³",
            "INTERNAL BENCHMARK",
            "Internal benchmark rate used for preliminary concrete cost.",
        )
        any_specific_rate = True

    if excavation_rate is not None:
        _add_row(
            "Excavation Rate",
            f"{_safe_float(excavation_rate):.0f} THB/m³",
            "INTERNAL BENCHMARK",
            "Internal benchmark rate used for preliminary excavation cost.",
        )
        any_specific_rate = True

    if reinforcement_rate is not None:
        _add_row(
            "Reinforcement Rate",
            f"{_safe_float(reinforcement_rate):.2f} THB/kg",
            "INTERNAL BENCHMARK",
            "Internal benchmark rate used for preliminary reinforcement cost.",
        )
        any_specific_rate = True

    if column_rate is not None:
        _add_row(
            "Column Upgrade Rate",
            f"{_safe_float(column_rate):.2f} THB/kN",
            "INTERNAL BENCHMARK",
            "Internal benchmark rate used for deterministic column upgrade estimate.",
        )
        any_specific_rate = True

    if not any_specific_rate:
        _add_row(
            "Cost Rates",
            "Internal benchmark",
            "INTERNAL BENCHMARK",
            "Preliminary cost engine uses fixed internal benchmark rates.",
        )

    return normalized_rows


def _build_export_payload(output_package, project_data):
    validation = output_package.get("validation", {}) or {}
    decision = output_package.get("decision", {}) or {}
    reasoning = output_package.get("reasoning", {}) or {}
    reliability_rows = output_package.get("input_reliability_rows", []) or []
    option_summary = output_package.get("option_ranking_summary", {}) or {}

    payload = {
        "project": {
            "project_name": project_data.get("project_name", "—"),
            "region": project_data.get("region", "Thailand"),
            "building_type": project_data.get("building_type", "—"),
            "building_width_m": project_data.get("building_width"),
            "building_length_m": project_data.get("building_length"),
            "num_floors": project_data.get("num_floors"),
        },
        "inputs": {
            "foundation_width_m": project_data.get("foundation_width"),
            "foundation_length_m": project_data.get("foundation_length"),
            "column_capacity_kN": project_data.get("column_capacity"),
            "soil_capacity_kN_m2": project_data.get("soil_capacity"),
            "engineering_load_per_storey_kN": project_data.get("engineering_load_per_storey"),
            "total_load_kN": project_data.get("total_load"),
        },
        "initial_validation": {
            "status": validation.get("status"),
            "governing_mode": validation.get("governing_mode"),
            "soil_utilization": validation.get("soil_utilization"),
            "column_utilization": validation.get("column_utilization"),
            "soil_pressure_kN_m2": validation.get("soil_pressure"),
            "soil_margin": validation.get("soil_margin"),
            "column_margin": validation.get("column_margin"),
        },
        "corrected_design": output_package.get("corrected_design", {}),
        "sequential_path": output_package.get("sequential_path", []),
        "boq": output_package.get("boq_recommended", {}),
        "cost_estimate": output_package.get("cost_estimate", {}),
        "time_estimate": output_package.get("time_estimate", {}),
        "decision": {
            "option_type": decision.get("option_type"),
            "description": decision.get("description"),
        },
        "reasoning": reasoning,
        "option_ranking_summary": option_summary,
        "reliability": reliability_rows,
    }

    return payload


def _build_csv_export_text(export_payload):
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["TRIPLE BOT V9.9.5 STRUCTURED EXPORT"])
    writer.writerow([])

    simple_sections = [
        ("PROJECT", export_payload.get("project", {})),
        ("INPUTS", export_payload.get("inputs", {})),
        ("INITIAL VALIDATION", export_payload.get("initial_validation", {})),
        ("CORRECTED DESIGN", export_payload.get("corrected_design", {})),
        ("BOQ", export_payload.get("boq", {})),
        ("COST ESTIMATE", export_payload.get("cost_estimate", {})),
        ("TIME ESTIMATE", export_payload.get("time_estimate", {})),
        ("DECISION", export_payload.get("decision", {})),
        ("REASONING", export_payload.get("reasoning", {})),
    ]

    for section_name, section_data in simple_sections:
        writer.writerow([section_name])
        writer.writerow(["Field", "Value"])
        for key, value in section_data.items():
            writer.writerow([key, value])
        writer.writerow([])

    writer.writerow(["SEQUENTIAL PATH"])
    writer.writerow([
        "step_number",
        "action",
        "foundation_width",
        "foundation_length",
        "column_capacity",
        "soil_utilization",
        "column_utilization",
        "status",
        "note",
    ])
    for step in export_payload.get("sequential_path", []):
        writer.writerow([
            step.get("step_number"),
            step.get("action"),
            step.get("foundation_width"),
            step.get("foundation_length"),
            step.get("column_capacity"),
            step.get("soil_utilization"),
            step.get("column_utilization"),
            step.get("status"),
            step.get("note"),
        ])
    writer.writerow([])

    option_summary = export_payload.get("option_ranking_summary", {}) or {}
    writer.writerow(["OPTION RANKING SUMMARY"])
    writer.writerow([
        "key",
        "label",
        "status",
        "total_cost_thb",
        "total_days",
        "soil_utilization",
        "column_utilization",
        "foundation_width",
        "foundation_length",
        "column_capacity",
        "is_selected",
        "note",
    ])
    for option in option_summary.get("options", []):
        writer.writerow([
            option.get("key"),
            option.get("label"),
            option.get("status"),
            option.get("total_cost_thb"),
            option.get("total_days"),
            option.get("soil_utilization"),
            option.get("column_utilization"),
            option.get("foundation_width"),
            option.get("foundation_length"),
            option.get("column_capacity"),
            option.get("is_selected"),
            option.get("note"),
        ])
    writer.writerow([])

    writer.writerow(["RANKING HIGHLIGHTS"])
    writer.writerow(["category", "label", "status", "total_cost_thb", "total_days"])
    for category in ("cheapest_overall", "fastest_overall", "best_pass_option"):
        item = option_summary.get(category)
        if item:
            writer.writerow([
                category,
                item.get("label"),
                item.get("status"),
                item.get("total_cost_thb"),
                item.get("total_days"),
            ])
    writer.writerow([])

    writer.writerow(["INPUT RELIABILITY"])
    writer.writerow(["label", "value_display", "source", "note"])
    for row in export_payload.get("reliability", []):
        writer.writerow([
            row.get("label"),
            row.get("value_display"),
            row.get("source"),
            row.get("note"),
        ])
    writer.writerow([])

    return buffer.getvalue()


def _build_ranking_summary_html(option_summary, currency_symbol, currency_code):
    ranking_options = option_summary.get("options", []) or []
    if not ranking_options:
        return ""

    rows_html = ""
    for option in ranking_options:
        row_class = ' class="selected"' if option.get("is_selected") else ""
        label = _escape_html_text(option.get("label", "—"))
        status = _escape_html_text(option.get("status", "—"))
        cost_val = int(_safe_float(option.get("total_cost_thb", 0), 0))
        time_val = _safe_float(option.get("total_days", 0), 0)
        soil_val = _safe_float(option.get("soil_utilization", 0), 0)
        column_val = _safe_float(option.get("column_utilization", 0), 0)
        note = _escape_html_text(option.get("note", "—"))

        rows_html += (
            f'<tr{row_class}>'
            f'<td>{label}</td>'
            f'<td>{status}</td>'
            f'<td>{currency_symbol}{cost_val:,} {currency_code}</td>'
            f'<td>{time_val:.1f} d</td>'
            f'<td>{soil_val:.3f}</td>'
            f'<td>{column_val:.3f}</td>'
            f'<td>{note}</td>'
            f'</tr>'
        )

    cheapest = option_summary.get("cheapest_overall")
    fastest = option_summary.get("fastest_overall")
    best_pass = option_summary.get("best_pass_option")

    chips_html = ""
    if cheapest:
        chips_html += (
            f'<span class="rank-chip">Cheapest Overall: '
            f'{_escape_html_text(cheapest.get("label", "—"))}</span>'
        )
    if fastest:
        chips_html += (
            f'<span class="rank-chip">Fastest Overall: '
            f'{_escape_html_text(fastest.get("label", "—"))}</span>'
        )
    if best_pass:
        chips_html += (
            f'<span class="rank-chip">Best PASS Option: '
            f'{_escape_html_text(best_pass.get("label", "—"))}</span>'
        )

    return (
        '<div class="rank-wrap">'
        '<div class="rank-head">Decision Option Ranking Summary</div>'
        '<table class="to-table">'
        '<tr>'
        '<th>Option</th>'
        '<th>Status</th>'
        '<th>Cost</th>'
        '<th>Time</th>'
        '<th>Soil Util.</th>'
        '<th>Column Util.</th>'
        '<th>Note</th>'
        '</tr>'
        f'{rows_html}'
        '</table>'
        f'<div style="margin-top:6px">{chips_html}</div>'
        '</div>'
    )


def _build_reliability_summary_html(reliability_rows):
    if not reliability_rows:
        return ""

    rows_html = ""
    for row in reliability_rows:
        rows_html += (
            '<tr>'
            f'<td>{_escape_html_text(row.get("label", "—"))}</td>'
            f'<td>{_escape_html_text(row.get("value_display", "—"))}</td>'
            f'<td>{_escape_html_text(row.get("source", "—"))}</td>'
            f'<td>{_escape_html_text(row.get("note", "—"))}</td>'
            '</tr>'
        )

    return (
        '<div class="rank-wrap">'
        '<div class="rank-head">Input Reliability / Data Source</div>'
        '<table class="to-table">'
        '<tr>'
        '<th>Field</th>'
        '<th>Value</th>'
        '<th>Source</th>'
        '<th>Note</th>'
        '</tr>'
        f'{rows_html}'
        '</table>'
        '</div>'
    )


def _call_report_generator(
    generate_engineering_report,
    final_validation,
    options,
    prebim_original,
    boq_recommended,
    decision,
    cost_estimate,
    time_estimate,
    sequential_path,
    action_outcome,
    next_required_action
):
    try:
        sig = inspect.signature(generate_engineering_report)
        full_kwargs = {
            "result": final_validation,
            "intelligence": options,
            "prebim": prebim_original,
            "boq": boq_recommended,
            "decision": decision,
            "cost_estimate": cost_estimate,
            "time_estimate": time_estimate,
            "sequential_path": sequential_path,
            "action_outcome": action_outcome,
            "next_required_action": next_required_action,
            "region": final_validation.get("region", "Thailand")
        }
        filtered_kwargs = {k: v for k, v in full_kwargs.items() if k in sig.parameters}
        return generate_engineering_report(**filtered_kwargs)
    except Exception:
        return generate_engineering_report(
            final_validation,
            options,
            prebim_original,
            boq_recommended,
            decision,
            cost_estimate=cost_estimate
        )


# ============================================
# CORE RUN
# ============================================

def run_construction_output(decision_package, project_data):
    validation = decision_package["validation"]
    decision = decision_package["decision"]
    options = decision_package.get("options", [])
    reasoning = decision_package.get("reasoning", {})

    total_load = project_data["total_load"]
    soil_capacity = project_data["soil_capacity"]
    num_floors = project_data["num_floors"]
    current_column_capacity = project_data["column_capacity"]
    foundation_width = project_data["foundation_width"]
    foundation_length = project_data["foundation_length"]

    from boq_engine import generate_boq
    from cost_estimate_engine import generate_cost_estimate
    from time_estimate_engine import generate_time_estimate
    from triplebot_diagram_engine import generate_conceptual_diagram
    from triplebot_report_generator import generate_engineering_report
    from pre_bim_validation_engine import run_prebim_validation

    engineering_load_per_storey = project_data.get("engineering_load_per_storey")
    if engineering_load_per_storey is None:
        engineering_load_per_storey = (
            total_load / num_floors if num_floors > 0 else 0.0
        )

    prebim_original = run_prebim_validation(
        engineering_load_per_storey,
        num_floors,
        foundation_width,
        foundation_length,
        current_column_capacity,
        soil_capacity
    )

    original_design = _build_design(
        foundation_width=foundation_width,
        foundation_length=foundation_length,
        total_load=total_load,
        soil_capacity=soil_capacity,
        column_capacity=current_column_capacity,
        status_override=validation.get("status", "N/A")
    )

    corrected_design = dict(original_design)
    corrected_applied = False
    output_note = None
    sequential_path = []
    action_outcome = []
    next_required_action = None
    decision_type = decision.get("option_type") if decision else None

    if decision_type == "FOUNDATION_INCREASE":
        corrected_applied = True
        step1_design, required_area, new_size = _apply_foundation_increase(
            total_load=total_load,
            soil_capacity=soil_capacity,
            column_capacity=current_column_capacity
        )
        corrected_design = step1_design
        output_note = f"Recommended foundation size based on soil capacity: {new_size:.2f} m"
        if decision is not None:
            decision["foundation_size"] = new_size
        sequential_path.append(
            _build_step_record(
                1,
                "FOUNDATION_INCREASE",
                step1_design,
                "Primary correction applied to reduce soil pressure."
            )
        )

        if step1_design["status"] == "PASS":
            action_outcome = [
                "Soil correction successful.",
                "Selected corrective action resolved the identified failure."
            ]
        else:
            if step1_design["column_utilization"] > PASS_LIMIT:
                next_required_action = {
                    "action": "COLUMN_UPGRADE",
                    "reason": f"Column utilization remains {step1_design['column_utilization']:.3f} (> {PASS_LIMIT})."
                }
                step2_design, upgraded_capacity = _apply_column_upgrade(
                    base_design=step1_design,
                    total_load=total_load,
                    target_capacity=total_load
                )
                corrected_design = step2_design
                sequential_path.append(
                    _build_step_record(
                        2,
                        "COLUMN_UPGRADE",
                        step2_design,
                        "Secondary correction applied to resolve remaining column failure."
                    )
                )
                if decision is not None:
                    decision["recommended_capacity"] = upgraded_capacity
                _su2 = step2_design.get("soil_utilization", 9.0)
                _cu2 = step2_design.get("column_utilization", 9.0)
                step2_design["status"] = _calc_status(_su2, _cu2)
                if _su2 <= PASS_LIMIT and _cu2 <= PASS_LIMIT:
                    action_outcome = [
                        "Soil correction successful.",
                        "Secondary action COLUMN_UPGRADE applied.",
                        "Final combined correction achieved PASS."
                    ]
                    next_required_action = None
                else:
                    action_outcome = ["Soil correction insufficient.", "Further redesign required."]
            else:
                action_outcome = [
                    "Primary corrective action applied.",
                    "Identified failure not fully resolved.",
                    "Further action required."
                ]

    elif decision_type == "COLUMN_UPGRADE":
        corrected_applied = True
        step1_design, upgraded_capacity = _apply_column_upgrade(
            base_design=original_design,
            total_load=total_load,
            target_capacity=total_load
        )
        corrected_design = step1_design
        output_note = f"Recommended column capacity based on total load: {upgraded_capacity:.2f} kN"
        if decision is not None:
            decision["recommended_capacity"] = upgraded_capacity
        sequential_path.append(
            _build_step_record(
                1,
                "COLUMN_UPGRADE",
                step1_design,
                "Primary correction applied to resolve column capacity deficiency."
            )
        )

        if step1_design["status"] == "PASS":
            action_outcome = [
                "Column correction successful.",
                "Selected corrective action resolved the identified failure."
            ]
        else:
            if step1_design["column_utilization"] <= 1.0 and step1_design["soil_utilization"] > 1.0:
                next_required_action = {
                    "action": "FOUNDATION_INCREASE",
                    "reason": f"Soil utilization remains {step1_design['soil_utilization']:.3f} (> 1.0)."
                }
                step2_design, required_area, new_size = _apply_foundation_increase(
                    total_load=total_load,
                    soil_capacity=soil_capacity,
                    column_capacity=step1_design["column_capacity"]
                )
                corrected_design = step2_design
                sequential_path.append(
                    _build_step_record(
                        2,
                        "FOUNDATION_INCREASE",
                        step2_design,
                        "Secondary correction applied to resolve remaining soil failure."
                    )
                )
                if decision is not None:
                    decision["foundation_size"] = new_size
                if step2_design["status"] == "PASS":
                    action_outcome = [
                        "Column correction successful.",
                        "Soil still fails.",
                        "Secondary action FOUNDATION_INCREASE applied.",
                        "Final combined correction achieved PASS."
                    ]
                    next_required_action = None
                else:
                    action_outcome = [
                        "Column correction successful.",
                        "Soil still fails.",
                        "Further action required."
                    ]
            else:
                action_outcome = [
                    "Primary corrective action applied.",
                    "Identified failure not fully resolved.",
                    "Further action required."
                ]
    else:
        corrected_design = dict(original_design)
        action_outcome = ["No corrective action required."]

    if corrected_applied:
        _fsu = corrected_design.get("soil_utilization", 9.0)
        _fcu = corrected_design.get("column_utilization", 9.0)
        corrected_design["status"] = _calc_status(_fsu, _fcu)
        if _fsu <= PASS_LIMIT and _fcu <= PASS_LIMIT:
            final_status = "PASS (Sequential Correction)" if len(sequential_path) >= 2 else "PASS (Corrected)"
        else:
            final_status = "FAIL"
    else:
        _fsu = corrected_design.get("soil_utilization", 9.0)
        _fcu = corrected_design.get("column_utilization", 9.0)
        final_status = _calc_status(_fsu, _fcu)

    no_action_case = _is_no_action_case(sequential_path, final_status)

    boq_original = generate_boq(
        foundation_width,
        foundation_length,
        total_load,
        soil_capacity,
        foundation_depth=DEFAULT_FOUNDATION_DEPTH
    )
    boq_recommended = generate_boq(
        corrected_design["foundation_width"],
        corrected_design["foundation_length"],
        total_load,
        soil_capacity,
        foundation_depth=DEFAULT_FOUNDATION_DEPTH
    )
    boq = boq_recommended

    _rgn = project_data.get("region", "Thailand")
    foundation_phase_cost = generate_cost_estimate(boq_recommended, region=_rgn)
    column_cost_info = _estimate_column_upgrade_cost(
        original_design["column_capacity"],
        corrected_design["column_capacity"]
    )
    column_upgrade_cost_thb = column_cost_info["column_upgrade_cost_thb"]
    foundation_total_cost_thb = round(foundation_phase_cost.get("total_cost_thb", 0.0), 0)
    combined_total_cost_thb = round(foundation_total_cost_thb + column_upgrade_cost_thb, 0)

    cost_estimate = dict(foundation_phase_cost)
    cost_estimate["foundation_phase_cost_thb"] = foundation_total_cost_thb
    cost_estimate["column_upgrade_cost_thb"] = column_upgrade_cost_thb
    cost_estimate["combined_total_cost_thb"] = combined_total_cost_thb
    cost_estimate["column_upgrade_capacity_increase_kn"] = column_cost_info["column_upgrade_capacity_increase_kn"]
    cost_estimate["column_upgrade_rate_thb_per_kn"] = column_cost_info["column_upgrade_rate_thb_per_kn"]
    cost_estimate["total_cost_thb"] = combined_total_cost_thb

    base_time_estimate = generate_time_estimate(decision, corrected_design)
    foundation_phase_days = float(base_time_estimate.get("estimated_days", 0.0))
    column_time_info = _estimate_column_upgrade_time(
        original_design["column_capacity"],
        corrected_design["column_capacity"]
    )
    column_upgrade_phase_days = float(column_time_info["column_upgrade_phase_days"])
    combined_total_days = foundation_phase_days + column_upgrade_phase_days

    if no_action_case:
        foundation_phase_days = 0.0
        column_upgrade_phase_days = 0.0
        combined_total_days = 0.0
        activity = "No corrective construction work"
        basis = "No corrective construction work required — current design already passes within engineering tolerance."
    elif column_upgrade_phase_days > 0:
        activity = "Foundation work + Column upgrade work"
        basis = (
            f"{base_time_estimate.get('basis', 'Foundation benchmark applied.')} "
            f"| Fixed internal benchmark: +{column_upgrade_phase_days:.1f} day "
            f"for deterministic column capacity upgrade package "
            f"({column_time_info['column_upgrade_capacity_increase_kn']:.1f} kN increase)."
        )
    else:
        activity = base_time_estimate.get("activity", "Foundation work")
        basis = base_time_estimate.get("basis", "N/A")

    time_estimate = dict(base_time_estimate)
    time_estimate["foundation_phase_days"] = foundation_phase_days
    time_estimate["column_upgrade_phase_days"] = column_upgrade_phase_days
    time_estimate["combined_total_days"] = combined_total_days
    time_estimate["estimated_days"] = combined_total_days
    time_estimate["activity"] = activity
    time_estimate["basis"] = basis

    option_entries = []

    if no_action_case:
        option_entries.append(
            _build_option_entry(
                key="current_design",
                label="Current Design",
                design=corrected_design,
                total_cost_thb=combined_total_cost_thb,
                total_days=combined_total_days,
                is_selected=True,
                note="Current design already passes without corrective action.",
            )
        )
    else:
        foundation_only_design, _, _ = _apply_foundation_increase(
            total_load=total_load,
            soil_capacity=soil_capacity,
            column_capacity=original_design["column_capacity"]
        )
        foundation_only_boq = generate_boq(
            foundation_only_design["foundation_width"],
            foundation_only_design["foundation_length"],
            total_load,
            soil_capacity,
            foundation_depth=DEFAULT_FOUNDATION_DEPTH
        )
        foundation_only_cost = generate_cost_estimate(foundation_only_boq, region=_rgn)
        foundation_only_time = float(
            generate_time_estimate(
                {"option_type": "FOUNDATION_INCREASE"},
                foundation_only_design
            ).get("estimated_days", 0.0)
        )
        option_entries.append(
            _build_option_entry(
                key="foundation_only",
                label="Foundation Only",
                design=foundation_only_design,
                total_cost_thb=foundation_only_cost.get("total_cost_thb", 0.0),
                total_days=foundation_only_time,
                is_selected=(len(sequential_path) == 1 and str(sequential_path[0].get("action", "")).upper() == "FOUNDATION_INCREASE"),
                note="Increase foundation size while keeping original column capacity.",
            )
        )

        column_only_design, column_only_capacity = _apply_column_upgrade(
            base_design=original_design,
            total_load=total_load,
            target_capacity=total_load
        )
        column_only_cost_info = _estimate_column_upgrade_cost(
            original_design["column_capacity"],
            column_only_capacity
        )
        column_only_time_info = _estimate_column_upgrade_time(
            original_design["column_capacity"],
            column_only_capacity
        )
        option_entries.append(
            _build_option_entry(
                key="column_only",
                label="Column Only",
                design=column_only_design,
                total_cost_thb=column_only_cost_info.get("column_upgrade_cost_thb", 0.0),
                total_days=column_only_time_info.get("column_upgrade_phase_days", 0.0),
                is_selected=(len(sequential_path) == 1 and str(sequential_path[0].get("action", "")).upper() == "COLUMN_UPGRADE"),
                note="Upgrade column capacity while keeping original foundation size.",
            )
        )

        if len(sequential_path) >= 2:
            option_entries.append(
                _build_option_entry(
                    key="selected_sequential",
                    label="Selected Sequential Path",
                    design=corrected_design,
                    total_cost_thb=combined_total_cost_thb,
                    total_days=combined_total_days,
                    is_selected=True,
                    note="Sequential correction path selected by deterministic logic.",
                )
            )

    option_ranking_summary = _build_option_ranking_summary(option_entries)
    reliability_rows = _build_reliability_rows(
        validation_package=validation,
        foundation_depth_m=DEFAULT_FOUNDATION_DEPTH,
        cost_estimate=cost_estimate,
    )

    try:
        diagram = generate_conceptual_diagram(
            corrected_design["foundation_width"],
            corrected_design["foundation_length"],
            total_load,
            corrected_design["soil_pressure"]
        )
    except Exception:
        diagram = None

    final_validation = dict(validation)
    final_validation["final_status"] = final_status
    final_validation["corrected_design"] = corrected_design
    final_validation["recommended_foundation"] = {
        "width": corrected_design["foundation_width"],
        "length": corrected_design["foundation_length"]
    }
    final_validation["recommended_column_capacity"] = corrected_design.get("column_capacity")
    final_validation["time_estimate"] = time_estimate
    final_validation["cost_estimate"] = cost_estimate
    final_validation["sequential_path"] = sequential_path
    final_validation["action_outcome"] = action_outcome
    final_validation["next_required_action"] = next_required_action
    final_validation["region"] = project_data.get("region", "Thailand")
    final_validation["option_ranking_summary"] = option_ranking_summary

    pdf_report = _call_report_generator(
        generate_engineering_report=generate_engineering_report,
        final_validation=final_validation,
        options=options,
        prebim_original=prebim_original,
        boq_recommended=boq_recommended,
        decision=decision,
        cost_estimate=cost_estimate,
        time_estimate=time_estimate,
        sequential_path=sequential_path,
        action_outcome=action_outcome,
        next_required_action=next_required_action
    )

    output_package = {
        "status": final_status,
        "validation": validation,
        "decision": decision,
        "options": options,
        "reasoning": reasoning,
        "prebim": prebim_original,
        "prebim_original": prebim_original,
        "original_design": original_design,
        "corrected_design": corrected_design,
        "corrected_applied": corrected_applied,
        "sequential_path": sequential_path,
        "action_outcome": action_outcome,
        "next_required_action": next_required_action,
        "boq": boq,
        "boq_original": boq_original,
        "boq_recommended": boq_recommended,
        "cost_estimate": cost_estimate,
        "time_estimate": time_estimate,
        "boq_note": output_note,
        "diagram": diagram,
        "pdf_report": pdf_report,
        "option_ranking_summary": option_ranking_summary,
        "input_reliability_rows": reliability_rows,
    }

    export_payload = _build_export_payload(output_package, project_data)
    output_package["structured_export"] = export_payload
    output_package["structured_export_csv"] = _build_csv_export_text(export_payload)
    output_package["structured_export_json"] = json.dumps(export_payload, indent=2, ensure_ascii=False)

    return output_package


# ============================================
# DISPLAY
# ============================================

def display_construction_output(st, output_package, project_data):
    original = output_package["original_design"]
    corrected = output_package["corrected_design"]
    cost = output_package.get("cost_estimate", {})
    time_est = output_package.get("time_estimate", {})
    seq_path = output_package.get("sequential_path", [])
    reasoning = output_package.get("reasoning", {})
    boq_rec = output_package["boq_recommended"]
    pdf_report = output_package["pdf_report"]
    final_status = output_package["status"]
    is_pass = "PASS" in final_status

    option_summary = output_package.get("option_ranking_summary", {})
    reliability_rows = output_package.get("input_reliability_rows", [])
    export_csv_text = output_package.get("structured_export_csv", "")
    export_json_text = output_package.get("structured_export_json", "")

    _currency, _symbol, _region = _get_currency_info(project_data)

    orig_fw = original.get("foundation_width", "—")
    orig_fl = original.get("foundation_length", "—")
    orig_cap = original.get("column_capacity", "—")
    orig_sp = original.get("soil_pressure", "—")
    orig_su = original.get("soil_utilization", "—")
    orig_cu = original.get("column_utilization", "—")

    corr_fw = corrected.get("foundation_width", "—")
    corr_fl = corrected.get("foundation_length", "—")
    corr_cap = corrected.get("column_capacity", "—")
    corr_su = corrected.get("soil_utilization", "—")
    corr_cu = corrected.get("column_utilization", "—")

    proj_name = project_data.get("project_name", "—")
    proj_type = project_data.get("building_type", "—")
    proj_w = project_data.get("building_width", "—")
    proj_l = project_data.get("building_length", "—")
    proj_f = project_data.get("num_floors", "—")
    total_load = project_data.get("total_load", "—")
    soil_cap = project_data.get("soil_capacity", "—")

    safe_project_name = _sanitize_filename(project_data.get("project_name", "project"))

    no_action_case = _is_no_action_case(seq_path, final_status)
    n_steps = 0 if no_action_case else len(seq_path)

    total_cost = int(cost.get("combined_total_cost_thb", 0))
    total_days = time_est.get("combined_total_days", 0)
    fp_cost = int(cost.get("foundation_phase_cost_thb", 0))
    fp_days = time_est.get("foundation_phase_days", 0)
    cu_cost = int(cost.get("column_upgrade_cost_thb", 0))
    cu_days = time_est.get("column_upgrade_phase_days", 0)

    if no_action_case:
        cost_subtext = f"Baseline construction estimate {_symbol}{fp_cost:,} {_currency}"
        time_subtext = "No corrective construction work required"
    else:
        cost_subtext = f"{_symbol}{fp_cost:,} foundation &nbsp;&middot;&nbsp; {_symbol}{cu_cost:,} column upgrade"
        time_subtext = f"{fp_days:.1f} d foundation &nbsp;&middot;&nbsp; {cu_days:.1f} d column upgrade"

    status_cls = "kf-header-status-pass" if is_pass else "kf-header-status-fail"
    status_symbol = "&#10003;" if is_pass else "&#10007;"

    eng_mode, eng_interp = _classify_design(corr_su, corr_cu)
    initial_status_display = _normalize_display_status(
        original.get("status", "N/A"),
        original.get("soil_utilization"),
        original.get("column_utilization")
    )

    display_primary_reason, display_governing_logic, display_confidence = _build_display_reasoning(
        reasoning=reasoning,
        seq_path=seq_path,
        original=original,
        corrected=corrected,
        final_status=final_status
    )

    phys_line1, phys_line2, phys_line3 = _build_physical_explanation(
        original=original,
        corrected=corrected,
        seq_path=seq_path,
        total_load=total_load,
        soil_cap=soil_cap,
        final_status=final_status
    )

    try:
        orig_cu_f = float(orig_cu)
        orig_su_f = float(orig_su)
        tradeoff_a_stat = "FAIL" if orig_cu_f > PASS_LIMIT else "PASS"
        tradeoff_c_stat = "FAIL" if orig_su_f > PASS_LIMIT else "PASS"
    except Exception:
        tradeoff_a_stat = "FAIL"
        tradeoff_c_stat = "FAIL"

    try:
        _corr_su_f = float(corr_su)
        _corr_cu_f = float(corr_cu)
        _show_tolerance_note = (
            1.000 < _corr_su_f <= PASS_LIMIT or
            1.000 < _corr_cu_f <= PASS_LIMIT
        )
    except (TypeError, ValueError):
        _show_tolerance_note = False

    st.markdown("""
    <style>
    .kf-wrap{border:1px solid #e0e0de;border-radius:8px;overflow:hidden;margin-bottom:12px;font-family:'DM Mono',monospace}
    .kf-header{display:flex;justify-content:space-between;align-items:center;padding:10px 18px;background:#f0f0ee;border-bottom:1px solid #ddd}
    .kf-header-brand{font-size:13px;font-weight:700;letter-spacing:.04em;color:#111}
    .kf-header-project{font-size:11px;color:#888;letter-spacing:.06em;margin-top:1px}
    .kf-header-status-pass{font-size:11px;font-weight:600;color:#fff;background:#444;padding:4px 14px;border-radius:4px;letter-spacing:.06em}
    .kf-header-status-fail{font-size:11px;font-weight:600;color:#fff;background:#7a3a3a;padding:4px 14px;border-radius:4px;letter-spacing:.06em}
    .kf-impact-top{padding:16px 20px;background:#fff;border-bottom:1px solid #e8e8e6;display:flex;gap:34px;align-items:flex-end}
    .kf-impact-main-num{font-size:32px;font-weight:500;color:#111;line-height:1;letter-spacing:-.01em}
    .kf-impact-main-unit{font-size:11px;color:#aaa;letter-spacing:.08em;margin-top:3px}
    .kf-impact-sub{font-size:11px;color:#888;margin-top:8px}
    .kf-result-strip{display:flex;gap:0;border-bottom:1px solid #e8e8e6;background:#fafaf8}
    .kf-result-cell{flex:1;padding:9px 18px;border-right:1px solid #e8e8e6}
    .kf-result-cell:last-child{border-right:none}
    .kf-result-label{font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
    .kf-result-val{font-size:14px;font-weight:500;color:#111}
    .kf-result-status{font-size:13px;font-weight:500;color:#111}
    .kf-cell-label{font-size:9px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#bbb;margin-bottom:6px}
    .kf-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;font-size:11px}
    .kf-row-key{color:#aaa}
    .kf-row-val{font-weight:400;color:#444}
    .kf-row-val.bad{color:#999}
    .phys-wrap{padding:12px 18px;background:#fafaf8;font-family:'DM Mono',monospace}
    .phys-label{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#bbb;margin-bottom:7px}
    .phys-line{font-size:11px;color:#666;margin-bottom:3px;line-height:1.55}
    .to-wrap{padding:12px 18px;background:#fff;font-family:'DM Mono',monospace}
    .to-label{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#bbb;margin-bottom:7px}
    .to-table{width:100%;border-collapse:collapse;font-size:11px}
    .to-table th{font-size:9px;color:#aaa;letter-spacing:.08em;text-transform:uppercase;text-align:left;padding:4px 8px;border-bottom:1px solid #eee;font-weight:500}
    .to-table td{padding:5px 8px;color:#555;border-bottom:1px solid #f5f5f3}
    .to-table td:last-child{font-weight:600}
    .to-table tr.selected td{color:#111;background:#f8f8f6}
    .eng-wrap{padding:10px 18px;background:#f8f8f6;font-family:'DM Mono',monospace;display:flex;gap:12px;align-items:center}
    .eng-label{font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase}
    .eng-mode{font-size:12px;font-weight:600;color:#333}
    .eng-interp{font-size:10px;color:#999;margin-top:0}
    .det-sec{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#bbb;border-bottom:1px solid #eee;padding-bottom:5px;margin:14px 0 8px}
    .det-table{width:100%;border-collapse:collapse}
    .det-table td{font-size:11px;padding:4px 8px;border-bottom:1px solid #f5f5f3;font-family:'DM Mono',monospace;color:#555}
    .det-table td:first-child{color:#aaa;width:55%}
    .det-table td:last-child{font-weight:500;color:#222;text-align:right}
    .tol-note{border:1px solid #d6c97a;border-radius:6px;background:#fdfbee;padding:10px 16px;
              font-family:'DM Mono',monospace;font-size:11px;color:#7a6f2e;margin-top:6px;line-height:1.6}
    .tol-note-label{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
                    color:#a89a3a;margin-bottom:5px}
    .rank-wrap{padding:12px 18px;background:#fff;border:1px solid #e8e8e6;border-radius:6px;margin-top:6px;font-family:'DM Mono',monospace}
    .rank-head{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#bbb;margin-bottom:6px}
    .rank-chip{display:inline-block;padding:4px 10px;border:1px solid #ddd;border-radius:20px;font-size:10px;margin-right:6px;margin-bottom:4px;background:#fafaf8;color:#444}
    div.stDownloadButton > button{white-space:nowrap;min-height:38px}
    div.stDownloadButton > button p{white-space:nowrap}
    div.stButton > button{min-height:38px}
    div.st-key-start_new_project_btn button{white-space:nowrap;min-height:38px}
    div.st-key-start_new_project_btn button p{white-space:nowrap}
    </style>
    """, unsafe_allow_html=True)

    if original.get("status") == "FAIL" and is_pass:
        st.markdown("""
        <div style="background:#f8f8f6;border:1px solid #e0e0de;border-radius:6px;
                    padding:10px 18px;margin-bottom:10px;font-family:'DM Mono',monospace;
                    display:flex;align-items:center;gap:12px;">
          <span style="font-size:13px;color:#888">&#10007; Current design fails</span>
          <span style="color:#bbb;font-size:13px">&rarr;</span>
          <span style="font-size:13px;font-weight:600;color:#333">Engineering correction applied &rarr; PASS</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="kf-wrap">
      <div class="kf-header">
        <div>
          <div class="kf-header-brand">TRIPLEBOT V9</div>
          <div class="kf-header-project">{proj_name} &nbsp;&middot;&nbsp; {proj_type} &nbsp;&middot;&nbsp; {proj_w}&times;{proj_l} m &nbsp;&middot;&nbsp; {proj_f} Floors &nbsp;&middot;&nbsp; {_region}</div>
        </div>
        <div class="{status_cls}">{status_symbol} {final_status}</div>
      </div>
      <div class="kf-impact-top">
        <div>
          <div style="font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px">Total Cost</div>
          <div class="kf-impact-main-num">{_symbol}{total_cost:,}</div>
          <div class="kf-impact-main-unit">{_currency}</div>
          <div class="kf-impact-sub">{cost_subtext}</div>
        </div>
        <div>
          <div style="font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px">Total Duration</div>
          <div class="kf-impact-main-num">{total_days:.1f}</div>
          <div class="kf-impact-main-unit">DAYS</div>
          <div class="kf-impact-sub">{time_subtext}</div>
        </div>
      </div>
      <div class="kf-result-strip">
        <div class="kf-result-cell">
          <div class="kf-result-label">Final Status</div>
          <div class="kf-result-status">{status_symbol} {final_status}</div>
        </div>
        <div class="kf-result-cell">
          <div class="kf-result-label">Soil Utilization</div>
          <div class="kf-result-val">{corr_su}</div>
        </div>
        <div class="kf-result-cell">
          <div class="kf-result-label">Column Utilization</div>
          <div class="kf-result-val">{corr_cu}</div>
        </div>
        <div class="kf-result-cell">
          <div class="kf-result-label">Foundation</div>
          <div class="kf-result-val">{corr_fw} &times; {corr_fl} m</div>
        </div>
        <div class="kf-result-cell">
          <div class="kf-result-label">Column Cap.</div>
          <div class="kf-result-val">{corr_cap} kN</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_prob, col_dec = st.columns(2)

    with col_prob:
        st.markdown('<div class="kf-cell-label">Problem</div>', unsafe_allow_html=True)
        if no_action_case:
            st.markdown(f"""
            <div style="font-family:'DM Mono',monospace;font-size:11px">
              <div class="kf-row"><span class="kf-row-key">Initial Status</span><span class="kf-row-val">{initial_status_display} &#10003;</span></div>
              <div class="kf-row"><span class="kf-row-key">Soil Utilization</span><span class="kf-row-val">{orig_su} &#10003;</span></div>
              <div class="kf-row"><span class="kf-row-key">Column Utilization</span><span class="kf-row-val">{orig_cu} &#10003;</span></div>
              <div class="kf-row"><span class="kf-row-key">Soil Pressure</span><span class="kf-row-val">{orig_sp} kN/m²</span></div>
              <div class="kf-row"><span class="kf-row-key">Foundation</span><span class="kf-row-val">{orig_fw} &times; {orig_fl} m</span></div>
              <div class="kf-row"><span class="kf-row-key">Column Cap.</span><span class="kf-row-val">{orig_cap} kN</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="font-family:'DM Mono',monospace;font-size:11px">
              <div class="kf-row"><span class="kf-row-key">Soil Utilization</span><span class="kf-row-val bad">{orig_su} &#10007;</span></div>
              <div class="kf-row"><span class="kf-row-key">Column Utilization</span><span class="kf-row-val bad">{orig_cu} &#10007;</span></div>
              <div class="kf-row"><span class="kf-row-key">Soil Pressure</span><span class="kf-row-val">{orig_sp} kN/m²</span></div>
              <div class="kf-row"><span class="kf-row-key">Foundation</span><span class="kf-row-val">{orig_fw} &times; {orig_fl} m</span></div>
              <div class="kf-row"><span class="kf-row-key">Column Cap.</span><span class="kf-row-val">{orig_cap} kN</span></div>
            </div>
            """, unsafe_allow_html=True)

    with col_dec:
        st.markdown('<div class="kf-cell-label">Decision</div>', unsafe_allow_html=True)
        if no_action_case:
            st.markdown(f"""
            <div style="font-family:'DM Mono',monospace;font-size:11px">
              <div class="kf-row"><span class="kf-row-key">Action</span><span style="font-weight:500;color:#222">NO_ACTION</span></div>
              <div class="kf-row"><span class="kf-row-key">Foundation</span><span class="kf-row-val">{corr_fw} m (unchanged)</span></div>
              <div class="kf-row"><span class="kf-row-key">Column Cap.</span><span class="kf-row-val">{corr_cap} kN (unchanged)</span></div>
              <div class="kf-row"><span class="kf-row-key">Corrections</span><span class="kf-row-val">0 applied</span></div>
              <div class="kf-row"><span class="kf-row-key">Note</span><span class="kf-row-val">Current design already satisfies the engineering limit.</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for s in seq_path:
                st.markdown(
                    f'<div class="kf-row" style="font-family:\'DM Mono\',monospace;font-size:11px">'
                    f'<span class="kf-row-key">Step {s["step_number"]}</span>'
                    f'<span style="font-weight:500;color:#222">{s["action"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            st.markdown(f"""
            <div style="font-family:'DM Mono',monospace;font-size:11px">
              <div class="kf-row"><span class="kf-row-key">Foundation</span><span class="kf-row-val">{orig_fw} &rarr; {corr_fw} m</span></div>
              <div class="kf-row"><span class="kf-row-key">Column Cap.</span><span class="kf-row-val">{orig_cap} &rarr; {corr_cap} kN</span></div>
              <div class="kf-row"><span class="kf-row-key">Corrections</span><span class="kf-row-val">{n_steps} applied</span></div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="phys-wrap" style="border:1px solid #e8e8e6;border-radius:6px;margin-top:8px">
      <div class="phys-label">Physical Explanation</div>
      <div class="phys-line">{phys_line1}</div>
      <div class="phys-line">{phys_line2}</div>
      <div class="phys-line" style="color:#444">{phys_line3}</div>
    </div>
    """, unsafe_allow_html=True)

    if no_action_case:
        st.markdown(f"""
        <div class="to-wrap" style="border:1px solid #e8e8e6;border-radius:6px;margin-top:8px">
          <div class="to-label">Engineering Trade-Off Snapshot</div>
          <table class="to-table">
            <tr><th>Option</th><th>Foundation</th><th>Column Cap.</th><th>Soil Util.</th><th>Column Util.</th><th>Status</th></tr>
            <tr class="selected"><td>Selected &mdash; Current Design &#10003;</td><td>{corr_fw} m</td><td>{corr_cap} kN</td><td>{corr_su}</td><td>{corr_cu}</td><td>PASS</td></tr>
          </table>
          <div style="margin-top:6px;font-size:11px;color:#777">No comparison scenario is required because the current design already passes without corrective action.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="to-wrap" style="border:1px solid #e8e8e6;border-radius:6px;margin-top:8px">
          <div class="to-label">Engineering Trade-Off Snapshot</div>
          <table class="to-table">
            <tr><th>Option</th><th>Foundation</th><th>Column Cap.</th><th>Soil Util.</th><th>Column Util.</th><th>Status</th></tr>
            <tr><td>A &mdash; Foundation only</td><td>{corr_fw} m</td><td>{orig_cap} kN</td><td>{corr_su}</td><td>{orig_cu}</td><td>{tradeoff_a_stat}</td></tr>
            <tr class="selected"><td>B &mdash; Selected &#10003;</td><td>{corr_fw} m</td><td>{corr_cap} kN</td><td>{corr_su}</td><td>{corr_cu}</td><td>PASS</td></tr>
            <tr><td>C &mdash; Column only</td><td>{orig_fw} m</td><td>{corr_cap} kN</td><td>{orig_su}</td><td>{corr_cu}</td><td>{tradeoff_c_stat}</td></tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

    ranking_summary_html = _build_ranking_summary_html(
        option_summary=option_summary,
        currency_symbol=_symbol,
        currency_code=_currency,
    )
    if ranking_summary_html:
        st.markdown(ranking_summary_html, unsafe_allow_html=True)

    reliability_summary_html = _build_reliability_summary_html(reliability_rows)
    if reliability_summary_html:
        st.markdown(reliability_summary_html, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="eng-wrap" style="border:1px solid #e8e8e6;border-radius:6px;margin-top:8px">
      <div>
        <div class="eng-label">Design Classification</div>
        <div class="eng-mode">{eng_mode}</div>
        <div class="eng-interp">{eng_interp}</div>
      </div>
      <div style="border-left:1px solid #e0e0de;padding-left:16px;margin-left:6px">
        <div class="eng-label">Soil Util. at Correction</div>
        <div class="eng-mode">{corr_su}</div>
        <div class="eng-interp">Limit = 1.010 (Engineering Tolerance)</div>
      </div>
      <div style="border-left:1px solid #e0e0de;padding-left:16px;margin-left:6px">
        <div class="eng-label">Column Util. at Correction</div>
        <div class="eng-mode">{corr_cu}</div>
        <div class="eng-interp">Limit = 1.010 (Engineering Tolerance)</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if _show_tolerance_note:
        _tol_vals = []
        if 1.000 < _corr_su_f <= PASS_LIMIT:
            _tol_vals.append(f"Soil Util. = {corr_su}")
        if 1.000 < _corr_cu_f <= PASS_LIMIT:
            _tol_vals.append(f"Column Util. = {corr_cu}")
        _tol_str = " &nbsp;&middot;&nbsp; ".join(_tol_vals)
        st.markdown(f"""
        <div class="tol-note">
          <div class="tol-note-label">&#9651; Engineering Tolerance Applied</div>
          {_tol_str} — within accepted band ≤ 1.010.
          Deterministic rounding, not structural failure.
          Final sign-off requires licensed structural engineer review.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("&#9656; Technical Detail", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="det-sec">Bill of Quantities</div>', unsafe_allow_html=True)
            st.markdown(f"""<table class="det-table">
              <tr><td>Foundation Area</td><td>{boq_rec.get("foundation_area","—")} m²</td></tr>
              <tr><td>Foundation Depth</td><td>{boq_rec.get("foundation_depth","—")} m</td></tr>
              <tr><td>Concrete Volume</td><td>{boq_rec.get("concrete_volume_m3","—")} m³</td></tr>
              <tr><td>Excavation Volume</td><td>{boq_rec.get("excavation_volume_m3","—")} m³</td></tr>
              <tr><td>Reinforcement</td><td>{boq_rec.get("reinforcement_estimate","—")} kg</td></tr>
            </table>""", unsafe_allow_html=True)

            st.markdown('<div class="det-sec">Cost Breakdown</div>', unsafe_allow_html=True)
            st.markdown(f"""<table class="det-table">
              <tr><td>Concrete</td><td>{_symbol}{int(cost.get("concrete_cost_thb",0)):,} {_currency}</td></tr>
              <tr><td>Excavation</td><td>{_symbol}{int(cost.get("excavation_cost_thb",0)):,} {_currency}</td></tr>
              <tr><td>Reinforcement</td><td>{_symbol}{int(cost.get("reinforcement_cost_thb",0)):,} {_currency}</td></tr>
              <tr><td>Column Upgrade</td><td>{_symbol}{int(cost.get("column_upgrade_cost_thb",0)):,} {_currency}</td></tr>
            </table>""", unsafe_allow_html=True)

            if reliability_rows:
                st.markdown('<div class="det-sec">Input Reliability / Data Source</div>', unsafe_allow_html=True)
                rows_html = ""
                for row in reliability_rows:
                    rows_html += (
                        "<tr>"
                        f"<td>{_escape_html_text(row.get('label', '—'))}</td>"
                        f"<td>{_escape_html_text(row.get('value_display', '—'))}</td>"
                        f"<td>{_escape_html_text(row.get('source', '—'))}</td>"
                        f"<td>{_escape_html_text(row.get('note', '—'))}</td>"
                        "</tr>"
                    )
                st.markdown(
                    (
                        '<table class="to-table">'
                        '<tr><th>Field</th><th>Value</th><th>Source</th><th>Note</th></tr>'
                        f'{rows_html}'
                        '</table>'
                    ),
                    unsafe_allow_html=True
                )

        with c2:
            st.markdown('<div class="det-sec">Correction Path</div>', unsafe_allow_html=True)
            if no_action_case:
                st.markdown(f"""<table class="det-table">
                  <tr><td>Action</td><td>NO_ACTION</td></tr>
                  <tr><td>Foundation</td><td>{corr_fw} x {corr_fl} m</td></tr>
                  <tr><td>Column Cap.</td><td>{float(corr_cap):.0f} kN</td></tr>
                  <tr><td>Soil Util.</td><td>{float(corr_su):.3f}</td></tr>
                  <tr><td>Column Util.</td><td>{float(corr_cu):.3f}</td></tr>
                </table><div style="margin:6px 0"></div>""", unsafe_allow_html=True)
            else:
                for s in seq_path:
                    st.markdown(f"""<table class="det-table">
                      <tr><td>Step {s["step_number"]} &mdash; {s["action"]}</td><td>{s["status"]}</td></tr>
                      <tr><td>Foundation</td><td>{s["foundation_width"]:.2f} x {s["foundation_length"]:.2f} m</td></tr>
                      <tr><td>Column Cap.</td><td>{s["column_capacity"]:.0f} kN</td></tr>
                      <tr><td>Soil Util.</td><td>{s["soil_utilization"]:.3f}</td></tr>
                      <tr><td>Column Util.</td><td>{s["column_utilization"]:.3f}</td></tr>
                    </table><div style="margin:6px 0"></div>""", unsafe_allow_html=True)

            st.markdown('<div class="det-sec">Decision Reasoning</div>', unsafe_allow_html=True)
            st.markdown(f"""<table class="det-table">
              <tr><td>Primary Reason</td><td>{display_primary_reason}</td></tr>
              <tr><td>Governing Logic</td><td>{display_governing_logic}</td></tr>
              <tr><td>Confidence</td><td>{display_confidence}</td></tr>
            </table>""", unsafe_allow_html=True)

    st.divider()

    col_pdf, col_csv, col_json, col_new = st.columns([1.7, 1.7, 1.7, 1.35])
    with col_pdf:
        st.download_button(
            label="Download PDF Report",
            data=pdf_report,
            file_name=f"triplebot_v9_{safe_project_name}_report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    with col_csv:
        st.download_button(
            label="Download CSV Export",
            data=export_csv_text,
            file_name=f"triplebot_v9_{safe_project_name}_export.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_json:
        st.download_button(
            label="Download JSON Export",
            data=export_json_text,
            file_name=f"triplebot_v9_{safe_project_name}_export.json",
            mime="application/json",
            use_container_width=True
        )
    with col_new:
        if st.button("Start New Project", key="start_new_project_btn", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.caption("Preliminary assessment only. Final verification by a licensed structural engineer required.")
    st.caption("Triple Bot V9 — Deterministic Engine · No generative AI · All results reproducible.")