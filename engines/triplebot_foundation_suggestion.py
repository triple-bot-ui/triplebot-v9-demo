# ============================================
# TRIPLE BOT V5
# Foundation Resize Suggestion Engine
# ============================================

import math


def suggest_foundation_resize(prebim_result):

    required_area = prebim_result["required_area"]

    suggested_side = math.sqrt(required_area)

    # BUG FIX: round(x + 0.05, 2) does NOT reliably round up.
    # e.g. sqrt(2.4) = 1.5492... → +0.05 = 1.5992 → round = 1.60
    # but sqrt(1.0) = 1.0 → +0.05 = 1.05 → round = 1.05 (not a clean size)
    # Use math.ceil to 2 decimal places for a proper engineering ceiling.
    suggested_side = math.ceil(suggested_side * 100) / 100

    suggested_area = round(suggested_side * suggested_side, 3)

    return {
        "required_area": required_area,
        "suggested_foundation_width": suggested_side,
        "suggested_foundation_length": suggested_side,
        "suggested_foundation_area": suggested_area
    }
