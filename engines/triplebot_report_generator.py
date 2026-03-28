from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
import io
import math


# ============================================
# TRIPLE BOT V9.9.5
# PDF REPORT GENERATOR
# FULL FILE REPLACEMENT
# FIX:
# - Add Input Reliability / Data Source table to PDF
# - Include USER INPUT / SYSTEM ASSUMPTION / INTERNAL RULE
# - Include Foundation Depth as SYSTEM DEFAULT
# - Include Cost Rates as INTERNAL BENCHMARK
# - Keep heading + table together where possible
# - Keep existing wording / stability logic intact
# ============================================

PASS_LIMIT = 1.010
DEFAULT_FOUNDATION_DEPTH = 0.4


def _safe_float(value):
    try:
        number = float(value)
        if math.isfinite(number):
            return number
        return None
    except (TypeError, ValueError):
        return None


def _fmt_num(value, decimals=3, suffix=""):
    number = _safe_float(value)
    if number is None:
        return "N/A"
    return f"{number:,.{decimals}f}{suffix}"


def _fmt_money(value, suffix=" THB"):
    number = _safe_float(value)
    if number is None:
        return "N/A"
    return f"{number:,.0f}{suffix}"


def _fmt_text(value):
    if value is None:
        return "N/A"
    text = str(value).strip()
    return text if text else "N/A"


def _fmt_boq_volume(value, suffix=" m³"):
    """
    Guard against BOQ values that are 1000x too large.
    """
    number = _safe_float(value)
    if number is None:
        return "N/A"
    if number > 1000:
        number = number / 1000
    return f"{number:,.3f}{suffix}"


def _fmt_boq_weight(value, suffix=" kg"):
    """
    Guard against reinforcement values that are 1000x too large.
    """
    number = _safe_float(value)
    if number is None:
        return "N/A"
    if number > 100000:
        number = number / 1000
    return f"{number:,.3f}{suffix}"


def _classify_design_pdf(su_val, cu_val, pass_limit=PASS_LIMIT):
    """
    Classification based on BOTH soil and column utilization.
    """
    if su_val is None or cu_val is None:
        return "N/A"
    max_util = max(su_val, cu_val)
    if max_util <= 0.85:
        return "CONSERVATIVE"
    elif max_util <= 1.0:
        return "EFFICIENT"
    elif max_util <= pass_limit:
        return "OPTIMIZED"
    else:
        return "OVER-LIMIT"


def _interpret_util_text(val, label="utilization"):
    """
    Dynamic interpretation text based on actual value.
    """
    if val is None:
        return f"N/A — {label}"
    if val <= 0.85:
        return f"{val:.3f} — safe with remaining margin"
    elif val <= 1.0:
        return f"{val:.3f} — near capacity limit"
    elif val <= PASS_LIMIT:
        return f"{val:.3f} — at capacity limit (within engineering tolerance)"
    else:
        return f"{val:.3f} — exceeds capacity limit"


def _get_step_number(step, default_index):
    for key in ["step_number", "step", "index"]:
        value = step.get(key)
        number = _safe_float(value)
        if number is not None:
            return int(number)
    return default_index


def _get_next_required_action_text(next_required_action):
    if next_required_action is None:
        return "No further action required"
    if isinstance(next_required_action, str):
        text = next_required_action.strip()
        return text if text else "No further action required"
    if isinstance(next_required_action, dict):
        action = _fmt_text(next_required_action.get("action", "N/A"))
        reason = next_required_action.get("reason")
        if reason:
            return f"{action} — {reason}"
        return action
    return "No further action required"


def _get_foundation_phase_days(time_estimate, phase_times):
    if isinstance(phase_times, dict):
        fp = phase_times.get("foundation")
        if isinstance(fp, dict):
            d = _safe_float(fp.get("estimated_days"))
            if d is not None:
                return d
    d = _safe_float(time_estimate.get("foundation_phase_days"))
    return d


def _get_column_phase_days(time_estimate, phase_times):
    if isinstance(phase_times, dict):
        cp = phase_times.get("column_upgrade")
        if isinstance(cp, dict):
            d = _safe_float(cp.get("estimated_days"))
            if d is not None:
                return d
    d = _safe_float(time_estimate.get("column_upgrade_phase_days"))
    return d


def _is_within_pass_limit(value, pass_limit=PASS_LIMIT):
    number = _safe_float(value)
    if number is None:
        return False
    return number <= pass_limit


def _get_mark(value):
    return "✓" if _is_within_pass_limit(value) else "✗"


def _get_original_values(result, prebim, corrected, sequential_path, cost_estimate):
    """
    Recover original values robustly for:
    - no-action case
    - single-step correction
    - sequential correction
    """
    original_design = result.get("original_design", {}) or {}

    def _first_number(*candidates):
        for item in candidates:
            value = _safe_float(item)
            if value is not None:
                return value
        return None

    def _get_total_load():
        cap = _safe_float(corrected.get("column_capacity"))
        util = _safe_float(corrected.get("column_utilization"))
        if cap is not None and util is not None:
            tl = cap * util
            if tl > 0:
                return tl
        return _safe_float(result.get("total_load"))

    total_load = _get_total_load()

    orig_soil_pressure = _first_number(
        original_design.get("soil_pressure"),
        result.get("soil_pressure"),
        (prebim or {}).get("soil_pressure"),
        corrected.get("soil_pressure"),
    )

    orig_area = _first_number(
        original_design.get("foundation_area"),
        result.get("foundation_area"),
        (prebim or {}).get("foundation_area"),
        corrected.get("foundation_area"),
    )

    orig_w = _first_number(
        original_design.get("foundation_width"),
        result.get("foundation_width"),
    )
    orig_l = _first_number(
        original_design.get("foundation_length"),
        result.get("foundation_length"),
    )

    if orig_w is None and orig_l is None and orig_area is not None:
        side = math.sqrt(orig_area)
        orig_w = side
        orig_l = side

    if orig_w is None:
        orig_w = _safe_float(corrected.get("foundation_width"))
    if orig_l is None:
        orig_l = _safe_float(corrected.get("foundation_length"))

    orig_col_cap = _first_number(
        original_design.get("column_capacity"),
        result.get("column_capacity"),
    )

    corr_cap = _safe_float(corrected.get("column_capacity"))
    inc = _safe_float(cost_estimate.get("column_upgrade_capacity_increase_kn"))

    if orig_col_cap is None and corr_cap is not None:
        if inc is not None and inc > 0:
            orig_col_cap = corr_cap - inc
        elif not sequential_path:
            orig_col_cap = corr_cap

    if orig_col_cap is None and sequential_path:
        first_step = sequential_path[0]
        first_cap = _safe_float(first_step.get("column_capacity"))
        first_action = str(first_step.get("action", "")).strip().upper()

        if first_cap is not None:
            if first_action == "COLUMN_UPGRADE" and inc is not None and inc > 0:
                orig_col_cap = first_cap - inc
            else:
                orig_col_cap = first_cap

    orig_soil_util = _first_number(
        original_design.get("soil_utilization"),
        result.get("soil_utilization"),
        corrected.get("soil_utilization") if not sequential_path else None,
    )

    orig_col_util = _first_number(
        original_design.get("column_utilization"),
        result.get("column_utilization"),
        corrected.get("column_utilization") if not sequential_path else None,
    )

    if orig_area is None and total_load is not None and orig_soil_pressure is not None and orig_soil_pressure > 0:
        orig_area = total_load / orig_soil_pressure

    orig_status = _fmt_text(
        original_design.get("status", result.get("status", result.get("final_status", "N/A")))
    )

    return {
        "foundation_width":   orig_w,
        "foundation_length":  orig_l,
        "foundation_area":    orig_area,
        "soil_pressure":      orig_soil_pressure,
        "soil_utilization":   orig_soil_util,
        "column_capacity":    orig_col_cap,
        "column_utilization": orig_col_util,
        "status":             orig_status,
    }


def _build_correction_type_text(sequential_path, final_status):
    step_count = len(sequential_path)

    if step_count == 0:
        return "No corrective action required"

    if step_count == 1:
        action = _fmt_text(sequential_path[0].get("action"))
        if "PASS" in str(final_status).upper():
            return f"Single-step deterministic correction ({action})"
        return f"Single-step corrective attempt ({action})"

    return f"Sequential ({step_count}-step) deterministic path"


def _build_governing_failure_text(final_status, governing_mode, orig_su_val, orig_cu_val, orig_sp_val, soil_cap_val):
    final_status_text = str(final_status).upper()

    if "PASS" in final_status_text and \
       (orig_su_val is not None and orig_su_val <= PASS_LIMIT) and \
       (orig_cu_val is not None and orig_cu_val <= PASS_LIMIT):
        return "No governing failure — current design is within engineering limit"

    if governing_mode == "COLUMN":
        if orig_cu_val is not None and orig_cu_val > 1.0:
            col_excess_pct = round((orig_cu_val - 1) * 100)
            return f"Column capacity exceeded by {col_excess_pct}%"
        return "Column capacity insufficient"

    if governing_mode == "SOIL":
        if orig_sp_val is not None and soil_cap_val is not None and soil_cap_val > 0 and orig_sp_val > soil_cap_val:
            excess_pct = round((orig_sp_val / soil_cap_val - 1) * 100)
            return f"Soil bearing capacity exceeded by {excess_pct}%"
        if orig_su_val is not None and orig_su_val > 1.0:
            excess_pct = round((orig_su_val - 1) * 100)
            return f"Soil bearing capacity exceeded by {excess_pct}%"
        return "Soil bearing limit governs"

    return "Governing failure requires engineering review"


def _build_interpretation_note(eng_mode, sequential_path, final_status):
    step_count = len(sequential_path)
    final_status_text = str(final_status).upper()

    if step_count == 0 and "PASS" in final_status_text:
        return "Current design passes without corrective action and remains within engineering tolerance ≤1.010."

    if step_count == 1 and "PASS" in final_status_text:
        return "Single corrective action achieved PASS within engineering tolerance ≤1.010."

    if step_count >= 2 and "PASS" in final_status_text:
        return "Sequential correction achieved PASS within engineering tolerance ≤1.010."

    if eng_mode == "CONSERVATIVE":
        return "Design has significant safety margin. Foundation and column both remain comfortably within safe range."

    if eng_mode in ("EFFICIENT", "OPTIMIZED"):
        return "Correction is efficient and controlled — not unnecessary overdesign."

    return "Exceeds engineering tolerance — further redesign required."


def _build_pdf_reliability_rows(result, cost_estimate, foundation_depth=DEFAULT_FOUNDATION_DEPTH):
    """
    Build explicit Input Reliability / Data Source rows for PDF.
    Priority:
    1) trust.input_reliability.rows from validation layer
    2) append PDF-only missing rows: Foundation Depth + Cost Rates
    """
    rows = []
    seen_labels = set()

    trust = result.get("trust", {}) or {}
    input_reliability = trust.get("input_reliability", {}) or {}
    source_rows = input_reliability.get("rows", []) or []

    def _add_row(label, value_display, source, note):
        key = _fmt_text(label).lower()
        if key in seen_labels:
            return
        seen_labels.add(key)
        rows.append([
            _fmt_text(label),
            _fmt_text(value_display),
            _fmt_text(source),
            _fmt_text(note),
        ])

    for row in source_rows:
        _add_row(
            row.get("label"),
            row.get("value_display"),
            row.get("source"),
            row.get("note"),
        )

    _add_row(
        "Foundation Depth",
        f"{foundation_depth:.3f} m",
        "SYSTEM DEFAULT",
        "Default depth used for preliminary BOQ and cost estimate.",
    )

    concrete_rate = cost_estimate.get("concrete_rate_thb_per_m3")
    excavation_rate = cost_estimate.get("excavation_rate_thb_per_m3")
    reinforcement_rate = cost_estimate.get("reinforcement_rate_thb_per_kg")
    column_rate = cost_estimate.get("column_upgrade_rate_thb_per_kn")

    if concrete_rate is not None:
        _add_row(
            "Concrete Rate",
            f"{_fmt_num(concrete_rate, 0)} THB/m³",
            "INTERNAL BENCHMARK",
            "Internal benchmark rate used for preliminary concrete cost.",
        )

    if excavation_rate is not None:
        _add_row(
            "Excavation Rate",
            f"{_fmt_num(excavation_rate, 0)} THB/m³",
            "INTERNAL BENCHMARK",
            "Internal benchmark rate used for preliminary excavation cost.",
        )

    if reinforcement_rate is not None:
        _add_row(
            "Reinforcement Rate",
            f"{_fmt_num(reinforcement_rate, 2)} THB/kg",
            "INTERNAL BENCHMARK",
            "Internal benchmark rate used for preliminary reinforcement cost.",
        )

    if column_rate is not None:
        _add_row(
            "Column Upgrade Rate",
            f"{_fmt_num(column_rate, 2)} THB/kN",
            "INTERNAL BENCHMARK",
            "Internal benchmark rate used for deterministic column upgrade estimate.",
        )

    return rows


# ── Style helpers ──

DARK   = colors.HexColor("#1e1e1e")
MID    = colors.HexColor("#444444")
LIGHT  = colors.HexColor("#888888")
RULE   = colors.HexColor("#e0e0de")
WHITE  = colors.white
OFF    = colors.HexColor("#fafaf8")
LGRAY  = colors.HexColor("#f0f0ee")


def _section_label(text, styles):
    return Paragraph(
        f'<font size="8" color="#aaaaaa"><b>{text.upper()}</b></font>',
        styles["Normal"]
    )


def _kf_table(data, col_widths):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#999999")),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK),
        ("FONTNAME",  (1, 0), (1, -1), "Helvetica-Bold"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, -1), (-1, -1), 0, WHITE),
    ]))
    return t


def _detail_table(header, rows):
    data = [header] + rows
    usable = 170 * mm
    t = Table(data, colWidths=[usable * 0.42, usable * 0.58], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#f5f5f3")),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR",     (0, 0), (-1, 0), LIGHT),
        ("TEXTCOLOR",     (0, 1), (-1, -1), MID),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.3, RULE),
        ("LINEBELOW",     (0, 1), (-1, -1), 0.2, colors.HexColor("#f0f0ee")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("WORDWRAP",      (0, 0), (-1, -1), True),
    ]))
    return t


def _reliability_table(rows):
    usable = 166 * mm
    data = [["Field", "Value", "Source", "Note"]] + rows

    t = Table(
        data,
        colWidths=[usable * 0.22, usable * 0.16, usable * 0.18, usable * 0.44],
        hAlign="LEFT",
        repeatRows=1
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#f5f5f3")),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.8),
        ("TEXTCOLOR",     (0, 0), (-1, 0), LIGHT),
        ("TEXTCOLOR",     (0, 1), (-1, -1), MID),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.3, RULE),
        ("LINEBELOW",     (0, 1), (-1, -1), 0.2, colors.HexColor("#f0f0ee")),
        ("BOX",           (0, 0), (-1, -1), 0.3, RULE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.2, colors.HexColor("#f0f0ee")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("WORDWRAP",      (0, 0), (-1, -1), True),
    ]))
    return t


def generate_engineering_report(
    result,
    intelligence,
    prebim,
    boq,
    decision,
    cost_estimate=None,
    time_estimate=None,
    sequential_path=None,
    action_outcome=None,
    next_required_action=None,
    phase_costs=None,
    phase_times=None,
    region=None,
):
    buffer = io.BytesIO()
    page_w, page_h = A4

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=13, textColor=MID)
    SMALL = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=11, textColor=LIGHT)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=10, leading=14, textColor=DARK, spaceAfter=4)
    H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=9, leading=12, textColor=MID, spaceAfter=2)
    TITLE = ParagraphStyle("Title", parent=styles["Title"], fontSize=16, leading=20, textColor=DARK)
    DISCLAIMER = ParagraphStyle("Disc", parent=styles["Normal"], fontSize=7.5, leading=11, textColor=LIGHT)

    cost_estimate = cost_estimate or {}
    time_estimate = time_estimate or result.get("time_estimate", {}) or {}
    sequential_path = sequential_path or result.get("sequential_path", []) or []
    action_outcome = action_outcome or result.get("action_outcome", []) or []
    phase_costs = phase_costs or {}
    phase_times = phase_times or {}

    reliability_rows = _build_pdf_reliability_rows(
        result=result,
        cost_estimate=cost_estimate,
        foundation_depth=DEFAULT_FOUNDATION_DEPTH,
    )

    final_status = result.get("final_status", result.get("status", "N/A"))
    corrected = result.get("corrected_design", {}) or {}
    original = _get_original_values(result, prebim or {}, corrected, sequential_path, cost_estimate)

    is_pass = "PASS" in str(final_status).upper()
    no_action_case = is_pass and len(sequential_path) == 0

    currency_map = {
        "Thailand": ("THB", ""),
        "China": ("CNY", "¥"),
        "United States": ("USD", "$"),
    }
    currency, symbol = currency_map.get(region or "Thailand", ("THB", ""))

    combined_cost = _safe_float(cost_estimate.get("combined_total_cost_thb")) or 0
    combined_days = _safe_float(time_estimate.get("combined_total_days")) or 0
    found_phase_cost = _safe_float(cost_estimate.get("foundation_phase_cost_thb")) or 0
    col_phase_cost = _safe_float(cost_estimate.get("column_upgrade_cost_thb")) or 0
    found_phase_days = _get_foundation_phase_days(time_estimate, phase_times) or 0
    col_phase_days = _get_column_phase_days(time_estimate, phase_times) or 0

    usable_w = page_w - 40 * mm
    half = usable_w / 2 - 3 * mm

    elements = []

    # ══════════════════════════════════════════
    # PAGE 1 — KILLER FRAME
    # ══════════════════════════════════════════

    header_data = [[
        Paragraph(
            '<font size="14" color="#111111"><b>TRIPLEBOT</b></font> <font size="9" color="#888888">V9</font>',
            styles["Normal"]
        ),
        Paragraph(
            '<font size="8" color="#aaaaaa">ENGINEERING DECISION INTELLIGENCE · DETERMINISTIC ENGINE</font>',
            styles["Normal"]
        ),
        Paragraph(
            f'<font size="10" color="#111111"><b>{"&#10003; PASS" if is_pass else "&#10007; FAIL"}</b></font>',
            styles["Normal"]
        )
    ]]
    header_t = Table(header_data, colWidths=[usable_w * 0.3, usable_w * 0.5, usable_w * 0.2])
    header_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LGRAY),
        ("TEXTCOLOR",     (0, 0), (-1, -1), DARK),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (2, 0), (2, 0), "RIGHT"),
    ]))
    elements.append(header_t)
    elements.append(Spacer(1, 8))

    def _quad_label(text):
        return Paragraph(f'<font size="7.5" color="#aaaaaa"><b>{text}</b></font>', styles["Normal"])

    def _quad_row(key, val, val_color="#111111"):
        return [
            Paragraph(f'<font size="9" color="#999999">{key}</font>', styles["Normal"]),
            Paragraph(f'<font size="9" color="{val_color}"><b>{val}</b></font>', styles["Normal"]),
        ]

    problem_section_label = "CURRENT DESIGN" if no_action_case else "PROBLEM"

    prob_rows = [
        _quad_row("Initial Status", _fmt_text(original["status"]), "#333333"),
        _quad_row("Soil Utilization", f"{_fmt_num(original['soil_utilization'], 3)} {_get_mark(original['soil_utilization'])}", "#777777"),
        _quad_row("Column Utilization", f"{_fmt_num(original['column_utilization'], 3)} {_get_mark(original['column_utilization'])}", "#777777"),
        _quad_row("Soil Pressure", f"{_fmt_num(original['soil_pressure'], 3)} kN/m²", "#777777"),
        _quad_row("Foundation", f"{_fmt_num(original['foundation_width'], 2)} × {_fmt_num(original['foundation_length'], 2)} m", "#777777"),
        _quad_row("Column Cap.", f"{_fmt_num(original['column_capacity'], 0)} kN", "#777777"),
    ]
    prob_data = [[_quad_label(problem_section_label), ""], *prob_rows]

    dec_rows = []
    if sequential_path:
        for s in sequential_path:
            dec_rows.append(_quad_row(f"Step {s['step_number']}", _fmt_text(s["action"])))
        dec_rows += [
            _quad_row("Foundation", f"{_fmt_num(original['foundation_width'], 2)} → {_fmt_num(corrected.get('foundation_width'), 2)} m"),
            _quad_row("Column Cap.", f"{_fmt_num(original['column_capacity'], 0)} → {_fmt_num(corrected.get('column_capacity'), 0)} kN"),
            _quad_row("Corrections", f"{len(sequential_path)} applied"),
        ]
    else:
        dec_rows += [
            _quad_row("Action", "NO_ACTION"),
            _quad_row("Foundation", f"{_fmt_num(corrected.get('foundation_width'), 2)} m (unchanged)"),
            _quad_row("Column Cap.", f"{_fmt_num(corrected.get('column_capacity'), 0)} kN (unchanged)"),
            _quad_row("Corrections", "0 applied"),
        ]
    dec_data = [[_quad_label("DECISION"), ""], *dec_rows]

    res_data = [
        [_quad_label("RESULT"), ""],
        *[_quad_row(k, v, "#222222") for k, v in [
            ("Final Status", f"{_fmt_text(final_status)}"),
            ("Soil Utilization", f"{_fmt_num(corrected.get('soil_utilization'), 3)} ✓"),
            ("Column Utilization", f"{_fmt_num(corrected.get('column_utilization'), 3)} ✓"),
            ("Soil Pressure", f"{_fmt_num(corrected.get('soil_pressure'), 3)} kN/m²"),
            ("Foundation", f"{_fmt_num(corrected.get('foundation_width'), 2)} × {_fmt_num(corrected.get('foundation_length'), 2)} m"),
            ("Column Cap.", f"{_fmt_num(corrected.get('column_capacity'), 0)} kN"),
        ]]
    ]

    impact_rows = [
        [
            Paragraph('<font size="8" color="#999999">Total Cost</font>', styles["Normal"]),
            Paragraph(
                f'<font size="18" color="#111111"><b>{symbol}{int(combined_cost):,}</b></font> <font size="9" color="#aaaaaa">{currency}</font>',
                styles["Normal"]
            ),
        ],
        [
            Paragraph('<font size="8" color="#999999">Total Duration</font>', styles["Normal"]),
            Paragraph(
                f'<font size="18" color="#111111"><b>{combined_days:.1f}</b></font> <font size="9" color="#aaaaaa">days</font>',
                styles["Normal"]
            ),
        ],
        _quad_row("Foundation Phase", f"{symbol}{int(found_phase_cost):,} {currency} · {found_phase_days:.1f} d"),
        _quad_row("Column Upgrade", f"{symbol}{int(col_phase_cost):,} {currency} · {col_phase_days:.1f} d"),
    ]
    imp_data = [[_quad_label("IMPACT"), ""], *impact_rows]

    def _make_quad(data):
        t = Table(data, colWidths=[half * 0.52, half * 0.48])
        t.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("SPAN",          (0, 0), (1, 0)),
            ("LINEBELOW",     (0, 0), (1, 0), 0.5, RULE),
        ]))
        return t

    quad_outer = Table(
        [[_make_quad(prob_data), _make_quad(dec_data)],
         [_make_quad(res_data),  _make_quad(imp_data)]],
        colWidths=[half + 3 * mm, half + 3 * mm],
    )
    quad_outer.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
    ]))
    elements.append(quad_outer)
    elements.append(Spacer(1, 6))

    proj_strip = Table([[
        Paragraph(
            f'<font size="8" color="#aaaaaa">PROJECT &nbsp; <font color="#333333">{_fmt_text(result.get("project_name", "—"))}</font></font>',
            styles["Normal"]
        ),
        Paragraph(
            f'<font size="8" color="#aaaaaa">STATUS &nbsp; <font color="#333333"><b>{_fmt_text(final_status)}</b></font></font>',
            styles["Normal"]
        ),
        Paragraph(
            '<font size="8" color="#aaaaaa">REPORT ID &nbsp; <font color="#333333">#TBV9</font></font>',
            styles["Normal"]
        ),
    ]], colWidths=[usable_w / 3] * 3)
    proj_strip.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), OFF),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.3, RULE),
    ]))
    elements.append(proj_strip)

    # ══════════════════════════════════════════
    # PAGE 2 — TECHNICAL DETAIL
    # ══════════════════════════════════════════

    elements.append(PageBreak())
    elements.append(Paragraph("Technical Detail", TITLE))
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=RULE))
    elements.append(Spacer(1, 12))

    elements.append(KeepTogether([
        Paragraph("Structural Validation", H2),
        _detail_table(
            ["Parameter", "Value"],
            [
                ["Status (initial)", _fmt_text(original.get("status"))],
                ["Column Utilization", _fmt_num(original.get("column_utilization"), 3)],
                ["Soil Utilization", _fmt_num(original.get("soil_utilization"), 3)],
                ["Governing Mode", _fmt_text(result.get("governing_mode", "N/A"))],
            ]
        ),
    ]))
    elements.append(Spacer(1, 12))

    if sequential_path:
        elements.append(Paragraph("Sequential Correction Path", H2))
        path_rows = []
        for idx, step in enumerate(sequential_path, 1):
            sn = _get_step_number(step, idx)
            path_rows.append([
                str(sn),
                _fmt_text(step.get("action")),
                f"{_fmt_num(step.get('foundation_width'), 2)}x{_fmt_num(step.get('foundation_length'), 2)} m",
                _fmt_num(step.get("column_capacity"), 0, " kN"),
                _fmt_num(step.get("soil_utilization"), 3),
                _fmt_num(step.get("column_utilization"), 3),
                _fmt_text(step.get("status")),
            ])

        usable = 166 * mm
        path_data = [["Step", "Action", "Foundation", "Col. Cap.", "Soil Util.", "Col. Util.", "Status"]] + path_rows
        path_t = Table(path_data, colWidths=[
            usable * 0.06, usable * 0.26, usable * 0.18,
            usable * 0.13, usable * 0.12, usable * 0.12, usable * 0.13
        ], hAlign="LEFT")
        path_t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#f5f5f3")),
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
            ("TEXTCOLOR",     (0, 0), (-1, 0), LIGHT),
            ("TEXTCOLOR",     (0, 1), (-1, -1), MID),
            ("LINEBELOW",     (0, 0), (-1, 0), 0.3, RULE),
            ("LINEBELOW",     (0, 1), (-1, -1), 0.2, colors.HexColor("#f0f0ee")),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(path_t)
        elements.append(Spacer(1, 6))
        for idx, step in enumerate(sequential_path, 1):
            note = step.get("note")
            if note:
                elements.append(Paragraph(f"Step {_get_step_number(step, idx)}: {note}", SMALL))
        elements.append(Spacer(1, 12))

    if action_outcome:
        elements.append(Paragraph("Action Outcome", H2))
        for item in action_outcome:
            elements.append(Paragraph(f"• {_fmt_text(item)}", BODY))
        elements.append(Spacer(1, 12))

    elements.append(KeepTogether([
        Paragraph("Next Required Action", H2),
        Paragraph(_get_next_required_action_text(next_required_action), BODY),
    ]))
    elements.append(Spacer(1, 12))

    if no_action_case:
        elements.append(KeepTogether([
            Paragraph("Final Design Confirmation", H2),
            Paragraph("No change — current design used as final design.", BODY),
            Spacer(1, 6),
            _detail_table(
                ["Parameter", "Value"],
                [
                    ["Final Status", _fmt_text(final_status)],
                    ["Engineering Action", "NO_ACTION"],
                    ["Foundation", f"{_fmt_num(corrected.get('foundation_width'), 3)} × {_fmt_num(corrected.get('foundation_length'), 3)} m"],
                    ["Column Capacity", _fmt_num(corrected.get("column_capacity"), 0, " kN")],
                    ["Soil Pressure", _fmt_num(corrected.get("soil_pressure"), 3, " kN/m²")],
                    ["Soil Utilization", _fmt_num(corrected.get("soil_utilization"), 3)],
                    ["Column Utilization", _fmt_num(corrected.get("column_utilization"), 3)],
                ]
            ),
        ]))
        elements.append(Spacer(1, 12))
    else:
        bva_data = [
            ["Metric", "Before", "After"],
            ["Foundation Width", _fmt_num(original["foundation_width"], 3, " m"), _fmt_num(corrected.get("foundation_width"), 3, " m")],
            ["Foundation Length", _fmt_num(original["foundation_length"], 3, " m"), _fmt_num(corrected.get("foundation_length"), 3, " m")],
            ["Foundation Area", _fmt_num(original["foundation_area"], 3, " m²"), _fmt_num(corrected.get("foundation_area"), 3, " m²")],
            ["Soil Pressure", _fmt_num(original["soil_pressure"], 3, " kN/m²"), _fmt_num(corrected.get("soil_pressure"), 3, " kN/m²")],
            ["Soil Utilization", _fmt_num(original["soil_utilization"], 3), _fmt_num(corrected.get("soil_utilization"), 3)],
            ["Column Capacity", _fmt_num(original["column_capacity"], 0, " kN"), _fmt_num(corrected.get("column_capacity"), 0, " kN")],
            ["Column Utilization", _fmt_num(original["column_utilization"], 3), _fmt_num(corrected.get("column_utilization"), 3)],
            ["Status", _fmt_text(original["status"]), _fmt_text(final_status)],
        ]
        usable = 166 * mm
        bva_t = Table(bva_data, colWidths=[usable * 0.38, usable * 0.31, usable * 0.31], hAlign="LEFT")
        bva_t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#f5f5f3")),
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
            ("TEXTCOLOR",     (0, 0), (-1, 0), LIGHT),
            ("TEXTCOLOR",     (0, 1), (-1, -1), MID),
            ("LINEBELOW",     (0, 0), (-1, 0), 0.3, RULE),
            ("LINEBELOW",     (0, 1), (-1, -1), 0.2, colors.HexColor("#f0f0ee")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(KeepTogether([
            Paragraph("Before vs After", H2),
            bva_t,
        ]))
        elements.append(Spacer(1, 12))

    elements.append(KeepTogether([
        Paragraph("Bill of Quantities", H2),
        _detail_table(
            ["Parameter", "Value"],
            [
                ["Foundation Area", _fmt_num(boq.get("foundation_area"), 3, " m²")],
                ["Foundation Depth", _fmt_num(boq.get("foundation_depth"), 3, " m")],
                ["Concrete Volume", _fmt_boq_volume(boq.get("concrete_volume_m3"))],
                ["Excavation Volume", _fmt_boq_volume(boq.get("excavation_volume_m3"), " m³")],
                ["Reinforcement", _fmt_boq_weight(boq.get("reinforcement_estimate"))],
            ]
        ),
    ]))
    elements.append(Spacer(1, 12))

    if cost_estimate:
        elements.append(KeepTogether([
            Paragraph("Cost Estimate", H2),
            _detail_table(
                ["Item", "Value"],
                [
                    ["Foundation Phase", _fmt_money(cost_estimate.get("foundation_phase_cost_thb"), f" {currency}")],
                    ["Column Upgrade", _fmt_money(cost_estimate.get("column_upgrade_cost_thb"), f" {currency}")],
                    ["Concrete", _fmt_money(cost_estimate.get("concrete_cost_thb"), f" {currency}")],
                    ["Excavation", _fmt_money(cost_estimate.get("excavation_cost_thb"), f" {currency}")],
                    ["Reinforcement", _fmt_money(cost_estimate.get("reinforcement_cost_thb"), f" {currency}")],
                    ["Combined Total", _fmt_money(cost_estimate.get("combined_total_cost_thb"), f" {currency}")],
                ]
            ),
        ]))
        elements.append(Spacer(1, 6))
        elements.append(KeepTogether([
            Paragraph("Cost Assumptions", H3),
            _detail_table(
                ["Benchmark", "Value"],
                [
                    ["Concrete Rate", _fmt_money(cost_estimate.get("concrete_rate_thb_per_m3"), f" {currency}/m³")],
                    ["Excavation Rate", _fmt_money(cost_estimate.get("excavation_rate_thb_per_m3"), f" {currency}/m³")],
                    ["Reinforcement Rate", _fmt_money(cost_estimate.get("reinforcement_rate_thb_per_kg"), f" {currency}/kg")],
                    ["Column Upgrade Rate", _fmt_money(cost_estimate.get("column_upgrade_rate_thb_per_kn"), f" {currency}/kN")],
                    ["Capacity Increase", _fmt_num(cost_estimate.get("column_upgrade_capacity_increase_kn"), 1, " kN")],
                ]
            ),
        ]))
        elements.append(Spacer(1, 12))

    if time_estimate:
        basis_text = _fmt_text(time_estimate.get("basis", "N/A"))
        if len(basis_text) > 80:
            basis_text = basis_text[:77] + "..."
        elements.append(KeepTogether([
            Paragraph("Time Estimate", H2),
            _detail_table(
                ["Item", "Value"],
                [
                    ["Foundation Phase", _fmt_num(_get_foundation_phase_days(time_estimate, phase_times), 1, " days")],
                    ["Column Upgrade", _fmt_num(_get_column_phase_days(time_estimate, phase_times), 1, " days")],
                    ["Combined Total", _fmt_num(_safe_float(time_estimate.get("combined_total_days")), 1, " days")],
                    ["Work Scope", _fmt_text(time_estimate.get("activity", "N/A"))],
                    ["Basis", basis_text],
                ]
            ),
        ]))
        elements.append(Spacer(1, 12))

    # NEW — INPUT RELIABILITY / DATA SOURCE
    if reliability_rows:
        elements.append(KeepTogether([
            Paragraph("Input Reliability / Data Source", H2),
            _reliability_table(reliability_rows),
        ]))
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("Assumptions & Standards", H2))
    for line in [
        "Load basis: 7.5 kN/m² — Dead Load 4.5 + Live Load 3.0 kN/m². Ref: ACI 318-19 / EIT 1007-34 / มยผ. typical residential.",
        "Cost estimate uses fixed internal benchmark rates.",
        "Time estimate uses fixed rule-based internal benchmarks.",
        "Sequential correction path is deterministic and reproducible.",
        "Engineering tolerance: utilization ≤ 1.010 = PASS. Values between 1.000–1.010 reflect deterministic rounding, not structural failure.",
        "Design scope: RC Frame 1–4 storeys, gravity load only, regular plan, firm soil (bearing capacity known).",
    ]:
        elements.append(Paragraph(f"• {line}", BODY))
    elements.append(Spacer(1, 12))

    usable_scope = 166 * mm
    scope_data = [
        [
            Paragraph('<font size="8" color="#4a7c59"><b>✓ APPLICABLE FOR</b></font>', styles["Normal"]),
            Paragraph('<font size="8" color="#a05050"><b>✗ NOT APPLICABLE FOR (RED FLAGS)</b></font>', styles["Normal"]),
        ],
        [
            Paragraph(
                '<font size="8" color="#444">✓ Reinforced Concrete (RC) Frame<br/>✓ 1–4 Storeys<br/>✓ Regular rectangular plan<br/>✓ Static gravity load only<br/>✓ Firm soil (bearing capacity known)<br/>✓ Pre-design / Feasibility stage<br/><br/>Ref: ACI 318-19 / EIT 1007-34 / มยผ.</font>',
                styles["Normal"]
            ),
            Paragraph(
                '<font size="8" color="#444">✗ Seismic zone — no lateral load analysis<br/>✗ Soft clay / peat — high settlement risk<br/>✗ Wind load — not included<br/>✗ Irregular plan / complex geometry<br/>✗ Pile foundation<br/>✗ Steel / timber frame<br/><br/><font color="#a05050"><b>Using outside scope = unsafe result</b></font></font>',
                styles["Normal"]
            ),
        ]
    ]
    scope_t = Table(scope_data, colWidths=[usable_scope * 0.5, usable_scope * 0.5], hAlign="LEFT")
    scope_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), colors.HexColor("#f0f7f0")),
        ("BACKGROUND",    (1, 0), (1, 0), colors.HexColor("#fdf0f0")),
        ("BACKGROUND",    (0, 1), (0, 1), colors.HexColor("#fafaf8")),
        ("BACKGROUND",    (1, 1), (1, 1), colors.HexColor("#fafaf8")),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.3, RULE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, RULE),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(KeepTogether([
        Paragraph("Scope of Use", H2),
        scope_t,
    ]))
    elements.append(Spacer(1, 16))

    try:
        su_val = _safe_float(corrected.get("soil_utilization"))
        cu_val = _safe_float(corrected.get("column_utilization"))
        orig_sp_val = _safe_float(original.get("soil_pressure"))
        soil_cap_val = _safe_float(result.get("soil_capacity")) or _safe_float((prebim or {}).get("soil_capacity")) or 200.0

        governing_mode = _fmt_text(result.get("governing_mode", "SOIL")).upper()
        orig_su_val = _safe_float(original.get("soil_utilization"))
        orig_cu_val = _safe_float(original.get("column_utilization"))

        governing_failure_text = _build_governing_failure_text(
            final_status=final_status,
            governing_mode=governing_mode,
            orig_su_val=orig_su_val,
            orig_cu_val=orig_cu_val,
            orig_sp_val=orig_sp_val,
            soil_cap_val=soil_cap_val,
        )

        eng_mode = _classify_design_pdf(su_val, cu_val)
        su_interp_text = _interpret_util_text(su_val, "soil utilization")
        cu_interp_text = _interpret_util_text(cu_val, "column utilization")
        correction_type_text = _build_correction_type_text(sequential_path, final_status)
        interp_note = _build_interpretation_note(eng_mode, sequential_path, final_status)

        interp_rows = [
            ["Governing failure", governing_failure_text],
            ["Correction type", correction_type_text],
            ["Final soil utilization", su_interp_text],
            ["Final column utilization", cu_interp_text],
            ["Design classification", eng_mode],
            ["Interpretation", interp_note],
        ]
        elements.append(KeepTogether([
            Paragraph("Engineering Interpretation", H2),
            _detail_table(["Parameter", "Value"], interp_rows),
        ]))
    except Exception:
        elements.append(KeepTogether([
            Paragraph("Engineering Interpretation", H2),
            Paragraph("Engineering interpretation not available.", BODY),
        ]))

    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.3, color=RULE))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "This report is generated using deterministic engineering logic. "
        "Final verification must be conducted by a licensed structural engineer. "
        "Triple Bot V9 — No generative AI · All results reproducible.",
        DISCLAIMER
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "System Positioning: Triple Bot V9 = Error-Detection & Speed-Booster. "
        "Not a replacement for engineers — a tool to eliminate repetitive checks and catch errors early. "
        "Designed for Gravity Loads on RC Frame 1–4 Storeys only. "
        "Not for Seismic Zones, Soft Clay, Wind Load, or Pile Foundation.",
        DISCLAIMER
    ))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf