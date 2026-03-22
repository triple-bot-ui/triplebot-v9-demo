# engineering_decision_engine_v8.py
# Triple Bot V8 Decision Engine
# Deterministic engineering recommendation layer


def filter_options_by_governing_mode(options, governing_mode):
    """
    BUG FIX: original code used prioritize (reorder) which still allowed
    secondary options to win if no primary options existed.
    Now uses a hard filter: only return options matching governing mode.
    If no matching options exist, fall back to all options.
    """

    if not options:
        return []

    if governing_mode == "COLUMN":
        primary = [o for o in options if o.get("option_type") == "COLUMN_UPGRADE"]
    elif governing_mode == "SOIL":
        primary = [o for o in options if o.get("option_type") == "FOUNDATION_INCREASE"]
    else:
        primary = []

    # Hard filter: use governing-mode options only
    # Fall back to full list only if no matching options found
    return primary if primary else options


def generate_engineering_decision(options, engineering_results=None):

    if not options:
        return {
            "best_option": None,
            "recommended_action": "NONE",
            "new_foundation_size": None,
            "upgraded_column_capacity": None,
            "load_reduction": None
        }

    governing_mode = None

    if engineering_results:
        governing_mode = engineering_results.get("governing_mode")

    # BUG FIX: filter by governing mode first (hard filter),
    # then pick the first (lowest score / best) from that filtered set.
    # Previously: prioritize was just a reorder, COLUMN could still win
    # when FOUNDATION options had higher scores.
    filtered_options = filter_options_by_governing_mode(options, governing_mode)

    best_option = filtered_options[0]

    decision = {
        "best_option": best_option,
        "recommended_action": best_option.get("option_type"),
        "new_foundation_size": best_option.get("new_foundation_size"),
        "upgraded_column_capacity": best_option.get("upgraded_column_capacity"),
        "load_reduction": best_option.get("load_reduction")
    }

    return decision
