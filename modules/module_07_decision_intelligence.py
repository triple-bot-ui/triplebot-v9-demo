# ============================================
# TRIPLE BOT V9.9.2
# Module 07 — Decision Intelligence + Action Layer
# SAFE MERGE: keep V9.7 UI + add Action Layer only
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


# ============================================
# NEW — ACTION LAYER (CORE ADDITION)
# ============================================

def _build_action_block(validation_package, best_option):

    status         = validation_package["status"]
    governing_mode = validation_package["governing_mode"]
    soil_util      = validation_package["soil_utilization"]
    column_util    = validation_package["column_utilization"]

    if status != "FAIL" or best_option is None:
        return {
            "primary_action": None,
            "all_actions": []
        }

    actions = []

    if governing_mode == "SOIL":
        actions.append({
            "action": "FOUNDATION_INCREASE",
            "detail": "Increase foundation size to required area"
        })

        if column_util > 1.0:
            actions.append({
                "action": "COLUMN_UPGRADE",
                "detail": "Upgrade column capacity to meet load demand"
            })

    elif governing_mode == "COLUMN":
        actions.append({
            "action": "COLUMN_UPGRADE",
            "detail": "Upgrade column capacity to reduce utilization"
        })

        if soil_util > 1.0:
            actions.append({
                "action": "FOUNDATION_INCREASE",
                "detail": "Increase foundation size to reduce soil pressure"
            })

    else:
        actions.append({
            "action": best_option.get("option_type", "N/A"),
            "detail": "Apply selected engineering correction"
        })

    return {
        "primary_action": actions[0] if actions else None,
        "all_actions": actions
    }


# ============================================
# CORE
# ============================================

def run_decision_intelligence(validation_package, decision_options):

    status = validation_package["status"]

    ranked_options = sorted(
        [{**opt, "score": _score_option(opt, validation_package)} for opt in decision_options],
        key=lambda x: x["score"],
        reverse=True
    )

    best_option = ranked_options[0] if status == "FAIL" and ranked_options else None

    reasoning = _build_reasoning(best_option, validation_package, ranked_options)

    if best_option is not None:
        best_option = {**best_option, "reasoning": reasoning}

    # 🔥 ADD HERE
    action_block = _build_action_block(validation_package, best_option)

    return {
        "validation": validation_package,
        "decision":   best_option,
        "options":    ranked_options,
        "reasoning":  reasoning,
        "action_block": action_block
    }


# ============================================
# DISPLAY (UNCHANGED + SHOW ACTION)
# ============================================

def display_decision_results(st, decision_results):

    decision  = decision_results.get("decision")
    options   = decision_results.get("options", [])
    reasoning = decision_results.get("reasoning", {})
    action_block = decision_results.get("action_block", {})

    if decision is None:
        st.success("No engineering action required.")
        return

    option_type = decision.get("option_type", "—")
    desc        = decision.get("description", "")
    confidence  = reasoning.get("confidence_in_selected_action", "—")

    st.write("### Engineering Decision")
    st.write(f"**Action:** {option_type}")
    st.write(f"**Reason:** {reasoning.get('primary_reason','—')}")
    st.write(f"**Logic:** {reasoning.get('governing_explanation','—')}")
    st.write(f"**Confidence:** {confidence}")

    # 🔥 NEW UI — Action Steps
    if action_block and action_block.get("all_actions"):
        st.write("### Action Steps")
        for i, act in enumerate(action_block["all_actions"], 1):
            st.write(f"Step {i}: {act.get('action')} → {act.get('detail')}")


# ============================================
# OUTPUT PACKAGE
# ============================================

def extract_decision_for_output(decision_results):
    return {
        "validation": decision_results["validation"],
        "decision":   decision_results["decision"],
        "options":    decision_results["options"],
        "reasoning":  decision_results.get("reasoning", {}),
        "action_block": decision_results.get("action_block")
    }