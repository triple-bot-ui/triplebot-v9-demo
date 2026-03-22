# ============================================
# TRIPLE BOT V9.7
# Module 07 — Decision Intelligence
# UI: Compact decision layer, detail in expander
# FIX: WARNING = advisory only, not trigger
#      Only FAIL triggers decision engine
# ============================================

def _score_option(option, validation_package):
    governing_mode = validation_package["governing_mode"]
    soil_util      = validation_package["soil_utilization"]
    column_util    = validation_package["column_utilization"]
    option_type    = option.get("option_type")

    if governing_mode == "SOIL":
        if option_type == "FOUNDATION_INCREASE": return soil_util * 100
        if option_type == "LOAD_REDUCTION":      return soil_util * 80
        if option_type == "SOIL_IMPROVEMENT":    return soil_util * 90
        if option_type == "COLUMN_UPGRADE":      return column_util * 20

    if governing_mode == "COLUMN":
        if option_type == "COLUMN_UPGRADE":      return column_util * 100
        if option_type == "LOAD_REDUCTION":      return column_util * 80
        if option_type == "FOUNDATION_INCREASE": return soil_util * 20
        if option_type == "SOIL_IMPROVEMENT":    return soil_util * 10

    return 0


def _build_reasoning(best_option, validation_package, ranked_options):
    if best_option is None:
        return {
            "primary_reason": "No engineering action required.",
            "governing_explanation": "Validation status is SAFE or WARNING — within acceptable limits.",
            "selection_explanation": "No corrective branch needed.",
            "rejected_explanation": "No competing engineering option required.",
            "confidence_in_selected_action": "HIGH"
        }

    governing_mode = validation_package["governing_mode"]
    soil_util      = validation_package["soil_utilization"]
    column_util    = validation_package["column_utilization"]
    option_type    = best_option.get("option_type", "N/A")

    if governing_mode == "SOIL":
        governing_explanation = f"SOIL governs — soil util ({soil_util:.3f}) > column util ({column_util:.3f})."
    elif governing_mode == "COLUMN":
        governing_explanation = f"COLUMN governs — column util ({column_util:.3f}) > soil util ({soil_util:.3f})."
    else:
        governing_explanation = f"Governing mode: {governing_mode}."

    if option_type == "FOUNDATION_INCREASE":
        primary_reason        = "Foundation increase — governing failure is soil-controlled."
        selection_explanation = "Reduces soil pressure by increasing foundation area."
    elif option_type == "COLUMN_UPGRADE":
        primary_reason        = "Column upgrade — governing failure is column-controlled."
        selection_explanation = "Reduces column utilization by increasing column capacity."
    elif option_type == "LOAD_REDUCTION":
        primary_reason        = "Load reduction — direct structural upgrade not prioritized."
        selection_explanation = "Reduces total structural demand across the system."
    else:
        primary_reason        = f"{option_type} selected by deterministic ranking."
        selection_explanation = "Highest deterministic score."

    rejected = [
        f"{o.get('option_type')} ({o.get('score',0):.0f})"
        for o in ranked_options if o.get("option_type") != option_type
    ]
    rejected_explanation = "Others ranked lower: " + ", ".join(rejected) + "." if rejected else "No alternatives."

    top_score    = best_option.get("score", 0)
    second_score = ranked_options[1].get("score", 0) if len(ranked_options) > 1 else 0
    gap          = top_score - second_score
    confidence   = "HIGH" if gap >= 50 else ("MEDIUM" if gap >= 10 else "LOW")

    return {
        "primary_reason":                primary_reason,
        "governing_explanation":         governing_explanation,
        "selection_explanation":         selection_explanation,
        "rejected_explanation":          rejected_explanation,
        "confidence_in_selected_action": confidence
    }


def run_decision_intelligence(validation_package, decision_options):
    status = validation_package["status"]

    ranked_options = sorted(
        [{**opt, "score": _score_option(opt, validation_package)} for opt in decision_options],
        key=lambda x: x["score"],
        reverse=True
    )

    # FIX: Only FAIL triggers decision engine
    # WARNING = advisory only (util 0.8-1.0), no corrective action needed
    # SAFE = no action needed
    best_option = ranked_options[0] if status == "FAIL" and ranked_options else None
    reasoning   = _build_reasoning(best_option, validation_package, ranked_options)

    if best_option is not None:
        best_option = {**best_option, "reasoning": reasoning}

    return {
        "validation": validation_package,
        "decision":   best_option,
        "options":    ranked_options,
        "reasoning":  reasoning
    }


# ============================================
# DISPLAY — compact decision layer
# ============================================

def display_decision_results(st, decision_results):

    decision  = decision_results.get("decision")
    options   = decision_results.get("options", [])
    reasoning = decision_results.get("reasoning", {})

    if decision is None:
        st.success("No engineering action required.")
        return

    option_type = decision.get("option_type", "—")
    desc        = decision.get("description", "")
    confidence  = reasoning.get("confidence_in_selected_action", "—")

    st.markdown("""
    <style>
    .dc-wrap {
        border: 1px solid #e0e0de;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 16px;
        font-family: 'DM Mono', monospace;
        background: #fff;
    }
    .dc-header {
        background: #2a2a2a;
        color: #fff;
        padding: 10px 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .dc-header-label { font-size: 13px; font-weight: 700; letter-spacing: .04em; }
    .dc-header-conf  { font-size: 10px; color: #aaa; letter-spacing: .1em; }
    .dc-body { padding: 14px 18px; }
    .dc-action { font-size: 15px; font-weight: 700; color: #111; margin-bottom: 6px; }
    .dc-desc   { font-size: 11px; color: #888; margin-bottom: 10px; }
    .dc-row    { font-size: 11px; color: #666; margin-bottom: 4px; line-height: 1.5; }
    .dc-row b  { color: #333; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="dc-wrap">
      <div class="dc-header">
        <span class="dc-header-label">Engineering Decision</span>
        <span class="dc-header-conf">CONFIDENCE · {confidence}</span>
      </div>
      <div class="dc-body">
        <div class="dc-action">{option_type}</div>
        <div class="dc-desc">{desc}</div>
        <div class="dc-row"><b>Why:</b> {reasoning.get('primary_reason','—')}</div>
        <div class="dc-row"><b>Logic:</b> {reasoning.get('governing_explanation','—')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("▸ Decision Detail", expanded=False):
        st.caption("Reasoning")
        st.markdown(f"""
        <table style="font-size:11px;width:100%;font-family:'DM Mono',monospace">
          <tr><td style="color:#aaa;padding:4px 8px">Why Selected</td><td style="padding:4px 8px">{reasoning.get('selection_explanation','—')}</td></tr>
          <tr><td style="color:#aaa;padding:4px 8px">Why Not Others</td><td style="padding:4px 8px">{reasoning.get('rejected_explanation','—')}</td></tr>
          <tr><td style="color:#aaa;padding:4px 8px">Confidence</td><td style="padding:4px 8px">{confidence}</td></tr>
        </table>
        """, unsafe_allow_html=True)

        st.caption("Options Ranking")
        import pandas as pd
        rows = [
            {"rank": i+1, "option": o.get("option_type"), "score": round(o.get("score",0),0), "description": o.get("description","")}
            for i, o in enumerate(options)
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ============================================
# OUTPUT PACKAGE
# ============================================

def extract_decision_for_output(decision_results):
    return {
        "validation": decision_results["validation"],
        "decision":   decision_results["decision"],
        "options":    decision_results["options"],
        "reasoning":  decision_results.get("reasoning", {})
    }
