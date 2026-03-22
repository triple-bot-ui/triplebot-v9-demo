# ============================================
# TRIPLE BOT – LOAD COMBINATION ENGINE
# V6 Engineering Expansion Layer
# ============================================

# BUG FIX: engineering_constants.py does not exist in the project.
# LOAD_FACTOR is now defined inline to prevent ImportError crash.
LOAD_FACTOR = 1.4


def generate_load_cases(load_per_storey, number_of_storeys):

    # ----------------------------------------
    # BASE LOAD
    # ----------------------------------------

    total_load = load_per_storey * number_of_storeys

    # ----------------------------------------
    # LOAD CASES
    # ----------------------------------------

    load_cases = {}

    # LC1 — Dead Load
    load_cases["LC1_DEAD"] = total_load

    # LC2 — Dead + Live (assume live load = storey load)
    load_cases["LC2_DEAD_LIVE"] = total_load * 1.0

    # LC3 — Dead + Live × Safety Factor
    load_cases["LC3_FACTORED"] = total_load * LOAD_FACTOR

    # ----------------------------------------
    # FIND WORST CASE
    # ----------------------------------------

    governing_case = max(load_cases, key=load_cases.get)

    worst_case_load = load_cases[governing_case]

    # ----------------------------------------
    # RESULT
    # ----------------------------------------

    result = {
        "load_cases": load_cases,
        "governing_case": governing_case,
        "worst_case_load": worst_case_load
    }

    return result
