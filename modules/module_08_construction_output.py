# ============================================
# TRIPLE BOT V9.9.1
# Module 08 — Construction Output System
# FIX V9.9.1:
# - Design Classification now considers BOTH soil + column utilization
# - Interpretation text now dynamic (not hardcoded "near capacity limit")
# - BOQ display format guard added
# - Tolerance note added in UI Stage 8 (Cross Clover fix)
# ============================================

import inspect


PASS_LIMIT = 1.010


def _calc_status(su, cu):
    if su <= PASS_LIMIT and cu <= PASS_LIMIT:
        if su > 1.000 or cu > 1.000:
            return "PASS (Engineering Tolerance)"
        return "PASS"
    return "FAIL"


def _classify_design(su, cu):
    """
    Design classification based on BOTH soil and column utilization.
    Uses max of the two — avoids misleading label when one governs.
    """
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
    """
    Return honest interpretation text based on actual value.
    """
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
    "Thailand":      {"currency": "THB", "symbol": ""},
    "China":         {"currency": "CNY", "symbol": "¥"},
    "United States": {"currency": "USD", "symbol": "$"},
}


def _get_currency_info(project_data):
    region = project_data.get("region", "Thailand")
    info = _REGION_CURRENCY.get(region, _REGION_CURRENCY["Thailand"])
    return info["currency"], info["symbol"], region


def _build_design(
    foundation_width,
    foundation_length,
    total_load,
    soil_capacity,
    column_capacity,
    status_override=None
):
    foundation_area = foundation_width * foundation_length
    soil_pressure = (
        total_load / foundation_area if foundation_area > 0 else float("inf")
    )
    soil_utilization = (
        soil_pressure / soil_capacity if soil_capacity > 0 else float("inf")
    )
    column_utilization = (
        total_load / column_capacity if column_capacity > 0 else float("inf")
    )
    status = _calc_status(soil_utilization, column_utilization)
    if status_override is not None:
        status = status_override
    return {
        "foundation_width":    round(foundation_width, 3),
        "foundation_length":   round(foundation_length, 3),
        "foundation_area":     round(foundation_area, 3),
        "soil_pressure":       round(soil_pressure, 3),
        "soil_utilization":    round(soil_utilization, 3),
        "column_capacity":     round(column_capacity, 3),
        "column_utilization":  round(column_utilization, 3),
        "status":              status
    }


def _apply_foundation_increase(total_load, soil_capacity, column_capacity):
    required_area = (
        total_load / soil_capacity if soil_capacity > 0 else float("inf")
    )
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
        "step_number":        step_number,
        "action":             action,
        "note":               note,
        "foundation_width":   round(design.get("foundation_width", 0.0), 3),
        "foundation_length":  round(design.get("foundation_length", 0.0), 3),
        "column_capacity":    round(design.get("column_capacity", 0.0), 3),
        "soil_utilization":   round(design.get("soil_utilization", 0.0), 3),
        "column_utilization": round(design.get("column_utilization", 0.0), 3),
        "status":             design.get("status", "N/A")
    }


def _estimate_column_upgrade_cost(original_capacity, final_capacity):
    increase_kn = max(0.0, final_capacity - original_capacity)
    rate_thb_per_kn = 10.0
    cost = increase_kn * rate_thb_per_kn
    return {
        "column_upgrade_capacity_increase_kn": round(increase_kn, 3),
        "column_upgrade_rate_thb_per_kn":      rate_thb_per_kn,
        "column_upgrade_cost_thb":             round(cost, 0)
    }


def _estimate_column_upgrade_time(original_capacity, final_capacity):
    increase_kn = max(0.0, final_capacity - original_capacity)
    days = 1.0 if increase_kn > 0 else 0.0
    return {
        "column_upgrade_capacity_increase_kn": round(increase_kn, 3),
        "column_upgrade_phase_days":           days
    }


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
            "result":               final_validation,
            "intelligence":         options,
            "prebim":               prebim_original,
            "boq":                  boq_recommended,
            "decision":             decision,
            "cost_estimate":        cost_estimate,
            "time_estimate":        time_estimate,
            "sequential_path":      sequential_path,
            "action_outcome":       action_outcome,
            "next_required_action": next_required_action,
            "region":               final_validation.get("region", "Thailand")
        }
        filtered_kwargs = {k: v for k, v in full_kwargs.items() if k in sig.parameters}
        return generate_engineering_report(**filtered_kwargs)
    except Exception:
        return generate_engineering_report(
            final_validation, options, prebim_original,
            boq_recommended, decision, cost_estimate=cost_estimate
        )


# ============================================
# CORE RUN
# ============================================

def run_construction_output(decision_package, project_data):

    validation = decision_package["validation"]
    decision   = decision_package["decision"]
    options    = decision_package.get("options", [])
    reasoning  = decision_package.get("reasoning", {})

    total_load              = project_data["total_load"]
    soil_capacity           = project_data["soil_capacity"]
    num_floors              = project_data["num_floors"]
    current_column_capacity = project_data["column_capacity"]
    foundation_width        = project_data["foundation_width"]
    foundation_length       = project_data["foundation_length"]

    from boq_engine                 import generate_boq
    from cost_estimate_engine       import generate_cost_estimate
    from time_estimate_engine       import generate_time_estimate
    from triplebot_diagram_engine   import generate_conceptual_diagram
    from triplebot_report_generator import generate_engineering_report
    from pre_bim_validation_engine  import run_prebim_validation

    engineering_load_per_storey = project_data.get("engineering_load_per_storey")
    if engineering_load_per_storey is None:
        engineering_load_per_storey = (
            total_load / num_floors if num_floors > 0 else 0.0
        )

    prebim_original = run_prebim_validation(
        engineering_load_per_storey, num_floors,
        foundation_width, foundation_length,
        current_column_capacity, soil_capacity
    )

    original_design = _build_design(
        foundation_width=foundation_width,
        foundation_length=foundation_length,
        total_load=total_load,
        soil_capacity=soil_capacity,
        column_capacity=current_column_capacity,
        status_override=validation.get("status", "N/A")
    )

    corrected_design     = dict(original_design)
    corrected_applied    = False
    output_note          = None
    sequential_path      = []
    action_outcome       = []
    next_required_action = None
    decision_type        = decision.get("option_type") if decision else None

    if decision_type == "FOUNDATION_INCREASE":
        corrected_applied = True
        step1_design, required_area, new_size = _apply_foundation_increase(
            total_load=total_load, soil_capacity=soil_capacity,
            column_capacity=current_column_capacity
        )
        corrected_design = step1_design
        output_note = f"Recommended foundation size based on soil capacity: {new_size:.2f} m"
        if decision is not None:
            decision["foundation_size"] = new_size
        sequential_path.append(_build_step_record(1, "FOUNDATION_INCREASE", step1_design,
            "Primary correction applied to reduce soil pressure."))

        if step1_design["status"] == "PASS":
            action_outcome = ["Soil correction successful.",
                              "Selected corrective action resolved the identified failure."]
        else:
            if step1_design["column_utilization"] > PASS_LIMIT:
                next_required_action = {"action": "COLUMN_UPGRADE",
                    "reason": f"Column utilization remains {step1_design['column_utilization']:.3f} (> {PASS_LIMIT})."}
                step2_design, upgraded_capacity = _apply_column_upgrade(
                    base_design=step1_design, total_load=total_load, target_capacity=total_load)
                corrected_design = step2_design
                sequential_path.append(_build_step_record(2, "COLUMN_UPGRADE", step2_design,
                    "Secondary correction applied to resolve remaining column failure."))
                if decision is not None:
                    decision["recommended_capacity"] = upgraded_capacity
                _su2 = step2_design.get("soil_utilization", 9.0)
                _cu2 = step2_design.get("column_utilization", 9.0)
                step2_design["status"] = _calc_status(_su2, _cu2)
                if _su2 <= PASS_LIMIT and _cu2 <= PASS_LIMIT:
                    action_outcome = ["Soil correction successful.",
                                      "Secondary action COLUMN_UPGRADE applied.",
                                      "Final combined correction achieved PASS."]
                    next_required_action = None
                else:
                    action_outcome = ["Soil correction insufficient.", "Further redesign required."]
            else:
                action_outcome = ["Primary corrective action applied.",
                                  "Identified failure not fully resolved.", "Further action required."]

    elif decision_type == "COLUMN_UPGRADE":
        corrected_applied = True
        step1_design, upgraded_capacity = _apply_column_upgrade(
            base_design=original_design, total_load=total_load, target_capacity=total_load)
        corrected_design = step1_design
        output_note = f"Recommended column capacity based on total load: {upgraded_capacity:.2f} kN"
        if decision is not None:
            decision["recommended_capacity"] = upgraded_capacity
        sequential_path.append(_build_step_record(1, "COLUMN_UPGRADE", step1_design,
            "Primary correction applied to resolve column capacity deficiency."))

        if step1_design["status"] == "PASS":
            action_outcome = ["Column correction successful.",
                              "Selected corrective action resolved the identified failure."]
        else:
            if step1_design["column_utilization"] <= 1.0 and step1_design["soil_utilization"] > 1.0:
                next_required_action = {"action": "FOUNDATION_INCREASE",
                    "reason": f"Soil utilization remains {step1_design['soil_utilization']:.3f} (> 1.0)."}
                step2_design, required_area, new_size = _apply_foundation_increase(
                    total_load=total_load, soil_capacity=soil_capacity,
                    column_capacity=step1_design["column_capacity"])
                corrected_design = step2_design
                sequential_path.append(_build_step_record(2, "FOUNDATION_INCREASE", step2_design,
                    "Secondary correction applied to resolve remaining soil failure."))
                if decision is not None:
                    decision["foundation_size"] = new_size
                if step2_design["status"] == "PASS":
                    action_outcome = ["Column correction successful.", "Soil still fails.",
                                      "Secondary action FOUNDATION_INCREASE applied.",
                                      "Final combined correction achieved PASS."]
                    next_required_action = None
                else:
                    action_outcome = ["Column correction successful.", "Soil still fails.",
                                      "Further action required."]
            else:
                action_outcome = ["Primary corrective action applied.",
                                  "Identified failure not fully resolved.", "Further action required."]
    else:
        corrected_design = dict(original_design)
        action_outcome   = ["No corrective construction action required."]

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

    DEFAULT_DEPTH = 0.4

    boq_original    = generate_boq(foundation_width, foundation_length,
                                   total_load, soil_capacity, foundation_depth=DEFAULT_DEPTH)
    boq_recommended = generate_boq(corrected_design["foundation_width"],
                                   corrected_design["foundation_length"],
                                   total_load, soil_capacity, foundation_depth=DEFAULT_DEPTH)
    boq = boq_recommended

    _rgn = project_data.get("region", "Thailand")
    foundation_phase_cost     = generate_cost_estimate(boq_recommended, region=_rgn)
    column_cost_info          = _estimate_column_upgrade_cost(
                                    original_design["column_capacity"],
                                    corrected_design["column_capacity"])
    column_upgrade_cost_thb   = column_cost_info["column_upgrade_cost_thb"]
    foundation_total_cost_thb = round(foundation_phase_cost.get("total_cost_thb", 0.0), 0)
    combined_total_cost_thb   = round(foundation_total_cost_thb + column_upgrade_cost_thb, 0)

    cost_estimate = dict(foundation_phase_cost)
    cost_estimate["foundation_phase_cost_thb"]           = foundation_total_cost_thb
    cost_estimate["column_upgrade_cost_thb"]             = column_upgrade_cost_thb
    cost_estimate["combined_total_cost_thb"]             = combined_total_cost_thb
    cost_estimate["column_upgrade_capacity_increase_kn"] = column_cost_info["column_upgrade_capacity_increase_kn"]
    cost_estimate["column_upgrade_rate_thb_per_kn"]      = column_cost_info["column_upgrade_rate_thb_per_kn"]
    cost_estimate["total_cost_thb"]                      = combined_total_cost_thb

    base_time_estimate        = generate_time_estimate(decision, corrected_design)
    foundation_phase_days     = float(base_time_estimate.get("estimated_days", 0.0))
    column_time_info          = _estimate_column_upgrade_time(
                                    original_design["column_capacity"],
                                    corrected_design["column_capacity"])
    column_upgrade_phase_days = float(column_time_info["column_upgrade_phase_days"])
    combined_total_days       = foundation_phase_days + column_upgrade_phase_days

    if column_upgrade_phase_days > 0:
        activity = "Foundation work + Column upgrade work"
        basis    = (f"{base_time_estimate.get('basis','Foundation benchmark applied.')} "
                    f"| Fixed internal benchmark: +{column_upgrade_phase_days:.1f} day "
                    f"for deterministic column capacity upgrade package "
                    f"({column_time_info['column_upgrade_capacity_increase_kn']:.1f} kN increase).")
    else:
        activity = base_time_estimate.get("activity", "Foundation work")
        basis    = base_time_estimate.get("basis", "N/A")

    time_estimate = dict(base_time_estimate)
    time_estimate["foundation_phase_days"]     = foundation_phase_days
    time_estimate["column_upgrade_phase_days"] = column_upgrade_phase_days
    time_estimate["combined_total_days"]       = combined_total_days
    time_estimate["estimated_days"]            = combined_total_days
    time_estimate["activity"]                  = activity
    time_estimate["basis"]                     = basis

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
    final_validation["final_status"]               = final_status
    final_validation["corrected_design"]           = corrected_design
    final_validation["recommended_foundation"]     = {
        "width":  corrected_design["foundation_width"],
        "length": corrected_design["foundation_length"]
    }
    final_validation["recommended_column_capacity"] = corrected_design.get("column_capacity")
    final_validation["time_estimate"]              = time_estimate
    final_validation["cost_estimate"]              = cost_estimate
    final_validation["sequential_path"]            = sequential_path
    final_validation["action_outcome"]             = action_outcome
    final_validation["next_required_action"]       = next_required_action
    final_validation["region"]                     = project_data.get("region", "Thailand")

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

    return {
        "status":            final_status,
        "validation":        validation,
        "decision":          decision,
        "options":           options,
        "reasoning":         reasoning,
        "prebim":            prebim_original,
        "prebim_original":   prebim_original,
        "original_design":   original_design,
        "corrected_design":  corrected_design,
        "corrected_applied": corrected_applied,
        "sequential_path":   sequential_path,
        "action_outcome":    action_outcome,
        "next_required_action": next_required_action,
        "boq":               boq,
        "boq_original":      boq_original,
        "boq_recommended":   boq_recommended,
        "cost_estimate":     cost_estimate,
        "time_estimate":     time_estimate,
        "boq_note":          output_note,
        "diagram":           diagram,
        "pdf_report":        pdf_report
    }


# ============================================
# DISPLAY
# ============================================

def display_construction_output(st, output_package, project_data):

    original     = output_package["original_design"]
    corrected    = output_package["corrected_design"]
    cost         = output_package.get("cost_estimate", {})
    time_est     = output_package.get("time_estimate", {})
    seq_path     = output_package.get("sequential_path", [])
    reasoning    = output_package.get("reasoning", {})
    boq_rec      = output_package["boq_recommended"]
    pdf_report   = output_package["pdf_report"]
    final_status = output_package["status"]
    is_pass      = "PASS" in final_status

    _currency, _symbol, _region = _get_currency_info(project_data)

    orig_fw   = original.get("foundation_width",  "—")
    orig_fl   = original.get("foundation_length", "—")
    orig_cap  = original.get("column_capacity",   "—")
    orig_sp   = original.get("soil_pressure",     "—")
    orig_su   = original.get("soil_utilization",  "—")
    orig_cu   = original.get("column_utilization","—")
    orig_area = original.get("foundation_area",   "—")

    corr_fw   = corrected.get("foundation_width",  "—")
    corr_fl   = corrected.get("foundation_length", "—")
    corr_cap  = corrected.get("column_capacity",   "—")
    corr_sp   = corrected.get("soil_pressure",     "—")
    corr_su   = corrected.get("soil_utilization",  "—")
    corr_cu   = corrected.get("column_utilization","—")
    corr_area = corrected.get("foundation_area",   "—")

    proj_name  = project_data.get("project_name",   "—")
    proj_type  = project_data.get("building_type",  "—")
    proj_w     = project_data.get("building_width",  "—")
    proj_l     = project_data.get("building_length", "—")
    proj_f     = project_data.get("num_floors",      "—")
    total_load = project_data.get("total_load",      "—")
    soil_cap   = project_data.get("soil_capacity",   "—")
    n_steps    = len(seq_path)

    total_cost = int(cost.get("combined_total_cost_thb", 0))
    total_days = time_est.get("combined_total_days", 0)
    fp_cost    = int(cost.get("foundation_phase_cost_thb", 0))
    fp_days    = time_est.get("foundation_phase_days", 0)
    cu_cost    = int(cost.get("column_upgrade_cost_thb", 0))
    cu_days    = time_est.get("column_upgrade_phase_days", 0)

    status_cls  = "kf-header-status-pass" if is_pass else "kf-header-status-fail"
    status_icon = "&#10003; PASS" if is_pass else "&#10007; FAIL"

    # ── FIX: Design Classification uses BOTH soil + column ──
    eng_mode, eng_interp = _classify_design(corr_su, corr_cu)

    try:
        orig_sp_f  = float(orig_sp)
        soil_cap_f = float(soil_cap)
        excess_pct = round((orig_sp_f / soil_cap_f - 1) * 100)
        phys_line1 = f"Applied load ({total_load} kN) over {orig_area} m² → {orig_sp} kN/m² > soil capacity ({soil_cap} kN/m²)"
        phys_line2 = f"Soil pressure exceeds capacity by {excess_pct}% → soil governs failure"
        phys_line3 = f"Foundation expanded to {corr_fw} × {corr_fl} m → area = {corr_area} m² → pressure stabilized at {corr_sp} kN/m²"
    except Exception:
        phys_line1 = "Insufficient foundation area causes excessive soil bearing pressure"
        phys_line2 = "Soil pressure exceeds capacity limit"
        phys_line3 = f"Foundation expanded to {corr_fw} x {corr_fl} m — pressure stabilized"

    try:
        orig_cu_f  = float(orig_cu)
        orig_su_f  = float(orig_su)
        tradeoff_a_stat = "FAIL" if orig_cu_f > PASS_LIMIT else "PASS"
        tradeoff_c_stat = "FAIL" if orig_su_f > PASS_LIMIT else "PASS"
    except Exception:
        tradeoff_a_stat = "FAIL"
        tradeoff_c_stat = "FAIL"

    # ── Tolerance note flag (Cross Clover fix V9.9.1) ──
    try:
        _corr_su_f = float(corr_su)
        _corr_cu_f = float(corr_cu)
        _show_tolerance_note = (
            1.000 < _corr_su_f <= PASS_LIMIT or
            1.000 < _corr_cu_f <= PASS_LIMIT
        )
    except (TypeError, ValueError):
        _show_tolerance_note = False

    # ── CSS ──
    st.markdown("""
    <style>
    .kf-wrap{border:1px solid #e0e0de;border-radius:8px;overflow:hidden;margin-bottom:16px;font-family:'DM Mono',monospace}
    .kf-header{display:flex;justify-content:space-between;align-items:center;padding:12px 20px;background:#f0f0ee;border-bottom:1px solid #ddd}
    .kf-header-brand{font-size:13px;font-weight:700;letter-spacing:.04em;color:#111}
    .kf-header-project{font-size:11px;color:#888;letter-spacing:.06em;margin-top:2px}
    .kf-header-status-pass{font-size:11px;font-weight:600;color:#fff;background:#444;padding:4px 14px;border-radius:4px;letter-spacing:.06em}
    .kf-header-status-fail{font-size:11px;font-weight:600;color:#fff;background:#7a3a3a;padding:4px 14px;border-radius:4px;letter-spacing:.06em}
    .kf-impact-top{padding:20px 24px;background:#fff;border-bottom:1px solid #e8e8e6;display:flex;gap:48px;align-items:flex-end}
    .kf-impact-main-num{font-size:34px;font-weight:500;color:#111;line-height:1;letter-spacing:-.01em}
    .kf-impact-main-unit{font-size:11px;color:#aaa;letter-spacing:.08em;margin-top:4px}
    .kf-impact-sub{font-size:11px;color:#888;margin-top:10px}
    .kf-result-strip{display:flex;gap:0;border-bottom:1px solid #e8e8e6;background:#fafaf8}
    .kf-result-cell{flex:1;padding:10px 20px;border-right:1px solid #e8e8e6}
    .kf-result-cell:last-child{border-right:none}
    .kf-result-label{font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
    .kf-result-val{font-size:14px;font-weight:500;color:#111}
    .kf-result-status{font-size:13px;font-weight:500;color:#111}
    .kf-cell-label{font-size:9px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#bbb;margin-bottom:8px}
    .kf-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px;font-size:11px}
    .kf-row-key{color:#aaa}
    .kf-row-val{font-weight:400;color:#444}
    .kf-row-val.bad{color:#999}
    .phys-wrap{padding:14px 20px;background:#fafaf8;font-family:'DM Mono',monospace}
    .phys-label{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#bbb;margin-bottom:8px}
    .phys-line{font-size:11px;color:#666;margin-bottom:4px;line-height:1.6}
    .to-wrap{padding:14px 20px;background:#fff;font-family:'DM Mono',monospace}
    .to-label{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#bbb;margin-bottom:8px}
    .to-table{width:100%;border-collapse:collapse;font-size:11px}
    .to-table th{font-size:9px;color:#aaa;letter-spacing:.08em;text-transform:uppercase;text-align:left;padding:4px 8px;border-bottom:1px solid #eee;font-weight:500}
    .to-table td{padding:5px 8px;color:#555;border-bottom:1px solid #f5f5f3}
    .to-table td:last-child{font-weight:600}
    .to-table tr.selected td{color:#111;background:#f8f8f6}
    .eng-wrap{padding:12px 20px;background:#f8f8f6;font-family:'DM Mono',monospace;display:flex;gap:16px;align-items:center}
    .eng-label{font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase}
    .eng-mode{font-size:12px;font-weight:600;color:#333}
    .eng-interp{font-size:10px;color:#999;margin-top:1px}
    .det-sec{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#bbb;border-bottom:1px solid #eee;padding-bottom:5px;margin:18px 0 10px}
    .det-table{width:100%;border-collapse:collapse}
    .det-table td{font-size:11px;padding:5px 8px;border-bottom:1px solid #f5f5f3;font-family:'DM Mono',monospace;color:#555}
    .det-table td:first-child{color:#aaa;width:55%}
    .det-table td:last-child{font-weight:500;color:#222;text-align:right}
    .tol-note{border:1px solid #d6c97a;border-radius:6px;background:#fdfbee;padding:10px 16px;
              font-family:'DM Mono',monospace;font-size:11px;color:#7a6f2e;margin-top:8px;line-height:1.6}
    .tol-note-label{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
                    color:#a89a3a;margin-bottom:5px}
    </style>
    """, unsafe_allow_html=True)

    # ── FAIL → FIX banner ──
    if original.get("status") == "FAIL" and is_pass:
        st.markdown("""
        <div style="background:#f8f8f6;border:1px solid #e0e0de;border-radius:6px;
                    padding:10px 18px;margin-bottom:12px;font-family:'DM Mono',monospace;
                    display:flex;align-items:center;gap:12px;">
          <span style="font-size:13px;color:#888">&#10007; Current design fails</span>
          <span style="color:#bbb;font-size:13px">&rarr;</span>
          <span style="font-size:13px;font-weight:600;color:#333">Engineering correction applied &rarr; PASS</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Header + Impact + Result strip ──
    st.markdown(f"""
    <div class="kf-wrap">
      <div class="kf-header">
        <div>
          <div class="kf-header-brand">TRIPLEBOT V9</div>
          <div class="kf-header-project">{proj_name} &nbsp;&middot;&nbsp; {proj_type} &nbsp;&middot;&nbsp; {proj_w}&times;{proj_l} m &nbsp;&middot;&nbsp; {proj_f} Floors &nbsp;&middot;&nbsp; {_region}</div>
        </div>
        <div class="{status_cls}">{status_icon} &mdash; {final_status}</div>
      </div>
      <div class="kf-impact-top">
        <div>
          <div style="font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px">Total Cost</div>
          <div class="kf-impact-main-num">{_symbol}{total_cost:,}</div>
          <div class="kf-impact-main-unit">{_currency}</div>
          <div class="kf-impact-sub">{_symbol}{fp_cost:,} foundation &nbsp;&middot;&nbsp; {_symbol}{cu_cost:,} column upgrade</div>
        </div>
        <div>
          <div style="font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px">Total Duration</div>
          <div class="kf-impact-main-num">{total_days:.1f}</div>
          <div class="kf-impact-main-unit">DAYS</div>
          <div class="kf-impact-sub">{fp_days:.1f} d foundation &nbsp;&middot;&nbsp; {cu_days:.1f} d column upgrade</div>
        </div>
      </div>
      <div class="kf-result-strip">
        <div class="kf-result-cell">
          <div class="kf-result-label">Final Status</div>
          <div class="kf-result-status">{status_icon} {final_status}</div>
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

    # ── Problem / Decision ──
    col_prob, col_dec = st.columns(2)

    with col_prob:
        st.markdown('<div class="kf-cell-label">Problem</div>', unsafe_allow_html=True)
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

    # ── Physical Explanation ──
    st.markdown(f"""
    <div class="phys-wrap" style="border:1px solid #e8e8e6;border-radius:6px;margin-top:8px">
      <div class="phys-label">Physical Explanation</div>
      <div class="phys-line">{phys_line1}</div>
      <div class="phys-line">{phys_line2}</div>
      <div class="phys-line" style="color:#444">{phys_line3}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Trade-Off Snapshot ──
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

    # ── Engineering Label (FIX: uses _classify_design) ──
    st.markdown(f"""
    <div class="eng-wrap" style="border:1px solid #e8e8e6;border-radius:6px;margin-top:8px">
      <div>
        <div class="eng-label">Design Classification</div>
        <div class="eng-mode">{eng_mode}</div>
        <div class="eng-interp">{eng_interp}</div>
      </div>
      <div style="border-left:1px solid #e0e0de;padding-left:16px;margin-left:8px">
        <div class="eng-label">Soil Util. at Correction</div>
        <div class="eng-mode">{corr_su}</div>
        <div class="eng-interp">Limit = 1.010 (Engineering Tolerance)</div>
      </div>
      <div style="border-left:1px solid #e0e0de;padding-left:16px;margin-left:8px">
        <div class="eng-label">Column Util. at Correction</div>
        <div class="eng-mode">{corr_cu}</div>
        <div class="eng-interp">Limit = 1.010 (Engineering Tolerance)</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tolerance Note (Cross Clover fix V9.9.1) ──
    # แสดงเมื่อ utilization อยู่ใน band 1.000–1.010
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

    # ── Technical Detail ──
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
        with c2:
            st.markdown('<div class="det-sec">Correction Path</div>', unsafe_allow_html=True)
            for s in seq_path:
                st.markdown(f"""<table class="det-table">
                  <tr><td>Step {s["step_number"]} &mdash; {s["action"]}</td><td>{s["status"]}</td></tr>
                  <tr><td>Foundation</td><td>{s["foundation_width"]:.2f} x {s["foundation_length"]:.2f} m</td></tr>
                  <tr><td>Column Cap.</td><td>{s["column_capacity"]:.0f} kN</td></tr>
                  <tr><td>Soil Util.</td><td>{s["soil_utilization"]:.3f}</td></tr>
                  <tr><td>Column Util.</td><td>{s["column_utilization"]:.3f}</td></tr>
                </table><div style="margin:8px 0"></div>""", unsafe_allow_html=True)
            st.markdown('<div class="det-sec">Decision Reasoning</div>', unsafe_allow_html=True)
            st.markdown(f"""<table class="det-table">
              <tr><td>Primary Reason</td><td>{reasoning.get("primary_reason","—")}</td></tr>
              <tr><td>Governing Logic</td><td>{reasoning.get("governing_explanation","—")}</td></tr>
              <tr><td>Confidence</td><td>{reasoning.get("confidence_in_selected_action","—")}</td></tr>
            </table>""", unsafe_allow_html=True)

    st.divider()

    col_dl, col_new = st.columns([2, 1])
    with col_dl:
        st.download_button(
            label="Download PDF Report",
            data=pdf_report,
            file_name=f"triplebot_v9_{project_data['project_name'].replace(' ','_')}_report.pdf",
            mime="application/pdf",
            type="primary"
        )
    with col_new:
        if st.button("Start New Project"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.caption("Preliminary assessment only. Final verification by a licensed structural engineer required.")
    st.caption("Triple Bot V9 — Deterministic Engine · No generative AI · All results reproducible.")
