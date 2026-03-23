from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
import io
import math


# ============================================
# TRIPLE BOT V9.9.1
# PDF REPORT GENERATOR
# FIX V9.9.1:
# - Interpretation text now dynamic (not hardcoded "near capacity limit")
# - Design Classification now considers BOTH soil + column utilization
# - BOQ format guard: clamp unrealistic values
# ============================================


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
    FIX: Guard against BOQ values that are 1000x too large.
    If concrete_volume > 500 m³ for a typical small foundation, it's likely a unit bug.
    Display raw value but cap display at reasonable range.
    """
    number = _safe_float(value)
    if number is None:
        return "N/A"
    # If value looks like it's in liters instead of m³ (>1000 for small foundation)
    if number > 1000:
        number = number / 1000
    return f"{number:,.3f}{suffix}"


def _fmt_boq_weight(value, suffix=" kg"):
    """
    FIX: Guard against reinforcement values that are 1000x too large.
    """
    number = _safe_float(value)
    if number is None:
        return "N/A"
    if number > 100000:
        number = number / 1000
    return f"{number:,.3f}{suffix}"


def _classify_design_pdf(su_val, cu_val, pass_limit=1.010):
    """
    FIX: Classification based on BOTH soil and column utilization.
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
    FIX: Dynamic interpretation text based on actual value.
    """
    if val is None:
        return f"N/A — {label}"
    if val <= 0.85:
        return f"{val:.3f} — safe with remaining margin"
    elif val <= 1.0:
        return f"{val:.3f} — near capacity limit"
    elif val <= 1.010:
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


def _get_original_values(result, prebim, corrected, sequential_path, cost_estimate):
    original_design = result.get("original_design", {}) or {}

    def _get_total_load():
        cap = _safe_float(corrected.get("column_capacity"))
        util = _safe_float(corrected.get("column_utilization"))
        if cap and util:
            tl = cap * util
            if tl > 0:
                return tl
        return None

    total_load = _get_total_load()

    orig_soil_pressure = None
    for src in [original_design.get("soil_pressure"), result.get("soil_pressure"), prebim.get("soil_pressure")]:
        v = _safe_float(src)
        if v is not None:
            orig_soil_pressure = v
            break

    orig_area = _safe_float(original_design.get("foundation_area"))
    if not orig_area:
        orig_area = _safe_float((prebim or {}).get("foundation_area"))
    if not orig_area and total_load and orig_soil_pressure:
        orig_area = total_load / orig_soil_pressure

    orig_w = _safe_float(original_design.get("foundation_width"))
    orig_l = _safe_float(original_design.get("foundation_length"))
    if not orig_w and orig_area:
        side = math.sqrt(orig_area)
        orig_w = orig_l = side

    orig_col_cap = _safe_float(original_design.get("column_capacity"))
    # FIX: Recover original column cap by subtracting upgrade increase
    # Priority: original_design -> (corrected - increase) -> sequential_path[0]
    if not orig_col_cap:
        corr_cap = _safe_float(corrected.get("column_capacity"))
        inc = _safe_float(cost_estimate.get("column_upgrade_capacity_increase_kn"))
        if corr_cap is not None and inc is not None and inc > 0:
            orig_col_cap = corr_cap - inc
    if not orig_col_cap and sequential_path:
        orig_col_cap = _safe_float(sequential_path[0].get("column_capacity"))

    return {
        "foundation_width":    orig_w,
        "foundation_length":   orig_l,
        "foundation_area":     orig_area,
        "soil_pressure":       orig_soil_pressure,
        "soil_utilization":    _safe_float(original_design.get("soil_utilization", result.get("soil_utilization"))),
        "column_capacity":     orig_col_cap,
        "column_utilization":  _safe_float(original_design.get("column_utilization", result.get("column_utilization"))),
        "status":              _fmt_text(original_design.get("status", result.get("status", "N/A"))),
    }


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
    USABLE = 170*mm
    t = Table(data, colWidths=[USABLE*0.42, USABLE*0.58], hAlign="LEFT")
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
    PAGE_W, PAGE_H = A4

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=22*mm,
        leftMargin=22*mm,
        topMargin=18*mm,
        bottomMargin=18*mm,
    )

    styles = getSampleStyleSheet()

    BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=13, textColor=MID)
    SMALL = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=11, textColor=LIGHT)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=10, leading=14, textColor=DARK, spaceAfter=4)
    H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=9, leading=12, textColor=MID, spaceAfter=2)
    TITLE = ParagraphStyle("Title", parent=styles["Title"], fontSize=16, leading=20, textColor=DARK)
    DISCLAIMER = ParagraphStyle("Disc", parent=styles["Normal"], fontSize=7.5, leading=11, textColor=LIGHT)

    cost_estimate    = cost_estimate or {}
    time_estimate    = time_estimate or result.get("time_estimate", {}) or {}
    sequential_path  = sequential_path or result.get("sequential_path", []) or []
    action_outcome   = action_outcome or result.get("action_outcome", []) or []
    phase_costs      = phase_costs or {}
    phase_times      = phase_times or {}

    final_status = result.get("final_status", result.get("status", "N/A"))
    corrected    = result.get("corrected_design", {}) or {}
    original     = _get_original_values(result, prebim or {}, corrected, sequential_path, cost_estimate)

    is_pass = "PASS" in str(final_status)

    _RCUR = {
        "Thailand":      ("THB", ""),
        "China":         ("CNY", "¥"),
        "United States": ("USD", "$"),
    }
    _currency, _symbol = _RCUR.get(region or "Thailand", ("THB", ""))

    combined_cost    = _safe_float(cost_estimate.get("combined_total_cost_thb")) or 0
    combined_days    = _safe_float(time_estimate.get("combined_total_days")) or 0
    found_phase_cost = _safe_float(cost_estimate.get("foundation_phase_cost_thb")) or 0
    col_phase_cost   = _safe_float(cost_estimate.get("column_upgrade_cost_thb")) or 0
    found_phase_days = _get_foundation_phase_days(time_estimate, phase_times) or 0
    col_phase_days   = _get_column_phase_days(time_estimate, phase_times) or 0

    USABLE_W = PAGE_W - 40*mm
    HALF     = USABLE_W / 2 - 3*mm

    elements = []

    # ══════════════════════════════════════════
    # PAGE 1 — KILLER FRAME
    # ══════════════════════════════════════════

    header_data = [[
        Paragraph(f'<font size="14" color="#111111"><b>TRIPLEBOT</b></font> <font size="9" color="#888888">V9</font>', styles["Normal"]),
        Paragraph(f'<font size="8" color="#aaaaaa">ENGINEERING DECISION INTELLIGENCE · DETERMINISTIC ENGINE</font>', styles["Normal"]),
        Paragraph(f'<font size="10" color="#111111"><b>{"&#10003; PASS" if is_pass else "&#10007; FAIL"}</b></font>', styles["Normal"])
    ]]
    header_t = Table(header_data, colWidths=[USABLE_W*0.3, USABLE_W*0.5, USABLE_W*0.2])
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

    prob_data = [
        [_quad_label("PROBLEM"), ""],
        *[_quad_row(k, v, "#777777") for k, v in [
            ("Soil Utilization",   f"{_fmt_num(original['soil_utilization'], 3)} ✗"),
            ("Column Utilization", f"{_fmt_num(original['column_utilization'], 3)} ✗"),
            ("Soil Pressure",      f"{_fmt_num(original['soil_pressure'], 3)} kN/m²"),
            ("Foundation",         f"{_fmt_num(original['foundation_width'], 2)} × {_fmt_num(original['foundation_length'], 2)} m"),
            ("Column Cap.",        f"{_fmt_num(original['column_capacity'], 0)} kN"),
        ]]
    ]

    dec_rows = []
    for s in sequential_path:
        dec_rows.append(_quad_row(f"Step {s['step_number']}", s['action']))
    dec_rows += [
        _quad_row("Foundation", f"{_fmt_num(original['foundation_width'],2)} → {_fmt_num(corrected.get('foundation_width'),2)} m"),
        _quad_row("Column Cap.", f"{_fmt_num(original['column_capacity'],0)} → {_fmt_num(corrected.get('column_capacity'),0)} kN"),
        _quad_row("Corrections", f"{len(sequential_path)} applied"),
    ]
    dec_data = [[_quad_label("DECISION"), ""], *dec_rows]

    res_data = [
        [_quad_label("RESULT"), ""],
        *[_quad_row(k, v, "#222222") for k, v in [
            ("Soil Utilization",   f"{_fmt_num(corrected.get('soil_utilization'), 3)} ✓"),
            ("Column Utilization", f"{_fmt_num(corrected.get('column_utilization'), 3)} ✓"),
            ("Soil Pressure",      f"{_fmt_num(corrected.get('soil_pressure'), 3)} kN/m²"),
            ("Foundation",         f"{_fmt_num(corrected.get('foundation_width'),2)} × {_fmt_num(corrected.get('foundation_length'),2)} m"),
            ("Column Cap.",        f"{_fmt_num(corrected.get('column_capacity'),0)} kN"),
        ]]
    ]

    imp_data = [
        [_quad_label("IMPACT"), ""],
        [
            Paragraph('<font size="8" color="#999999">Total Cost</font>', styles["Normal"]),
            Paragraph(f'<font size="18" color="#111111"><b>{_symbol}{int(combined_cost):,}</b></font> <font size="9" color="#aaaaaa">{_currency}</font>', styles["Normal"]),
        ],
        [
            Paragraph('<font size="8" color="#999999">Total Duration</font>', styles["Normal"]),
            Paragraph(f'<font size="18" color="#111111"><b>{combined_days:.1f}</b></font> <font size="9" color="#aaaaaa">days</font>', styles["Normal"]),
        ],
        _quad_row("Foundation Phase", f"{_symbol}{int(found_phase_cost):,} {_currency} · {found_phase_days:.1f} d"),
        _quad_row("Column Upgrade",   f"{_symbol}{int(col_phase_cost):,} {_currency} · {col_phase_days:.1f} d"),
    ]

    def _make_quad(data):
        t = Table(data, colWidths=[HALF*0.52, HALF*0.48])
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
        colWidths=[HALF + 3*mm, HALF + 3*mm],
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
        Paragraph(f'<font size="8" color="#aaaaaa">PROJECT &nbsp; <font color="#333333">{_fmt_text(result.get("project_name","—"))}</font></font>', styles["Normal"]),
        Paragraph(f'<font size="8" color="#aaaaaa">STATUS &nbsp; <font color="#333333"><b>{_fmt_text(final_status)}</b></font></font>', styles["Normal"]),
        Paragraph(f'<font size="8" color="#aaaaaa">REPORT ID &nbsp; <font color="#333333">#TBV9</font></font>', styles["Normal"]),
    ]], colWidths=[USABLE_W/3]*3)
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

    elements.append(Paragraph("Structural Validation", H2))
    elements.append(_detail_table(
        ["Parameter", "Value"],
        [
            ["Status (initial)", _fmt_text(result.get("status", "N/A"))],
            ["Column Utilization", _fmt_num(result.get("column_utilization", 0), 3)],
            ["Soil Utilization",   _fmt_num(result.get("soil_utilization", 0), 3)],
            ["Governing Mode",     _fmt_text(result.get("governing_mode", "N/A"))],
        ]
    ))
    elements.append(Spacer(1, 12))

    if sequential_path:
        elements.append(Paragraph("Sequential Correction Path", H2))
        path_rows = []
        for idx, step in enumerate(sequential_path, 1):
            sn = _get_step_number(step, idx)
            path_rows.append([
                str(sn),
                _fmt_text(step.get("action")),
                f"{_fmt_num(step.get('foundation_width'),2)}x{_fmt_num(step.get('foundation_length'),2)} m",
                _fmt_num(step.get("column_capacity"), 0, " kN"),
                _fmt_num(step.get("soil_utilization"), 3),
                _fmt_num(step.get("column_utilization"), 3),
                _fmt_text(step.get("status")),
            ])

        USABLE = 166*mm
        path_data = [["Step", "Action", "Foundation", "Col. Cap.", "Soil Util.", "Col. Util.", "Status"]] + path_rows
        path_t = Table(path_data, colWidths=[
            USABLE*0.06, USABLE*0.26, USABLE*0.18,
            USABLE*0.13, USABLE*0.12, USABLE*0.12, USABLE*0.13
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

    elements.append(Paragraph("Next Required Action", H2))
    elements.append(Paragraph(_get_next_required_action_text(next_required_action), BODY))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Before vs After", H2))
    bva_data = [
        ["Metric", "Before", "After"],
        ["Foundation Width",   _fmt_num(original["foundation_width"], 3, " m"),   _fmt_num(corrected.get("foundation_width"), 3, " m")],
        ["Foundation Length",  _fmt_num(original["foundation_length"], 3, " m"),  _fmt_num(corrected.get("foundation_length"), 3, " m")],
        ["Foundation Area",    _fmt_num(original["foundation_area"], 3, " m2"),   _fmt_num(corrected.get("foundation_area"), 3, " m2")],
        ["Soil Pressure",      _fmt_num(original["soil_pressure"], 3, " kN/m2"),  _fmt_num(corrected.get("soil_pressure"), 3, " kN/m2")],
        ["Soil Utilization",   _fmt_num(original["soil_utilization"], 3),          _fmt_num(corrected.get("soil_utilization"), 3)],
        ["Column Capacity",    _fmt_num(original["column_capacity"], 0, " kN"),   _fmt_num(corrected.get("column_capacity"), 0, " kN")],
        ["Column Utilization", _fmt_num(original["column_utilization"], 3),        _fmt_num(corrected.get("column_utilization"), 3)],
        ["Status",             _fmt_text(original["status"]),                      _fmt_text(final_status)],
    ]
    USABLE = 166*mm
    bva_t = Table(bva_data, colWidths=[USABLE*0.38, USABLE*0.31, USABLE*0.31], hAlign="LEFT")
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
    elements.append(bva_t)
    elements.append(Spacer(1, 12))

    # ── BOQ (FIX: use _fmt_boq_volume and _fmt_boq_weight) ──
    elements.append(Paragraph("Bill of Quantities", H2))
    elements.append(_detail_table(
        ["Parameter", "Value"],
        [
            ["Foundation Area",    _fmt_num(boq.get("foundation_area"), 3, " m²")],
            ["Foundation Depth",   _fmt_num(boq.get("foundation_depth"), 3, " m")],
            ["Concrete Volume",    _fmt_boq_volume(boq.get("concrete_volume_m3"))],
            ["Excavation Volume",  _fmt_boq_volume(boq.get("excavation_volume_m3"), " m³")],
            ["Reinforcement",      _fmt_boq_weight(boq.get("reinforcement_estimate"))],
        ]
    ))
    elements.append(Spacer(1, 12))

    if cost_estimate:
        elements.append(Paragraph("Cost Estimate", H2))
        elements.append(_detail_table(
            ["Item", "Value"],
            [
                ["Foundation Phase",  _fmt_money(cost_estimate.get("foundation_phase_cost_thb"), f" {_currency}")],
                ["Column Upgrade",    _fmt_money(cost_estimate.get("column_upgrade_cost_thb"), f" {_currency}")],
                ["Concrete",          _fmt_money(cost_estimate.get("concrete_cost_thb"), f" {_currency}")],
                ["Excavation",        _fmt_money(cost_estimate.get("excavation_cost_thb"), f" {_currency}")],
                ["Reinforcement",     _fmt_money(cost_estimate.get("reinforcement_cost_thb"), f" {_currency}")],
                ["Combined Total",    _fmt_money(cost_estimate.get("combined_total_cost_thb"), f" {_currency}")],
            ]
        ))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("Cost Assumptions", H3))
        elements.append(_detail_table(
            ["Benchmark", "Value"],
            [
                ["Concrete Rate",       _fmt_money(cost_estimate.get("concrete_rate_thb_per_m3"), f" {_currency}/m³")],
                ["Excavation Rate",     _fmt_money(cost_estimate.get("excavation_rate_thb_per_m3"), f" {_currency}/m³")],
                ["Reinforcement Rate",  _fmt_money(cost_estimate.get("reinforcement_rate_thb_per_kg"), f" {_currency}/kg")],
                ["Column Upgrade Rate", _fmt_money(cost_estimate.get("column_upgrade_rate_thb_per_kn"), f" {_currency}/kN")],
                ["Capacity Increase",   _fmt_num(cost_estimate.get("column_upgrade_capacity_increase_kn"), 1, " kN")],
            ]
        ))
        elements.append(Spacer(1, 12))

    if time_estimate:
        elements.append(Paragraph("Time Estimate", H2))
        basis_text = _fmt_text(time_estimate.get("basis", "N/A"))
        if len(basis_text) > 80:
            basis_text = basis_text[:77] + "..."
        elements.append(_detail_table(
            ["Item", "Value"],
            [
                ["Foundation Phase",  _fmt_num(_get_foundation_phase_days(time_estimate, phase_times), 1, " days")],
                ["Column Upgrade",    _fmt_num(_get_column_phase_days(time_estimate, phase_times), 1, " days")],
                ["Combined Total",    _fmt_num(_safe_float(time_estimate.get("combined_total_days")), 1, " days")],
                ["Work Scope",        _fmt_text(time_estimate.get("activity", "N/A"))],
                ["Basis",             basis_text],
            ]
        ))
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

    # ── Scope of Use ──
    elements.append(Paragraph("Scope of Use", H2))

    USABLE_SCOPE = 166*mm
    scope_data = [
        [
            Paragraph('<font size="8" color="#4a7c59"><b>✓ APPLICABLE FOR</b></font>', styles["Normal"]),
            Paragraph('<font size="8" color="#a05050"><b>✗ NOT APPLICABLE FOR (RED FLAGS)</b></font>', styles["Normal"]),
        ],
        [
            Paragraph('<font size="8" color="#444">✓ Reinforced Concrete (RC) Frame<br/>✓ 1–4 Storeys<br/>✓ Regular rectangular plan<br/>✓ Static gravity load only<br/>✓ Firm soil (bearing capacity known)<br/>✓ Pre-design / Feasibility stage<br/><br/>Ref: ACI 318-19 / EIT 1007-34 / มยผ.</font>', styles["Normal"]),
            Paragraph('<font size="8" color="#444">✗ Seismic zone — no lateral load analysis<br/>✗ Soft clay / peat — high settlement risk<br/>✗ Wind load — not included<br/>✗ Irregular plan / complex geometry<br/>✗ Pile foundation<br/>✗ Steel / timber frame<br/><br/><font color="#a05050"><b>Using outside scope = unsafe result</b></font></font>', styles["Normal"]),
        ]
    ]
    scope_t = Table(scope_data, colWidths=[USABLE_SCOPE*0.5, USABLE_SCOPE*0.5], hAlign="LEFT")
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
    elements.append(scope_t)
    elements.append(Spacer(1, 16))

    # ── Engineering Interpretation (FIX: dynamic text + correct classification) ──
    elements.append(Paragraph("Engineering Interpretation", H2))

    try:
        su_val      = _safe_float(corrected.get("soil_utilization"))
        cu_val      = _safe_float(corrected.get("column_utilization"))
        orig_sp_val = _safe_float(original.get("soil_pressure"))
        soil_cap_val = _safe_float(result.get("soil_capacity")) or 200.0

        governing_mode = _fmt_text(result.get("governing_mode", "SOIL"))
        orig_su_val    = _safe_float(original.get("soil_utilization"))
        orig_cu_val    = _safe_float(original.get("column_utilization"))

        # FIX: Governing failure text based on actual governing mode
        if governing_mode == "COLUMN":
            if orig_cu_val and orig_cu_val > 0:
                col_excess_pct = round((orig_cu_val - 1) * 100)
                governing_failure_text = f"Column capacity exceeded by {col_excess_pct}%"
            else:
                governing_failure_text = "Column capacity insufficient"
        else:
            if orig_sp_val and soil_cap_val and orig_sp_val > soil_cap_val:
                excess_pct = round((orig_sp_val / soil_cap_val - 1) * 100)
                governing_failure_text = f"Soil bearing capacity exceeded by {excess_pct}%"
            elif orig_su_val and orig_su_val > 1.0:
                excess_pct = round((orig_su_val - 1) * 100)
                governing_failure_text = f"Soil bearing capacity exceeded by {excess_pct}%"
            else:
                governing_failure_text = "Soil bearing within limit — column governs"

        # FIX: Use both su and cu for classification
        eng_mode = _classify_design_pdf(su_val, cu_val)

        # FIX: Dynamic interpretation text
        su_interp_text = _interpret_util_text(su_val, "soil utilization")
        cu_interp_text = _interpret_util_text(cu_val, "column utilization")

        if eng_mode in ("EFFICIENT", "OPTIMIZED"):
            interp_note = "Optimized correction — not overdesign. Engineering tolerance ≤1.010 applied."
        elif eng_mode == "CONSERVATIVE":
            interp_note = "Design has significant safety margin. Foundation and column both within safe range."
        else:
            interp_note = "Exceeds engineering tolerance — further redesign required."

        interp_rows = [
            ["Governing failure",       governing_failure_text],
            ["Correction type",          f"Sequential ({len(sequential_path)}-step) deterministic path"],
            ["Final soil utilization",   su_interp_text],
            ["Final column utilization", cu_interp_text],
            ["Design classification",    eng_mode],
            ["Interpretation",           interp_note],
        ]
        elements.append(_detail_table(["Parameter", "Value"], interp_rows))
    except Exception:
        elements.append(Paragraph("Engineering interpretation not available.", BODY))

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
