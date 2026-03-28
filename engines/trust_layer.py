print("TRUST_LAYER_V9_9_5_REQUIRED_VALUES_ACTUAL_FIX_LOADED")
# ============================================
# TRIPLE BOT V9.9.5
# engines/trust_layer.py
# FIX:
# - Make C · Required Values use ACTUAL current validation values
#   for Soil Utilization / Column Utilization / Reserve Margin
# - Keep required area / size / required column capacity logic
# - Keep reference matching logic stable
# - Keep action block logic stable
# - No core structural calculation rewrite
# ============================================

from typing import Dict, Any, Tuple

from test_cases import TEST_CASES

PASS_LIMIT = 1.010
EXACT_MATCH_THRESHOLD = 0.995
EXACT_INPUT_TOLERANCE = 0.01  # 1% relative tolerance on critical inputs


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_status(raw_status: Any) -> str:
    text = str(raw_status).strip().upper()

    if text.startswith("PASS"):
        return "PASS"

    if text in ("SAFE", "WARNING"):
        return "PASS"

    if text == "FAIL":
        return "FAIL"

    return text


def _extract_features(input_data: Dict[str, Any]) -> Dict[str, float]:
    foundation_width = _safe_float(input_data.get("foundation_width"))
    foundation_length = _safe_float(input_data.get("foundation_length"))

    return {
        "building_width": _safe_float(input_data.get("building_width")),
        "building_length": _safe_float(input_data.get("building_length")),
        "num_floors": _safe_float(input_data.get("num_floors")),
        "soil_capacity": _safe_float(input_data.get("soil_capacity")),
        "foundation_width": foundation_width,
        "foundation_length": foundation_length,
        "foundation_area": foundation_width * foundation_length,
        "column_capacity": _safe_float(input_data.get("column_capacity")),
        "engineering_load_per_storey": _safe_float(input_data.get("engineering_load_per_storey")),
        "total_load": _safe_float(input_data.get("total_load")),
    }


def _relative_diff(a: float, b: float) -> float:
    denom = max(abs(a), abs(b), 1.0)
    return abs(a - b) / denom


def _case_distance(runtime_inputs: Dict[str, float], case_inputs: Dict[str, float]) -> float:
    weights = {
        "num_floors": 0.25,
        "total_load": 0.25,
        "soil_capacity": 0.15,
        "foundation_area": 0.20,
        "column_capacity": 0.15,
    }

    distance = 0.0
    for key, weight in weights.items():
        distance += weight * _relative_diff(
            runtime_inputs.get(key, 0.0),
            case_inputs.get(key, 0.0),
        )
    return distance


def match_test_case(input_data: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
    runtime_inputs = _extract_features(input_data)

    best_case = None
    best_distance = 999.0

    for case in TEST_CASES:
        case_inputs = _extract_features(case["inputs"])
        distance = _case_distance(runtime_inputs, case_inputs)
        if distance < best_distance:
            best_distance = distance
            best_case = case

    similarity_score = max(0.0, 1.0 - best_distance)
    similarity_score = round(similarity_score, 3)

    return best_case, similarity_score


def _is_exact_reference_match(
    runtime_inputs: Dict[str, float],
    matched_case: Dict[str, Any],
    similarity_score: float,
) -> bool:
    if matched_case is None:
        return False

    if similarity_score < EXACT_MATCH_THRESHOLD:
        return False

    case_inputs = _extract_features(matched_case.get("inputs", {}))

    critical_keys = [
        "num_floors",
        "total_load",
        "soil_capacity",
        "foundation_area",
        "column_capacity",
    ]

    for key in critical_keys:
        runtime_value = runtime_inputs.get(key, 0.0)
        case_value = case_inputs.get(key, 0.0)
        if _relative_diff(runtime_value, case_value) > EXACT_INPUT_TOLERANCE:
            return False

    return True


def _build_test_validation(
    runtime_inputs: Dict[str, float],
    validation: Dict[str, Any],
    matched_case: Dict[str, Any],
    similarity_score: float,
) -> Dict[str, Any]:
    actual_status = _normalize_status(validation.get("status"))
    actual_mode = str(validation.get("governing_mode", "N/A")).upper()

    if matched_case is None:
        return {
            "verdict": "NO_REFERENCE",
            "matched_case_id": "NO_REFERENCE",
            "tag": "NO_REFERENCE",
            "confidence": "LOW",
            "similarity_score": 0.0,
            "comparison_mode": "NO_REFERENCE",
        }

    expected = matched_case.get("expected", {})
    expected_status = str(expected.get("status", "N/A")).upper()
    expected_mode = str(expected.get("governing_mode", "N/A")).upper()

    exact_match = _is_exact_reference_match(
        runtime_inputs=runtime_inputs,
        matched_case=matched_case,
        similarity_score=similarity_score,
    )

    if similarity_score >= 0.99:
        confidence = "HIGH"
    elif similarity_score >= 0.90:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    if not exact_match:
        return {
            "verdict": "REFERENCE_ONLY",
            "matched_case_id": matched_case["case_id"],
            "tag": matched_case["tag"],
            "confidence": confidence,
            "similarity_score": similarity_score,
            "comparison_mode": "SIMILAR_REFERENCE",
            "expected_status": expected_status,
            "expected_governing_mode": expected_mode,
            "actual_status": actual_status,
            "actual_governing_mode": actual_mode,
        }

    status_ok = expected_status == actual_status
    mode_ok = expected_mode == actual_mode
    verdict = "CONSISTENT" if status_ok and mode_ok else "MISMATCH"

    return {
        "verdict": verdict,
        "matched_case_id": matched_case["case_id"],
        "tag": matched_case["tag"],
        "confidence": confidence,
        "similarity_score": similarity_score,
        "comparison_mode": "EXACT_REFERENCE",
        "expected_status": expected_status,
        "expected_governing_mode": expected_mode,
        "actual_status": actual_status,
        "actual_governing_mode": actual_mode,
    }


def _build_expected_actual(
    runtime_inputs: Dict[str, float],
    validation: Dict[str, Any],
    matched_case: Dict[str, Any],
    similarity_score: float,
) -> Dict[str, Any]:
    actual_status = _normalize_status(validation.get("status"))
    actual_mode = str(validation.get("governing_mode", "N/A")).upper()
    actual_soil = round(_safe_float(validation.get("soil_utilization")), 3)
    actual_column = round(_safe_float(validation.get("column_utilization")), 3)

    if matched_case is None:
        return {
            "expected_status": "NO_REFERENCE",
            "actual_status": actual_status,
            "status_check": "NO_REFERENCE",
            "expected_governing_mode": "NO_REFERENCE",
            "actual_governing_mode": actual_mode,
            "mode_check": "NO_REFERENCE",
            "expected_soil_utilization": "NO_REFERENCE",
            "actual_soil_utilization": actual_soil,
            "delta_soil_utilization": "NO_REFERENCE",
            "soil_check": "NO_REFERENCE",
            "expected_column_utilization": "NO_REFERENCE",
            "actual_column_utilization": actual_column,
            "delta_column_utilization": "NO_REFERENCE",
            "column_check": "NO_REFERENCE",
            "comparison_mode": "NO_REFERENCE",
        }

    expected = matched_case.get("expected", {})
    exact_match = _is_exact_reference_match(
        runtime_inputs=runtime_inputs,
        matched_case=matched_case,
        similarity_score=similarity_score,
    )

    expected_status = str(expected.get("status", "N/A")).upper()
    expected_mode = str(expected.get("governing_mode", "N/A")).upper()
    expected_soil = round(_safe_float(expected.get("soil_utilization")), 3)
    expected_column = round(_safe_float(expected.get("column_utilization")), 3)

    delta_soil = round(actual_soil - expected_soil, 3)
    delta_column = round(actual_column - expected_column, 3)

    if not exact_match:
        return {
            "expected_status": f"{expected_status} (REFERENCE)",
            "actual_status": actual_status,
            "status_check": "REFERENCE_ONLY",
            "expected_governing_mode": f"{expected_mode} (REFERENCE)",
            "actual_governing_mode": actual_mode,
            "mode_check": "REFERENCE_ONLY",
            "expected_soil_utilization": expected_soil,
            "actual_soil_utilization": actual_soil,
            "delta_soil_utilization": delta_soil,
            "soil_check": "REFERENCE_ONLY",
            "expected_column_utilization": expected_column,
            "actual_column_utilization": actual_column,
            "delta_column_utilization": delta_column,
            "column_check": "REFERENCE_ONLY",
            "comparison_mode": "SIMILAR_REFERENCE",
        }

    return {
        "expected_status": expected_status,
        "actual_status": actual_status,
        "status_check": "CONSISTENT" if expected_status == actual_status else "MISMATCH",
        "expected_governing_mode": expected_mode,
        "actual_governing_mode": actual_mode,
        "mode_check": "CONSISTENT" if expected_mode == actual_mode else "MISMATCH",
        "expected_soil_utilization": expected_soil,
        "actual_soil_utilization": actual_soil,
        "delta_soil_utilization": delta_soil,
        "soil_check": "CONSISTENT" if expected_soil == actual_soil else "MISMATCH",
        "expected_column_utilization": expected_column,
        "actual_column_utilization": actual_column,
        "delta_column_utilization": delta_column,
        "column_check": "CONSISTENT" if expected_column == actual_column else "MISMATCH",
        "comparison_mode": "EXACT_REFERENCE",
    }


def _build_required_values(
    input_data: Dict[str, Any],
    validation: Dict[str, Any],
) -> Dict[str, Any]:
    soil_util_actual = _safe_float(validation.get("soil_utilization"))
    column_util_actual = _safe_float(validation.get("column_utilization"))
    total_load = _safe_float(input_data.get("total_load"))
    soil_cap = _safe_float(input_data.get("soil_capacity"))
    current_column_cap = _safe_float(input_data.get("column_capacity"))

    required_area = total_load / soil_cap if soil_cap > 0 else 0.0
    recommended_size = required_area ** 0.5 if required_area > 0 else 0.0
    required_column = total_load if column_util_actual > 1.0 else current_column_cap

    reserve_margin = (1 - max(soil_util_actual, column_util_actual)) * 100

    return {
        "required_foundation_area_m2": round(required_area, 3),
        "recommended_size_label": f"{recommended_size:.2f} x {recommended_size:.2f} m",
        "required_column_capacity_kN": round(required_column, 0),
        "soil_utilization": round(soil_util_actual, 3),
        "column_utilization": round(column_util_actual, 3),
        "reserve_margin_pct": round(reserve_margin, 1),
    }


def _build_action_block(
    input_data: Dict[str, Any],
    validation: Dict[str, Any],
) -> Dict[str, Any]:
    status = _normalize_status(validation.get("status"))
    governing_mode = str(validation.get("governing_mode", "N/A")).upper()
    soil_util = _safe_float(validation.get("soil_utilization"))
    column_util = _safe_float(validation.get("column_utilization"))

    required_values = _build_required_values(input_data, validation)
    recommended_size = required_values["recommended_size_label"]
    required_column = required_values["required_column_capacity_kN"]

    actions = []

    if status == "PASS":
        actions.append({
            "action": "NO_ACTION",
            "detail": "No corrective action required",
        })
        return {
            "primary_action": actions[0],
            "all_actions": actions,
        }

    if governing_mode == "SOIL":
        actions.append({
            "action": "FOUNDATION_INCREASE",
            "detail": f"Increase foundation to {recommended_size} to reduce soil pressure",
        })
        if column_util > 1.0:
            actions.append({
                "action": "COLUMN_UPGRADE",
                "detail": f"Upgrade column to minimum {required_column:.0f} kN capacity",
            })

    elif governing_mode == "COLUMN":
        actions.append({
            "action": "COLUMN_UPGRADE",
            "detail": f"Upgrade column to minimum {required_column:.0f} kN capacity",
        })
        if soil_util > 1.0:
            actions.append({
                "action": "FOUNDATION_INCREASE",
                "detail": f"Increase foundation to {recommended_size} to reduce soil pressure",
            })

    else:
        actions.append({
            "action": "ENGINEERING_REVIEW",
            "detail": "Review governing mode and corrective action manually",
        })

    return {
        "primary_action": actions[0],
        "all_actions": actions,
    }


def _build_assumption_trace(input_data: Dict[str, Any]) -> Dict[str, Any]:
    foundation_width = _safe_float(input_data.get("foundation_width"))
    foundation_length = _safe_float(input_data.get("foundation_length"))

    return {
        "storeys": input_data.get("num_floors"),
        "load_per_storey_kN": round(_safe_float(input_data.get("engineering_load_per_storey")), 3),
        "load_factor_kN_m2": 7.5,
        "total_load_kN": round(_safe_float(input_data.get("total_load")), 3),
        "soil_capacity_kN_m2": round(_safe_float(input_data.get("soil_capacity")), 3),
        "foundation_width_m": round(foundation_width, 3),
        "foundation_length_m": round(foundation_length, 3),
        "foundation_area_m2": round(foundation_width * foundation_length, 3),
        "column_capacity_kN": round(_safe_float(input_data.get("column_capacity")), 3),
        "tolerance_rule": f"≤ {PASS_LIMIT:.3f}",
        "load_basis": "DL 4.5 + LL 3.0 = 7.5 kN/m²",
    }


def _build_boundary_warning(
    input_data: Dict[str, Any],
    validation: Dict[str, Any],
) -> Dict[str, Any]:
    soil_util = _safe_float(validation.get("soil_utilization"))
    column_util = _safe_float(validation.get("column_utilization"))
    max_util = max(soil_util, column_util)
    margin_to_limit = round(PASS_LIMIT - max_util, 3)

    if max_util > PASS_LIMIT:
        proximity = "OVER_LIMIT"
    elif max_util >= 0.95:
        proximity = "NEAR_LIMIT"
    elif max_util >= 0.80:
        proximity = "APPROACHING"
    else:
        proximity = "SAFE"

    warnings = []

    plus5 = round(max_util * 1.05, 3)
    warnings.append({
        "scenario": "+5% load",
        "impact": "FAIL" if plus5 > PASS_LIMIT else "PASS",
        "detail": f"Max utilization = {plus5}",
    })

    if soil_util > 0:
        minus10_soil = round(soil_util / 0.90, 3)
        warnings.append({
            "scenario": "-10% soil capacity",
            "impact": "FAIL" if minus10_soil > PASS_LIMIT else "PASS",
            "detail": f"Soil utilization = {minus10_soil}",
        })

    return {
        "proximity": proximity,
        "proximity_detail": f"Margin to limit = {margin_to_limit}",
        "warning_count": len(warnings),
        "warnings": warnings,
        "margin_to_limit": margin_to_limit,
    }


def run_trust_layer(input_data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
    runtime_inputs = _extract_features(input_data)
    matched_case, similarity_score = match_test_case(input_data)

    return {
        "test_validation": _build_test_validation(
            runtime_inputs=runtime_inputs,
            validation=validation,
            matched_case=matched_case,
            similarity_score=similarity_score,
        ),
        "expected_actual": _build_expected_actual(
            runtime_inputs=runtime_inputs,
            validation=validation,
            matched_case=matched_case,
            similarity_score=similarity_score,
        ),
        "required_values": _build_required_values(
            input_data=input_data,
            validation=validation,
        ),
        "action_block": _build_action_block(
            input_data=input_data,
            validation=validation,
        ),
        "assumption_trace": _build_assumption_trace(input_data),
        "boundary_warning": _build_boundary_warning(
            input_data=input_data,
            validation=validation,
        ),
    }